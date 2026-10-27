"""
ContrastCraft — Color Recommendation Engine
Generates mathematically verified, hue-preserving accessible color recommendations.
Adjusts lightness in HSL color space with minimal perceptual delta to satisfy WCAG targets.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from .colors import RGBAColor, parse_color
from .contrast import calculate_contrast_ratio, calculate_relative_luminance, format_ratio


@dataclass
class ColorSuggestion:
    hex_color: str
    rgb_str: str
    contrast_ratio: float
    formatted_ratio: str
    target_threshold: float
    passes_target: bool
    passes_aa: bool
    passes_aaa: bool
    passes_ui: bool
    lightness_shift: float
    description: str


PRESET_PALETTES: Dict[str, Dict[str, str]] = {
    "neutral_accessible": {
        "name": "Neutral Accessible",
        "description": "Crisp slate on clean white, balanced for high readability and timeless elegance.",
        "foreground": "#0F172A",
        "background": "#FFFFFF",
        "accent": "#0284C7",
        "border": "#475569"
    },
    "high_contrast": {
        "name": "High Contrast",
        "description": "Maximum legibility pairing deep pitch black with pure luminous white.",
        "foreground": "#000000",
        "background": "#FFFFFF",
        "accent": "#0055FF",
        "border": "#000000"
    },
    "soft_professional": {
        "name": "Soft Professional",
        "description": "Executive navy on cool mist gray, reducing eye strain for long sessions.",
        "foreground": "#1E293B",
        "background": "#F8FAFC",
        "accent": "#2563EB",
        "border": "#64748B"
    },
    "editorial": {
        "name": "Editorial",
        "description": "Warm espresso on warm parchment cream, ideal for article and narrative layouts.",
        "foreground": "#271D15",
        "background": "#FAF7F2",
        "accent": "#B45309",
        "border": "#78350F"
    },
    "dark_interface": {
        "name": "Dark Interface",
        "description": "Bright cool text on deep space obsidian, tested for low glare and high contrast.",
        "foreground": "#F8FAFC",
        "background": "#0F172A",
        "accent": "#38BDF8",
        "border": "#94A3B8"
    },
    "light_interface": {
        "name": "Light Interface",
        "description": "Deep graphite on clean zinc, modern developer tooling aesthetic.",
        "foreground": "#18181B",
        "background": "#FAFAFA",
        "accent": "#4F46E5",
        "border": "#71717A"
    }
}


def find_hue_preserving_color(
    original_fg: RGBAColor,
    bg_color: RGBAColor,
    target_ratio: float = 4.5
) -> Optional[ColorSuggestion]:
    """
    Finds the minimal lightness adjustment to original_fg in HSL space that achieves target_ratio against bg_color.
    Evaluates both darkening and lightening to find the smallest perceptible shift.
    """
    h, s, orig_l = original_fg.to_hsl()
    bg_lum = calculate_relative_luminance(bg_color)

    best_cand: Optional[RGBAColor] = None
    min_delta = 999.0
    best_ratio = 0.0

    # Search directions: test all integer lightness steps from 0 to 100
    for l_cand in range(0, 101):
        cand = RGBAColor.from_hsl(h, s, float(l_cand), a=original_fg.a)
        ratio, _, _ = calculate_contrast_ratio(cand, bg_color)
        if ratio >= target_ratio:
            delta = abs(float(l_cand) - orig_l)
            if delta < min_delta:
                min_delta = delta
                best_cand = cand
                best_ratio = ratio

    if not best_cand:
        # If saturation was too high or hue restricted luminance, fallback to desaturating
        for s_cand in [s * 0.75, s * 0.5, 0.0]:
            for l_cand in (0, 100):
                cand = RGBAColor.from_hsl(h, s_cand, float(l_cand), a=original_fg.a)
                ratio, _, _ = calculate_contrast_ratio(cand, bg_color)
                if ratio >= target_ratio:
                    best_cand = cand
                    best_ratio = ratio
                    min_delta = abs(float(l_cand) - orig_l)
                    break
            if best_cand:
                break

    if not best_cand:
        return None

    passes_aa = best_ratio >= 4.5
    passes_aaa = best_ratio >= 7.0
    passes_ui = best_ratio >= 3.0

    shift_desc = f"{'Darkened' if best_cand.to_hsl()[2] < orig_l else 'Lightened'} lightness by {min_delta:.1f}%"

    return ColorSuggestion(
        hex_color=best_cand.to_hex(),
        rgb_str=best_cand.to_rgb_str(),
        contrast_ratio=best_ratio,
        formatted_ratio=format_ratio(best_ratio),
        target_threshold=target_ratio,
        passes_target=best_ratio >= target_ratio,
        passes_aa=passes_aa,
        passes_aaa=passes_aaa,
        passes_ui=passes_ui,
        lightness_shift=min_delta,
        description=f"Minimal shift recommendation ({shift_desc})"
    )


def generate_color_recommendations(
    fg_str: str,
    bg_str: str,
    target_threshold: float = 4.5
) -> Dict[str, Any]:
    """
    Produces primary recommendation and varied compliant alternatives.
    Guarantees every returned suggestion is mathematically verified against the actual background.
    """
    fg_c, fg_status = parse_color(fg_str)
    bg_c, bg_status = parse_color(bg_str)

    if not fg_c or not bg_c:
        return {
            "success": False,
            "error": f"Could not parse colors: fg='{fg_str}' ({fg_status}), bg='{bg_str}' ({bg_status})",
            "recommendations": []
        }

    orig_ratio, _, _ = calculate_contrast_ratio(fg_c, bg_c)

    # 1. Primary minimal shift suggestion
    primary = find_hue_preserving_color(fg_c, bg_c, target_threshold)

    # 2. Enhanced AAA suggestion (7.0:1)
    aaa_sugg = find_hue_preserving_color(fg_c, bg_c, 7.0)
    if aaa_sugg:
        aaa_sugg.description = "Enhanced Level AAA target (7.0:1)"

    # 3. High-contrast pure boundary (Black or White)
    white_c = RGBAColor(255, 255, 255)
    black_c = RGBAColor(0, 0, 0)
    r_white, _, _ = calculate_contrast_ratio(white_c, bg_c)
    r_black, _, _ = calculate_contrast_ratio(black_c, bg_c)
    hi_c = white_c if r_white > r_black else black_c
    hi_ratio = max(r_white, r_black)
    hi_sugg = ColorSuggestion(
        hex_color=hi_c.to_hex(),
        rgb_str=hi_c.to_rgb_str(),
        contrast_ratio=hi_ratio,
        formatted_ratio=format_ratio(hi_ratio),
        target_threshold=target_threshold,
        passes_target=hi_ratio >= target_threshold,
        passes_aa=hi_ratio >= 4.5,
        passes_aaa=hi_ratio >= 7.0,
        passes_ui=hi_ratio >= 3.0,
        lightness_shift=abs(hi_c.to_hsl()[2] - fg_c.to_hsl()[2]),
        description="High Contrast Anchor"
    )

    # Gather suggestions, deduplicating identical hexes
    seen_hexes = set()
    suggestions: List[Dict[str, Any]] = []

    for s in [primary, aaa_sugg, hi_sugg]:
        if s and s.hex_color not in seen_hexes:
            seen_hexes.add(s.hex_color)
            suggestions.append({
                "hex": s.hex_color,
                "rgb": s.rgb_str,
                "ratio": s.contrast_ratio,
                "formatted_ratio": s.formatted_ratio,
                "passes_target": s.passes_target,
                "passes_aa": s.passes_aa,
                "passes_aaa": s.passes_aaa,
                "passes_ui": s.passes_ui,
                "lightness_shift": round(s.lightness_shift, 1),
                "description": s.description
            })

    return {
        "success": True,
        "original_fg": fg_c.to_hex(),
        "original_bg": bg_c.to_hex(),
        "original_ratio": orig_ratio,
        "original_formatted_ratio": format_ratio(orig_ratio),
        "target_threshold": target_threshold,
        "suggestions": suggestions,
        "presets": PRESET_PALETTES
    }
