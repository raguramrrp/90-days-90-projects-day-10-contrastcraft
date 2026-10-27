"""
Unit tests for WCAG Thresholds and Classification Engine
"""

import pytest
from backend.app.core.classifier import classify_contrast, is_large_text_evaluation


def test_large_text_evaluation():
    # 24px regular is large text (>= 18pt)
    assert is_large_text_evaluation(24.0, "normal") is True
    assert is_large_text_evaluation(20.0, "normal") is False

    # 19px bold is large text (>= 14pt bold)
    assert is_large_text_evaluation(19.0, "bold") is True
    assert is_large_text_evaluation(19.0, "700") is True
    assert is_large_text_evaluation(16.0, "bold") is False


def test_normal_text_aa_and_aaa():
    # 5.0:1 passes AA (4.5), but fails AAA (7.0)
    res_5 = classify_contrast(5.0, element_role="text", font_size_px=16.0)
    assert res_5.pass_aa is True
    assert res_5.pass_aaa is False
    assert res_5.status == "pass_aa_only"
    assert res_5.target_threshold == 4.5

    # 8.0:1 passes both AA and AAA
    res_8 = classify_contrast(8.0, element_role="text", font_size_px=16.0)
    assert res_8.pass_aa is True
    assert res_8.pass_aaa is True
    assert res_8.status == "pass"

    # 3.5:1 fails normal text AA
    res_3_5 = classify_contrast(3.5, element_role="text", font_size_px=16.0)
    assert res_3_5.pass_aa is False
    assert res_3_5.status == "fail_aa"
    assert res_3_5.severity == "high"

    # 2.0:1 is critical failure
    res_2 = classify_contrast(2.0, element_role="text", font_size_px=16.0)
    assert res_2.severity == "critical"


def test_large_text_aa_and_aaa():
    # Large text threshold is 3.0:1 for AA and 4.5:1 for AAA
    res_large_3_5 = classify_contrast(3.5, element_role="heading", font_size_px=28.0)
    assert res_large_3_5.is_large_text is True
    assert res_large_3_5.target_threshold == 3.0
    assert res_large_3_5.pass_aa is True
    assert res_large_3_5.pass_aaa is False

    res_large_5 = classify_contrast(5.0, element_role="heading", font_size_px=28.0)
    assert res_large_5.pass_aa is True
    assert res_large_5.pass_aaa is True


def test_non_text_ui_component_boundary():
    # SC 1.4.11 requires 3.0:1 for UI boundaries
    res_border_pass = classify_contrast(3.2, element_role="ui_component_boundary")
    assert res_border_pass.pass_non_text is True
    assert res_border_pass.pass_aa is True
    assert res_border_pass.target_threshold == 3.0

    res_border_fail = classify_contrast(2.1, element_role="ui_component_boundary")
    assert res_border_fail.pass_non_text is False
    assert res_border_fail.pass_aa is False
    assert res_border_fail.status == "fail_non_text"
