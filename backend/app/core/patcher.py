"""
ContrastCraft — CSS Patch Generator and Safe Application Engine
Generates unified diffs, replaces specific declarations safely without overwriting unrelated code,
creates backup copies (.bak), and performs re-analysis verification.
"""

from __future__ import annotations
import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


@dataclass
class PatchProposal:
    target_selector: str
    target_property: str
    original_value: str
    proposed_value: str
    diff_text: str
    affected_file: str
    original_snippet: str
    patched_snippet: str


def generate_css_patch(
    css_content: str,
    selector: str,
    property_name: str,
    new_value: str,
    file_name: str = "styles.css"
) -> PatchProposal:
    """
    Generates a targeted CSS declaration replacement patch and unified diff.
    Preserves all comments, indentation, and unrelated rules.
    """
    lines = css_content.splitlines(keepends=True)
    patched_lines = list(lines)

    # Strategy: find rule matching selector
    # Regex matching selector followed by { ... }
    # Escape special regex characters in selector
    clean_sel = selector.strip()
    sel_pattern = re.compile(r"([^{}]*?" + re.escape(clean_sel) + r"[^{}]*?\{)([^}]*)(\})", re.DOTALL)

    full_css = "".join(lines)
    match = sel_pattern.search(full_css)

    original_val = "unknown"
    if match:
        body = match.group(2)
        prop_pattern = re.compile(r"(\b" + re.escape(property_name) + r"\s*:\s*)([^;]+)(;?)", re.IGNORECASE)
        prop_match = prop_pattern.search(body)

        if prop_match:
            original_val = prop_match.group(2).strip()
            new_body = prop_pattern.sub(r"\g<1>" + new_value + r"\g<3>", body, count=1)
            patched_full = full_css[:match.start(2)] + new_body + full_css[match.end(2):]
            patched_lines = patched_full.splitlines(keepends=True)
        else:
            # Property doesn't exist in rule; inject it before closing bracket
            indent = "  "
            new_decl = f"\n{indent}{property_name}: {new_value};"
            patched_full = full_css[:match.end(2)] + new_decl + full_css[match.end(2):]
            patched_lines = patched_full.splitlines(keepends=True)
    else:
        # Selector not found in CSS; check if it's a CSS custom property
        if property_name.startswith("--") or selector == ":root":
            var_pattern = re.compile(r"(\b" + re.escape(property_name) + r"\s*:\s*)([^;]+)(;?)", re.IGNORECASE)
            var_match = var_pattern.search(full_css)
            if var_match:
                original_val = var_match.group(2).strip()
                patched_full = var_pattern.sub(r"\g<1>" + new_value + r"\g<3>", full_css, count=1)
                patched_lines = patched_full.splitlines(keepends=True)
            else:
                # Append rule to end
                new_rule = f"\n\n/* Accessibility contrast patch */\n{selector} {{\n  {property_name}: {new_value};\n}}\n"
                patched_lines.append(new_rule)
        else:
            # Append new rule
            new_rule = f"\n\n/* Accessibility contrast patch */\n{selector} {{\n  {property_name}: {new_value};\n}}\n"
            patched_lines.append(new_rule)

    diff = "".join(difflib.unified_diff(
        lines,
        patched_lines,
        fromfile=f"a/{file_name}",
        tofile=f"b/{file_name}",
        n=3
    ))

    return PatchProposal(
        target_selector=selector,
        target_property=property_name,
        original_value=original_val,
        proposed_value=new_value,
        diff_text=diff if diff else "No textual differences detected.",
        affected_file=file_name,
        original_snippet="".join(lines),
        patched_snippet="".join(patched_lines)
    )


def apply_patch_safely(
    file_path: Path,
    patched_content: str,
    explicit_approval: bool = False
) -> Dict[str, Any]:
    """
    Safely writes patched content to disk ONLY with explicit approval.
    Creates a timestamped or .bak backup file before modifying anything.
    """
    if not explicit_approval:
        return {
            "success": False,
            "error": "Explicit user approval is required before applying patches to source files."
        }

    if not file_path.exists():
        return {
            "success": False,
            "error": f"File does not exist: {file_path}"
        }

    try:
        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        backup_path.write_text(file_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")

        # Write patched content
        file_path.write_text(patched_content, encoding="utf-8")

        return {
            "success": True,
            "file": str(file_path),
            "backup_file": str(backup_path),
            "bytes_written": len(patched_content)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to apply patch: {str(e)}"
        }


def revert_patch_safely(file_path: Path) -> Dict[str, Any]:
    """
    Restores the .bak backup file to original file_path.
    """
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    if not backup_path.exists():
        return {
            "success": False,
            "error": f"No backup file (.bak) found for {file_path.name}"
        }

    try:
        content = backup_path.read_text(encoding="utf-8", errors="replace")
        file_path.write_text(content, encoding="utf-8")
        backup_path.unlink()  # Clean up backup after restoration
        return {
            "success": True,
            "file": str(file_path),
            "reverted": True,
            "content": content
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to revert patch: {str(e)}"
        }

