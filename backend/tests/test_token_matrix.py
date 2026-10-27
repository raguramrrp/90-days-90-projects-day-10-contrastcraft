"""
Unit tests for Design Token Intelligence & Compatibility Matrix
"""

import pytest
from backend.app.core.token_matrix import TokenIntelligenceEngine


def test_token_matrix_generation():
    engine = TokenIntelligenceEngine()
    tokens = [
        {"name": "--color-primary", "value": "#0284C7"},
        {"name": "--color-bg", "value": "#FFFFFF"},
        {"name": "--color-dark", "value": "#0F172A"},
        {"name": "--color-muted", "value": "#94A3B8"}
    ]

    result = engine.build_matrix(tokens)
    assert result["token_count"] == 4
    assert len(result["matrix_cells"]) == 4 * 3  # 12 distinct pairs
    assert "duplicates" in result

    # Check cell structure
    cell = result["matrix_cells"][0]
    assert "fg_token" in cell
    assert "bg_token" in cell
    assert "contrast_ratio" in cell
    assert "apca_lc" in cell
    assert "pass_normal_aa" in cell


def test_duplicate_token_detection():
    engine = TokenIntelligenceEngine()
    tokens = [
        {"name": "--text-dark", "value": "#0F172A"},
        {"name": "--slate-900", "value": "#0F172A"},
        {"name": "--accent", "value": "#0284C7"}
    ]

    result = engine.build_matrix(tokens)
    assert len(result["duplicates"]) == 1
    dup = result["duplicates"][0]
    assert dup["count"] == 2
    assert "--text-dark" in dup["token_names"]
    assert "--slate-900" in dup["token_names"]


def test_token_impact_evaluation():
    engine = TokenIntelligenceEngine()
    tokens = [
        {"name": "--color-muted", "value": "#94A3B8"}
    ]
    findings = [
        {
            "selector": ".hero-caption",
            "foreground_raw": "var(--color-muted)",
            "effective_bg": "#FFFFFF",
            "contrast_ratio": 2.60,
            "target_threshold": 4.5,
            "pass_aa": False
        }
    ]

    # Propose darker token value #596A82 that passes AA
    impact = engine.evaluate_token_impact(
        token_name="--color-muted",
        proposed_value="#596A82",
        findings=findings,
        tokens=tokens
    )

    assert impact["token_name"] == "--color-muted"
    assert impact["failing_usages_resolved"] == 1
    assert ".hero-caption" in impact["affected_selectors"]
    assert impact["net_contrast_gain"] > 1.5
