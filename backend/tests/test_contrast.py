"""
Unit tests for ContrastCraft WCAG Contrast Calculation Engine
"""

import pytest
from backend.app.core.colors import RGBAColor
from backend.app.core.contrast import (
    channel_to_linear,
    calculate_relative_luminance,
    calculate_contrast_ratio,
    calculate_apca,
    format_ratio
)


def test_channel_to_linear():
    # Test boundary below threshold 0.04045
    # channel_val = 10 -> c = 10 / 255.0 = 0.0392156 <= 0.04045
    val_low = channel_to_linear(10)
    expected_low = (10 / 255.0) / 12.92
    assert pytest.approx(val_low, rel=1e-4) == expected_low

    # Test boundary above threshold
    # channel_val = 255 -> c = 1.0 -> ((1.0 + 0.055) / 1.055) ** 2.4 = 1.0
    val_high = channel_to_linear(255)
    assert pytest.approx(val_high, rel=1e-4) == 1.0

    # channel_val = 0 -> 0.0
    assert channel_to_linear(0) == 0.0


def test_relative_luminance_extremes():
    black = RGBAColor(0, 0, 0)
    white = RGBAColor(255, 255, 255)

    lum_black = calculate_relative_luminance(black)
    lum_white = calculate_relative_luminance(white)

    assert lum_black == 0.0
    assert pytest.approx(lum_white, rel=1e-4) == 1.0


def test_black_on_white_21_to_1():
    black = RGBAColor(0, 0, 0)
    white = RGBAColor(255, 255, 255)

    ratio_bw, _, _ = calculate_contrast_ratio(black, white)
    ratio_wb, _, _ = calculate_contrast_ratio(white, black)

    assert pytest.approx(ratio_bw, rel=1e-2) == 21.0
    assert pytest.approx(ratio_wb, rel=1e-2) == 21.0
    assert format_ratio(ratio_bw) == "21.00:1"


def test_equal_colors_1_to_1():
    gray = RGBAColor(128, 128, 128)
    ratio, _, _ = calculate_contrast_ratio(gray, gray)
    assert pytest.approx(ratio, rel=1e-2) == 1.0
    assert format_ratio(ratio) == "1.00:1"


def test_known_wcag_boundary():
    # #767676 on #FFFFFF is the canonical boundary for 4.54:1 (passes AA normal text)
    fg = RGBAColor(118, 118, 118)  # #767676
    bg = RGBAColor(255, 255, 255)
    ratio, _, _ = calculate_contrast_ratio(fg, bg)
    assert ratio >= 4.5
    assert ratio < 4.6

    # #777777 on #FFFFFF fails 4.5:1 (approximately 4.47:1)
    fg_fail = RGBAColor(119, 119, 119)
    ratio_fail, _, _ = calculate_contrast_ratio(fg_fail, bg)
    assert ratio_fail < 4.5


def test_apca_calculation():
    black = RGBAColor(0, 0, 0)
    white = RGBAColor(255, 255, 255)
    # Black text on white background yields high positive Lc (~100+)
    lc_dark_on_light = calculate_apca(black, white)
    assert lc_dark_on_light > 100.0

    # White text on black background yields high negative Lc (~ -100)
    lc_light_on_dark = calculate_apca(white, black)
    assert lc_light_on_dark < -100.0
