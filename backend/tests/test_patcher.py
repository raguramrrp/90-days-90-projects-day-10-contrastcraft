"""
Unit tests for CSS Patch Generation and Safe File Application
"""

import pytest
from pathlib import Path
from backend.app.core.patcher import (
    generate_css_patch,
    apply_patch_safely,
    revert_patch_safely
)


def test_targeted_css_patch_generation():
    original_css = """
    /* Main Stylesheet */
    .hero-title {
        font-size: 32px;
        color: #9CA3AF; /* Failing color */
        margin-bottom: 12px;
    }
    .hero-btn {
        background-color: #2563EB;
        color: #FFFFFF;
    }
    """
    proposal = generate_css_patch(
        css_content=original_css,
        selector=".hero-title",
        property_name="color",
        new_value="#4B5563",
        file_name="hero.css"
    )

    assert proposal.target_selector == ".hero-title"
    assert proposal.target_property == "color"
    assert proposal.original_value == "#9CA3AF"
    assert proposal.proposed_value == "#4B5563"
    assert "color: #4B5563;" in proposal.patched_snippet
    # Verify unrelated button rule remains completely intact
    assert ".hero-btn" in proposal.patched_snippet
    assert "background-color: #2563EB;" in proposal.patched_snippet
    # Verify diff contains expected unified markers
    assert "--- a/hero.css" in proposal.diff_text
    assert "+++ b/hero.css" in proposal.diff_text


def test_safe_patch_application_safety(tmp_path):
    target_file = tmp_path / "test.css"
    original_text = ".btn { color: #aaa; }\n"
    target_file.write_text(original_text, encoding="utf-8")

    patched_text = ".btn { color: #111; }\n"

    # Attempt without explicit approval MUST fail
    unapproved_res = apply_patch_safely(target_file, patched_text, explicit_approval=False)
    assert unapproved_res["success"] is False
    assert target_file.read_text(encoding="utf-8") == original_text

    # With explicit approval: succeeds and creates .bak backup
    approved_res = apply_patch_safely(target_file, patched_text, explicit_approval=True)
    assert approved_res["success"] is True
    assert target_file.read_text(encoding="utf-8") == patched_text

    backup_file = target_file.with_suffix(".css.bak")
    assert backup_file.exists()
    assert backup_file.read_text(encoding="utf-8") == original_text
