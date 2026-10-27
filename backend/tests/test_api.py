"""
Integration tests for FastAPI REST Endpoints
"""

import pytest
from backend.app.api.routes import (
    health_check,
    get_presets,
    run_audit,
    get_recommendations,
    create_patch,
    save_session,
    get_session,
    rename_session,
    delete_session,
    AuditRequest,
    RecommendRequest,
    PatchGenerateRequest,
    SessionSaveRequest,
    SessionRenameRequest
)


def test_api_health_direct():
    data = health_check()
    assert data["status"] == "healthy"
    assert data["tool"] == "ContrastCraft"


def test_api_presets_direct():
    data = get_presets()
    assert "presets" in data
    assert "neutral_accessible" in data["presets"]


def test_api_audit_paste_valid_direct():
    html_sample = """
    <div style="background-color: #FFFFFF;">
        <h1 style="color: #0F172A; font-size: 32px;">Welcome</h1>
        <p style="color: #9CA3AF;">Failing light gray text</p>
        <button style="color: #FFFFFF; background-color: #2563EB; border: 1px solid #1D4ED8;">Action</button>
    </div>
    """
    req = AuditRequest(html=html_sample, session_name="API Test")
    data = run_audit(req)

    assert "summary" in data
    assert "findings" in data
    assert data["summary"]["total_analyzed"] >= 2
    assert data["summary"]["fail_aa_count"] >= 1


def test_api_recommend_direct():
    req = RecommendRequest(
        foreground="#9CA3AF",
        background="#FFFFFF",
        target_threshold=4.5
    )
    data = get_recommendations(req)
    assert data["success"] is True
    assert len(data["suggestions"]) >= 2
    assert data["suggestions"][0]["ratio"] >= 4.5


def test_api_patch_lifecycle_direct():
    original_css = ".text { color: #9CA3AF; }"
    req = PatchGenerateRequest(
        css=original_css,
        selector=".text",
        property_name="color",
        new_value="#4B5563"
    )
    gen_data = create_patch(req)
    assert "color: #4B5563;" in gen_data["patched_css"]
    assert "--- a/styles.css" in gen_data["diff"]


def test_api_session_lifecycle_direct():
    # Save
    save_req = SessionSaveRequest(
        name="Direct Integration Audit",
        input_type="paste",
        html_content="<p>Test</p>",
        css_content="",
        summary={"compliance_score": 90.0, "total_analyzed": 5},
        findings=[],
        tokens=[]
    )
    save_res = save_session(save_req)
    assert save_res["success"] is True
    session_id = save_res["session_id"]

    # Get
    loaded = get_session(session_id)
    assert loaded["name"] == "Direct Integration Audit"

    # Rename
    renamed = rename_session(session_id, SessionRenameRequest(name="Renamed Direct"))
    assert renamed["name"] == "Renamed Direct"

    # Delete
    deleted = delete_session(session_id)
    assert deleted["success"] is True
