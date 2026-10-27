"""
Unit tests for Color Parsing, Conversions, and Alpha Compositing
"""

import pytest
from backend.app.core.colors import (
    RGBAColor,
    parse_color,
    composite_colors
)


def test_hex_parsing():
    # 3-digit hex #fff
    c3, s3 = parse_color("#fff")
    assert c3 is not None
    assert (c3.r, c3.g, c3.b, c3.a) == (255, 255, 255, 1.0)
    assert s3 == "hex"

    # 4-digit hex #fff8
    c4, s4 = parse_color("#fff8")
    assert c4 is not None
    assert c4.r == 255 and c4.g == 255 and c4.b == 255
    assert pytest.approx(c4.a, rel=1e-2) == 0.533
    assert s4 == "hex_alpha"

    # 6-digit hex #111827
    c6, s6 = parse_color("#111827")
    assert c6 is not None
    assert (c6.r, c6.g, c6.b, c6.a) == (17, 24, 39, 1.0)
    assert s6 == "hex"

    # 8-digit hex #11182780
    c8, s8 = parse_color("#11182780")
    assert c8 is not None
    assert (c8.r, c8.g, c8.b) == (17, 24, 39)
    assert pytest.approx(c8.a, rel=1e-2) == 0.502
    assert s8 == "hex_alpha"


def test_rgb_and_rgba_parsing():
    # Comma syntax
    c_rgb, _ = parse_color("rgb(255, 0, 128)")
    assert c_rgb is not None
    assert (c_rgb.r, c_rgb.g, c_rgb.b, c_rgb.a) == (255, 0, 128, 1.0)

    c_rgba, _ = parse_color("rgba(0, 50, 100, 0.4)")
    assert c_rgba is not None
    assert (c_rgba.r, c_rgba.g, c_rgba.b) == (0, 50, 100)
    assert pytest.approx(c_rgba.a, rel=1e-2) == 0.4

    # Slash syntax CSS4
    c_slash, _ = parse_color("rgb(10 20 30 / 80%)")
    assert c_slash is not None
    assert (c_slash.r, c_slash.g, c_slash.b) == (10, 20, 30)
    assert pytest.approx(c_slash.a, rel=1e-2) == 0.8


def test_hsl_and_hsla_parsing():
    c_hsl, _ = parse_color("hsl(210, 100%, 50%)")
    assert c_hsl is not None
    # 210 deg pure blue-cyan
    assert c_hsl.r == 0
    assert c_hsl.g in (127, 128)
    assert c_hsl.b == 255

    # Angles with deg and turn
    c_turn, _ = parse_color("hsl(0.5turn, 100%, 50%)")
    assert c_turn is not None
    # 0.5 turn = 180 deg (cyan)
    assert c_turn.r == 0 and c_turn.g == 255 and c_turn.b == 255


def test_named_colors():
    c_white, _ = parse_color("white")
    c_navy, _ = parse_color("navy")
    c_rebecca, _ = parse_color("rebeccapurple")

    assert c_white == RGBAColor(255, 255, 255, 1.0, raw="white")
    assert c_navy == RGBAColor(0, 0, 128, 1.0, raw="navy")
    assert c_rebecca == RGBAColor(102, 51, 153, 1.0, raw="rebeccapurple")


def test_css_variables_and_fallbacks():
    vars_dict = {
        "--text-primary": "#0F172A",
        "--accent": "rgb(2, 132, 199)"
    }
    # Direct var
    c_var, s_var = parse_color("var(--text-primary)", variables=vars_dict)
    assert c_var is not None
    assert c_var.r == 15 and c_var.g == 23 and c_var.b == 42

    # Fallback used when var missing
    c_fb, s_fb = parse_color("var(--missing, #DC2626)", variables=vars_dict)
    assert c_fb is not None
    assert c_fb.r == 220 and c_fb.g == 38 and c_fb.b == 38
    assert "fallback" in s_fb

    # Missing var without fallback
    c_none, s_none = parse_color("var(--unknown)", variables=vars_dict)
    assert c_none is None
    assert "unresolved_css_variable" in s_none


def test_alpha_compositing():
    # 50% black over 100% white -> exact 50% gray (128, 128, 128)
    fg_semi = RGBAColor(0, 0, 0, 0.5, raw="rgba(0,0,0,0.5)")
    bg_white = RGBAColor(255, 255, 255, 1.0, raw="#FFFFFF")

    comp = composite_colors(fg_semi, bg_white)
    assert comp.r == 128
    assert comp.g == 128
    assert comp.b == 128
    assert comp.a == 1.0


def test_unsupported_dynamic_indicators():
    # Gradients and images should return None and flag browser requirement
    c_grad, s_grad = parse_color("linear-gradient(to right, red, blue)")
    assert c_grad is None
    assert s_grad == "gradient_requires_browser"

    c_img, s_img = parse_color("url('/bg.png')")
    assert c_img is None
    assert s_img == "background_image_requires_browser"
