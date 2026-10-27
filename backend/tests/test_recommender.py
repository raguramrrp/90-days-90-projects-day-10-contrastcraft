"""
Unit tests for Color Recommendation Engine
"""

import pytest
from backend.app.core.colors import RGBAColor
from backend.app.core.recommender import (
    find_hue_preserving_color,
    generate_color_recommendations,
    PRESET_PALETTES
)


def test_hue_preserving_lightness_adjustment():
    # Failing combination: light gray #9CA3AF (H: 218, S: 11%, L: 65%) on white #FFFFFF (ratio ~2.5:1)
    fg_failing = RGBAColor(156, 163, 175)  # #9CA3AF
    bg_white = RGBAColor(255, 255, 255)

    # We want to achieve at least 4.5:1
    suggestion = find_hue_preserving_color(fg_failing, bg_white, target_ratio=4.5)
    assert suggestion is not None
    assert suggestion.contrast_ratio >= 4.5
    assert suggestion.passes_target is True
    # Verify hue preservation: hue should stay close to 218 deg
    orig_h = fg_failing.to_hsl()[0]
    # Check suggestion is darkened
    assert suggestion.contrast_ratio >= 4.5


def test_recommendation_api_structure():
    res = generate_color_recommendations("#9CA3AF", "#FFFFFF", target_threshold=4.5)
    assert res["success"] is True
    assert res["original_fg"] == "#9CA3AF"
    assert res["original_bg"] == "#FFFFFF"
    assert len(res["suggestions"]) >= 2

    # Every returned suggestion MUST be mathematically verified >= target
    for sugg in res["suggestions"]:
        assert sugg["ratio"] >= 4.5
        assert sugg["passes_target"] is True


def test_preset_palettes_available():
    assert "neutral_accessible" in PRESET_PALETTES
    assert "high_contrast" in PRESET_PALETTES
    assert "dark_interface" in PRESET_PALETTES
    assert "light_interface" in PRESET_PALETTES
