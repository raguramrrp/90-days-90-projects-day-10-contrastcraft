"""
ContrastCraft — WCAG 2.1 / 2.2 Relative Luminance and Contrast Ratio Engine
Independent mathematical calculation engine implementing the official W3C / WCAG formulas.
"""

from __future__ import annotations
from typing import Tuple
from .colors import RGBAColor, composite_colors


def channel_to_linear(channel_val: int) -> float:
    """
    Linearize a normalized sRGB channel value according to WCAG 2.1 / 2.2 specifications.
    Formula:
      c = channel_val / 255.0
      if c <= 0.04045: return c / 12.92
      else: return ((c + 0.055) / 1.055) ** 2.4
    """
    c = max(0.0, min(255.0, float(channel_val))) / 255.0
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4


def calculate_relative_luminance(color: RGBAColor) -> float:
    """
    Calculate the relative luminance of a color according to WCAG 2.1 / 2.2.
    Formula:
      L = 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin
    Returns a float between 0.0 (pure black) and 1.0 (pure white).
    """
    r_lin = channel_to_linear(color.r)
    g_lin = channel_to_linear(color.g)
    b_lin = channel_to_linear(color.b)

    lum = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    return max(0.0, min(1.0, lum))


def calculate_contrast_ratio(
    foreground: RGBAColor,
    background: RGBAColor
) -> Tuple[float, RGBAColor, RGBAColor]:
    """
    Calculate the WCAG contrast ratio between effective foreground and background.
    If the foreground or background is semi-transparent, handles alpha compositing.
    Formula:
      ratio = (L_lighter + 0.05) / (L_darker + 0.05)
    Returns:
      (contrast_ratio, effective_foreground, effective_background)
    """
    eff_bg = background
    # If foreground has transparency and background is known, composite fg over bg
    if foreground.a < 0.999:
        eff_fg = composite_colors(foreground, eff_bg)
    else:
        eff_fg = foreground

    l1 = calculate_relative_luminance(eff_fg)
    l2 = calculate_relative_luminance(eff_bg)

    l_lighter = max(l1, l2)
    l_darker = min(l1, l2)

    ratio = (l_lighter + 0.05) / (l_darker + 0.05)
    return ratio, eff_fg, eff_bg


def format_ratio(ratio: float) -> str:
    """Format contrast ratio as standard X.XX:1 string."""
    return f"{ratio:.2f}:1"


def calculate_apca(foreground: RGBAColor, background: RGBAColor) -> float:
    """
    Calculate the Advanced Perceptual Contrast Algorithm (APCA) Lc (Lightness contrast) value.
    Candidate perceptual metric for WCAG 3.0.
    Returns signed float:
      Positive Lc: Dark text on light background.
      Negative Lc: Light text on dark background.
    """
    def srgb_to_y(c: RGBAColor) -> float:
        r = (c.r / 255.0) ** 2.4
        g = (c.g / 255.0) ** 2.4
        b = (c.b / 255.0) ** 2.4
        return 0.2126729 * r + 0.7151522 * g + 0.0721750 * b

    y_fg = srgb_to_y(foreground)
    y_bg = srgb_to_y(background)

    # Soft clamp for black level flare
    blk_thresh = 0.022
    blk_clamp = 1.414
    if y_fg < blk_thresh:
        y_fg += (blk_thresh - y_fg) ** blk_clamp
    if y_bg < blk_thresh:
        y_bg += (blk_thresh - y_bg) ** blk_clamp

    if y_bg > y_fg:
        # Dark text on light background
        s_bg = y_bg ** 0.56
        s_fg = y_fg ** 0.57
        lc = (s_bg - s_fg) * 1.14
    else:
        # Light text on dark background
        s_bg = y_bg ** 0.65
        s_fg = y_fg ** 0.62
        lc = (s_bg - s_fg) * 1.14

    return round(lc * 100.0, 1)

