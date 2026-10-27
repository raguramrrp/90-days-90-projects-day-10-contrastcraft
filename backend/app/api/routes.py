"""
ContrastCraft — FastAPI API Routes
Modular, validated REST endpoints for accessibility auditing, recommendations,
patch generation, safe patch application, reports, and session management.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from ..core.analyzer import AuditEngine
from ..core.recommender import generate_color_recommendations, PRESET_PALETTES
from ..core.patcher import generate_css_patch, apply_patch_safely, revert_patch_safely
from ..core.reporter import generate_json_report, generate_html_report, generate_csv_report, export_corrected_css
from ..core.html_a11y import HTMLA11yAuditor
from ..core.token_matrix import TokenIntelligenceEngine
from ..database.session_store import SessionStore

router = APIRouter(prefix="/api")
session_store = SessionStore()


# --- Pydantic Request Models ---

class AuditRequest(BaseModel):
    html: str = Field(..., max_length=5_000_000, description="HTML source content to audit")
    css: Optional[str] = Field(default="", max_length=5_000_000, description="Optional CSS source")
    session_name: Optional[str] = Field(default="ContrastCraft Audit", max_length=150)


class FolderAuditRequest(BaseModel):
    folder_path: str = Field(..., max_length=1000, description="Local folder path to scan")
    exclusions: Optional[List[str]] = Field(
        default=["node_modules", ".git", "dist", "build", ".venv", "__pycache__", ".idea", ".vscode"]
    )
    max_files: Optional[int] = Field(default=50, ge=1, le=200)


class RecommendRequest(BaseModel):
    foreground: str = Field(..., max_length=100)
    background: str = Field(..., max_length=100)
    target_threshold: Optional[float] = Field(default=4.5, ge=1.0, le=21.0)


class PatchGenerateRequest(BaseModel):
    css: str = Field(..., max_length=5_000_000)
    selector: str = Field(..., max_length=200)
    property_name: str = Field(default="color", max_length=100)
    new_value: str = Field(..., max_length=100)
    file_name: Optional[str] = Field(default="styles.css", max_length=150)


class PatchApplyRequest(BaseModel):
    file_path: str = Field(..., max_length=1000)
    patched_content: str = Field(..., max_length=5_000_000)
    explicit_approval: bool = Field(default=False)


class PatchRevertRequest(BaseModel):
    file_path: str = Field(..., max_length=1000)


class TokenImpactRequest(BaseModel):
    token_name: str = Field(..., max_length=100)
    proposed_value: str = Field(..., max_length=100)
    findings: List[Dict[str, Any]]
    tokens: List[Dict[str, Any]]


class HTMLA11yRequest(BaseModel):
    html: str = Field(..., max_length=5_000_000)
    css: Optional[str] = Field(default="", max_length=5_000_000)


class SessionSaveRequest(BaseModel):
    name: str = Field(..., max_length=150)
    input_type: str = Field(default="paste", max_length=50)
    html_content: str = Field(default="")
    css_content: str = Field(default="")
    summary: Dict[str, Any]
    findings: List[Dict[str, Any]]
    tokens: List[Dict[str, Any]]
    session_id: Optional[str] = None


class SessionRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)


# --- Endpoints ---

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "tool": "ContrastCraft",
        "version": "1.0.0",
        "engine": "WCAG 2.1 / 2.2 Relative Luminance Engine"
    }


@router.get("/presets")
def get_presets():
    return {"presets": PRESET_PALETTES}


@router.post("/audit")
def run_audit(req: AuditRequest):
    if not req.html.strip():
        raise HTTPException(status_code=400, detail="HTML content cannot be empty.")

    engine = AuditEngine()
    result = engine.analyze(html_content=req.html, custom_css=req.css or "")
    result["session_name"] = req.session_name
    return result


@router.post("/audit-folder")
def run_folder_audit(req: FolderAuditRequest):
    target_dir = Path(req.folder_path).resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"Directory does not exist or is not a folder: {req.folder_path}")

    # Security check: ensure path is valid and within safe drive
    exclusions = set(req.exclusions or [])
    html_files: List[Path] = []
    css_files: List[Path] = []

    for root, dirs, files in os.walk(str(target_dir)):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in exclusions and not d.startswith(".")]

        for f in files:
            p = Path(root) / f
            # Check symlinks pointing outside
            try:
                resolved_p = p.resolve()
                if not str(resolved_p).startswith(str(target_dir)):
                    continue
            except Exception:
                continue

            if p.suffix.lower() in (".html", ".htm"):
                html_files.append(p)
            elif p.suffix.lower() == ".css":
                css_files.append(p)

            if len(html_files) + len(css_files) >= (req.max_files or 50):
                break
        if len(html_files) + len(css_files) >= (req.max_files or 50):
            break

    if not html_files:
        raise HTTPException(status_code=404, detail="No HTML files discovered in the selected directory.")

    # Aggregate primary HTML and external CSS
    primary_html = html_files[0].read_text(encoding="utf-8", errors="replace")
    external_css_map: Dict[str, str] = {}
    combined_css = []

    for c_path in css_files:
        try:
            c_text = c_path.read_text(encoding="utf-8", errors="replace")
            external_css_map[c_path.name] = c_text
            combined_css.append(f"/* {c_path.name} */\n" + c_text)
        except Exception:
            continue

    engine = AuditEngine()
    result = engine.analyze(
        html_content=primary_html,
        custom_css="\n\n".join(combined_css),
        external_stylesheets=external_css_map
    )

    result["scanned_folder"] = str(target_dir)
    result["scanned_html_files"] = [str(p.relative_to(target_dir)) for p in html_files]
    result["scanned_css_files"] = [str(p.relative_to(target_dir)) for p in css_files]
    result["session_name"] = f"Folder Audit: {target_dir.name}"

    return result


@router.post("/recommend")
def get_recommendations(req: RecommendRequest):
    return generate_color_recommendations(
        fg_str=req.foreground,
        bg_str=req.background,
        target_threshold=req.target_threshold or 4.5
    )


@router.post("/patch/generate")
def create_patch(req: PatchGenerateRequest):
    proposal = generate_css_patch(
        css_content=req.css,
        selector=req.selector,
        property_name=req.property_name,
        new_value=req.new_value,
        file_name=req.file_name or "styles.css"
    )
    return {
        "selector": proposal.target_selector,
        "property": proposal.target_property,
        "original_value": proposal.original_value,
        "proposed_value": proposal.proposed_value,
        "diff": proposal.diff_text,
        "affected_file": proposal.affected_file,
        "patched_css": proposal.patched_snippet
    }


@router.post("/patch/apply")
def apply_patch(req: PatchApplyRequest):
    p = Path(req.file_path).resolve()
    result = apply_patch_safely(
        file_path=p,
        patched_content=req.patched_content,
        explicit_approval=req.explicit_approval
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to apply patch."))
    return result


@router.post("/patch/revert")
def revert_patch(req: PatchRevertRequest):
    p = Path(req.file_path).resolve()
    result = revert_patch_safely(file_path=p)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to revert patch."))
    return result


@router.post("/tokens/impact")
def evaluate_token_impact(req: TokenImpactRequest):
    engine = TokenIntelligenceEngine()
    return engine.evaluate_token_impact(
        token_name=req.token_name,
        proposed_value=req.proposed_value,
        findings=req.findings,
        tokens=req.tokens
    )


@router.post("/audit-html-a11y")
def audit_html_a11y(req: HTMLA11yRequest):
    auditor = HTMLA11yAuditor()
    findings = auditor.audit(req.html, custom_css=req.css or "")
    from dataclasses import asdict
    return {"findings": [asdict(f) for f in findings], "total": len(findings)}


@router.post("/reports/json")
def download_json_report(data: Dict[str, Any]):
    name = data.get("session_name", "ContrastCraft-Audit")
    json_str = generate_json_report(data, session_name=name)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="contrastcraft-report.json"'}
    )


@router.post("/reports/html")
def download_html_report(data: Dict[str, Any]):
    name = data.get("session_name", "ContrastCraft-Audit")
    html_str = generate_html_report(data, session_name=name)
    return Response(
        content=html_str,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="contrastcraft-report.html"'}
    )


@router.post("/reports/csv")
def download_csv_report(data: Dict[str, Any]):
    csv_str = generate_csv_report(data)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="contrastcraft-findings.csv"'}
    )


@router.post("/export/css")
def download_corrected_css(data: Dict[str, Any]):
    findings = data.get("findings", [])
    original_css = data.get("original_css", "")
    css_str = export_corrected_css(findings, original_css=original_css)
    return Response(
        content=css_str,
        media_type="text/css",
        headers={"Content-Disposition": f'attachment; filename="contrastcraft-corrected.css"'}
    )


# --- Session Management Endpoints ---

@router.get("/sessions")
def list_sessions():
    return {"sessions": session_store.list_sessions()}


@router.post("/sessions")
def save_session(req: SessionSaveRequest):
    s_id = session_store.save_session(
        name=req.name,
        input_type=req.input_type,
        html_content=req.html_content,
        css_content=req.css_content,
        summary=req.summary,
        findings=req.findings,
        tokens=req.tokens,
        session_id=req.session_id
    )
    return {"success": True, "session_id": s_id}


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    s = session_store.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")
    return s


@router.patch("/sessions/{session_id}")
def rename_session(session_id: str, req: SessionRenameRequest):
    ok = session_store.rename_session(session_id, req.name)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True, "name": req.name}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    ok = session_store.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True}


@router.get("/sessions/compare/{session_id_a}/{session_id_b}")
def compare_sessions(session_id_a: str, session_id_b: str):
    comparison = session_store.compare_sessions(session_id_a, session_id_b)
    if not comparison:
        raise HTTPException(status_code=404, detail="One or both sessions not found.")
    return comparison
