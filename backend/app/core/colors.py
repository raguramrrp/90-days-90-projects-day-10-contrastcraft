"""
ContrastCraft — Colors Module
Safe, robust CSS color parser, normalizer, and alpha compositor.
Supports Hex, RGB/RGBA, HSL/HSLA, CSS Color 4 syntax, Named colors, CSS custom properties,
and alpha compositing over known backdrops.
"""

from __future__ import annotations
import math
import re
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any


NAMED_COLORS: Dict[str, Tuple[int, int, int]] = {
    "aliceblue": (240, 248, 255), "antiquewhite": (250, 235, 215), "aqua": (0, 255, 255),
    "aquamarine": (127, 255, 212), "azure": (240, 255, 255), "beige": (245, 245, 220),
    "bisque": (255, 228, 196), "black": (0, 0, 0), "blanchedalmond": (255, 235, 205),
    "blue": (0, 0, 255), "blueviolet": (138, 43, 226), "brown": (165, 42, 42),
    "burlywood": (222, 184, 135), "cadetblue": (95, 158, 160), "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30), "coral": (255, 127, 80), "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220), "crimson": (220, 20, 60), "cyan": (0, 255, 255),
    "darkblue": (0, 0, 139), "darkcyan": (0, 139, 139), "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169), "darkgrey": (169, 169, 169), "darkgreen": (0, 100, 0),
    "darkkhaki": (189, 183, 107), "darkmagenta": (139, 0, 139), "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0), "darkorchid": (153, 50, 204), "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122), "darkseagreen": (143, 188, 143), "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79), "darkslategrey": (47, 79, 79), "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211), "deeppink": (255, 20, 147), "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105), "dimgrey": (105, 105, 105), "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34), "floralwhite": (255, 250, 240), "forestgreen": (34, 139, 34),
    "fuchsia": (255, 0, 255), "gainsboro": (220, 220, 220), "ghostwhite": (248, 248, 255),
    "gold": (255, 215, 0), "goldenrod": (218, 165, 32), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "green": (0, 128, 0), "greenyellow": (173, 255, 47),
    "honeydew": (240, 255, 240), "hotpink": (255, 105, 180), "indianred": (205, 92, 92),
    "indigo": (75, 0, 130), "ivory": (255, 255, 240), "khaki": (240, 230, 140),
    "lavender": (230, 230, 250), "lavenderblush": (255, 240, 245), "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205), "lightblue": (173, 216, 230), "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255), "lightgoldenrodyellow": (250, 250, 210), "lightgray": (211, 211, 211),
    "lightgrey": (211, 211, 211), "lightgreen": (144, 238, 144), "lightpink": (255, 182, 193),
    "lightsalmon": (255, 160, 122), "lightseagreen": (32, 178, 170), "lightskyblue": (135, 206, 250),
    "lightslategray": (119, 136, 153), "lightslategrey": (119, 136, 153), "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224), "lime": (0, 255, 0), "limegreen": (50, 205, 50),
    "linen": (250, 240, 230), "magenta": (255, 0, 255), "maroon": (128, 0, 0),
    "mediumaquamarine": (102, 205, 170), "mediumblue": (0, 0, 205), "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219), "mediumseagreen": (60, 179, 113), "mediumslateblue": (123, 104, 238),
    "mediumspringgreen": (0, 250, 154), "mediumturquoise": (72, 209, 204), "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112), "mintcream": (245, 255, 250), "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181), "navajowhite": (255, 222, 173), "navy": (0, 0, 128),
    "oldlace": (253, 245, 230), "olive": (128, 128, 0), "olivedrab": (107, 142, 35),
    "orange": (255, 165, 0), "orangered": (255, 69, 0), "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170), "palegreen": (152, 251, 152), "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 147), "papayawhip": (255, 239, 213), "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63), "pink": (255, 192, 203), "plum": (221, 160, 221),
    "powderblue": (176, 224, 230), "purple": (128, 0, 128), "rebeccapurple": (102, 51, 153),
    "red": (255, 0, 0), "rosybrown": (188, 143, 143), "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19), "salmon": (250, 128, 114), "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87), "seashell": (255, 245, 238), "sienna": (160, 82, 45),
    "silver": (192, 192, 192), "skyblue": (135, 206, 235), "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144), "slategrey": (112, 128, 144), "snow": (255, 250, 250),
    "springgreen": (0, 255, 127), "steelblue": (70, 130, 180), "tan": (210, 180, 140),
    "teal": (0, 128, 128), "thistle": (216, 191, 216), "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208), "violet": (238, 130, 238), "wheat": (245, 222, 179),
    "white": (255, 255, 255), "whitesmoke": (245, 245, 245), "yellow": (255, 255, 0),
    "yellowgreen": (154, 205, 50)
}


@dataclass(frozen=True)
class RGBAColor:
    r: int  # 0 to 255
    g: int  # 0 to 255
    b: int  # 0 to 255
    a: float = 1.0  # 0.0 to 1.0
    raw: str = ""

    def __post_init__(self):
        # Enforce bounds
        r = max(0, min(255, int(round(self.r))))
        g = max(0, min(255, int(round(self.g))))
        b = max(0, min(255, int(round(self.b))))
        a = max(0.0, min(1.0, float(self.a)))
        object.__setattr__(self, "r", r)
        object.__setattr__(self, "g", g)
        object.__setattr__(self, "b", b)
        object.__setattr__(self, "a", round(a, 4))

    @property
    def is_transparent(self) -> bool:
        return self.a <= 0.001

    @property
    def is_semi_transparent(self) -> bool:
        return 0.001 < self.a < 0.999

    def to_hex(self, include_alpha: bool = False) -> str:
        """Returns standard uppercase hex color, e.g. #FFFFFF or #FFFFFF80."""
        if include_alpha and self.a < 0.999:
            alpha_int = int(round(self.a * 255))
            return f"#{self.r:02X}{self.g:02X}{self.b:02X}{alpha_int:02X}"
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def to_rgb_str(self) -> str:
        """Returns standard css rgb() string."""
        return f"rgb({self.r}, {self.g}, {self.b})"

    def to_rgba_str(self) -> str:
        """Returns standard css rgba() string."""
        return f"rgba({self.r}, {self.g}, {self.b}, {self.a:.2f})"

    def to_hsl(self) -> Tuple[float, float, float]:
        """Convert RGB (0-255) to HSL: (H: 0-360, S: 0-100, L: 0-100)."""
        r_norm = self.r / 255.0
        g_norm = self.g / 255.0
        b_norm = self.b / 255.0

        max_val = max(r_norm, g_norm, b_norm)
        min_val = min(r_norm, g_norm, b_norm)
        delta = max_val - min_val

        # Lightness
        l = (max_val + min_val) / 2.0

        if delta == 0:
            h = 0.0
            s = 0.0
        else:
            # Saturation
            s = delta / (1.0 - abs(2.0 * l - 1.0)) if (1.0 - abs(2.0 * l - 1.0)) != 0 else 0.0

            # Hue
            if max_val == r_norm:
                h = 60.0 * (((g_norm - b_norm) / delta) % 6.0)
            elif max_val == g_norm:
                h = 60.0 * (((b_norm - r_norm) / delta) + 2.0)
            else:
                h = 60.0 * (((r_norm - g_norm) / delta) + 4.0)

        h = (h + 360.0) % 360.0
        return round(h, 2), round(s * 100.0, 2), round(l * 100.0, 2)

    @classmethod
    def from_hsl(cls, h: float, s: float, l: float, a: float = 1.0, raw: str = "") -> RGBAColor:
        """Convert HSL (H: 0-360, S: 0-100, L: 0-100) to RGBAColor."""
        h_norm = (h % 360.0) / 360.0
        s_norm = max(0.0, min(100.0, s)) / 100.0
        l_norm = max(0.0, min(100.0, l)) / 100.0

        if s_norm == 0:
            r = g = b = int(round(l_norm * 255))
        else:
            def hue2rgb(p: float, q: float, t: float) -> float:
                if t < 0:
                    t += 1.0
                if t > 1:
                    t -= 1.0
                if t < 1.0 / 6.0:
                    return p + (q - p) * 6.0 * t
                if t < 1.0 / 2.0:
                    return q
                if t < 2.0 / 3.0:
                    return p + (q - p) * (2.0 / 3.0 - t) * 6.0
                return p

            q = l_norm * (1.0 + s_norm) if l_norm < 0.5 else l_norm + s_norm - l_norm * s_norm
            p = 2.0 * l_norm - q

            r = int(round(hue2rgb(p, q, h_norm + 1.0 / 3.0) * 255))
            g = int(round(hue2rgb(p, q, h_norm) * 255))
            b = int(round(hue2rgb(p, q, h_norm - 1.0 / 3.0) * 255))

        return cls(r=r, g=g, b=b, a=a, raw=raw)


def composite_colors(foreground: RGBAColor, background: RGBAColor) -> RGBAColor:
    """
    Standard Alpha compositing (Porter-Duff 'over' operator).
    Composites foreground over background.
    If background is opaque (alpha == 1.0), output alpha is 1.0.
    """
    fg_a = foreground.a
    bg_a = background.a

    if fg_a >= 0.999:
        return RGBAColor(foreground.r, foreground.g, foreground.b, 1.0, raw=foreground.raw)
    
    if fg_a <= 0.001:
        return background

    # Target alpha: a_out = fg_a + bg_a * (1 - fg_a)
    out_a = fg_a + bg_a * (1.0 - fg_a)
    if out_a <= 0.0001:
        return RGBAColor(0, 0, 0, 0.0)

    # Channel compositing
    out_r = (foreground.r * fg_a + background.r * bg_a * (1.0 - fg_a)) / out_a
    out_g = (foreground.g * fg_a + background.g * bg_a * (1.0 - fg_a)) / out_a
    out_b = (foreground.b * fg_a + background.b * bg_a * (1.0 - fg_a)) / out_a

    return RGBAColor(
        r=int(round(out_r)),
        g=int(round(out_g)),
        b=int(round(out_b)),
        a=out_a,
        raw=f"composite({foreground.raw} over {background.raw})"
    )


def parse_color(
    color_str: str,
    variables: Optional[Dict[str, str]] = None,
    depth: int = 0
) -> Tuple[Optional[RGBAColor], Optional[str]]:
    """
    Parse a CSS color string into an RGBAColor.
    Returns (color, reason_or_status).
    If color cannot be parsed statically, returns (None, reason).
    """
    if not color_str or not isinstance(color_str, str):
        return None, "empty_or_invalid"

    raw_clean = color_str.strip().lower()
    # Strip !important
    raw_clean = re.sub(r"\s*!important\s*$", "", raw_clean).strip()
    # Strip comments /* ... */
    raw_clean = re.sub(r"/\*.*?\*/", "", raw_clean).strip()

    if not raw_clean:
        return None, "empty"

    # Check for unsupported or dynamic backgrounds
    if "url(" in raw_clean:
        return None, "background_image_requires_browser"
    if "gradient(" in raw_clean:
        return None, "gradient_requires_browser"
    if raw_clean in ("inherit", "initial", "unset", "revert", "revert-layer"):
        return None, f"css_keyword_{raw_clean}"
    if raw_clean == "currentcolor":
        return None, "currentcolor_needs_cascade_resolution"
    if raw_clean == "transparent":
        return RGBAColor(0, 0, 0, 0.0, raw="transparent"), "transparent"

    # CSS Custom Property: var(--name) or var(--name, fallback)
    if raw_clean.startswith("var(") and raw_clean.endswith(")"):
        if depth > 10:
            return None, "cyclic_css_variable"
        inner = raw_clean[4:-1].strip()
        # Split on comma for fallback if present
        parts = inner.split(",", 1)
        var_name = parts[0].strip()
        fallback = parts[1].strip() if len(parts) > 1 else None

        if variables and var_name in variables:
            return parse_color(variables[var_name], variables, depth + 1)
        elif fallback:
            res_c, res_s = parse_color(fallback, variables, depth + 1)
            if res_c:
                return res_c, f"fallback_from_{var_name}"
            return None, f"unresolved_css_variable_{var_name}"
        else:
            return None, f"unresolved_css_variable_{var_name}"

    # Hex: #RGB, #RGBA, #RRGGBB, #RRGGBBAA
    if raw_clean.startswith("#"):
        hex_val = raw_clean[1:]
        if len(hex_val) == 3:  # #RGB
            r = int(hex_val[0] * 2, 16)
            g = int(hex_val[1] * 2, 16)
            b = int(hex_val[2] * 2, 16)
            return RGBAColor(r, g, b, 1.0, raw=color_str), "hex"
        elif len(hex_val) == 4:  # #RGBA
            r = int(hex_val[0] * 2, 16)
            g = int(hex_val[1] * 2, 16)
            b = int(hex_val[2] * 2, 16)
            a = int(hex_val[3] * 2, 16) / 255.0
            return RGBAColor(r, g, b, a, raw=color_str), "hex_alpha"
        elif len(hex_val) == 6:  # #RRGGBB
            try:
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
                return RGBAColor(r, g, b, 1.0, raw=color_str), "hex"
            except ValueError:
                return None, "invalid_hex"
        elif len(hex_val) == 8:  # #RRGGBBAA
            try:
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
                a = int(hex_val[6:8], 16) / 255.0
                return RGBAColor(r, g, b, a, raw=color_str), "hex_alpha"
            except ValueError:
                return None, "invalid_hex"
        return None, "invalid_hex_length"

    # Named Colors
    if raw_clean in NAMED_COLORS:
        r, g, b = NAMED_COLORS[raw_clean]
        return RGBAColor(r, g, b, 1.0, raw=color_str), "named"

    # rgb(...) and rgba(...)
    rgb_match = re.match(r"^rgba?\s*\((.+)\)$", raw_clean)
    if rgb_match:
        content = rgb_match.group(1).strip()
        # Handle slash syntax: rgb(255 255 255 / 0.5)
        if "/" in content:
            rgb_part, a_part = content.split("/", 1)
            parts = [p for p in re.split(r"[\s,]+", rgb_part.strip()) if p]
            parts.append(a_part.strip())
        else:
            parts = [p for p in re.split(r"[\s,]+", content) if p]

        if len(parts) in (3, 4):
            try:
                # Helper for channel
                def parse_channel(val_str: str) -> int:
                    val_str = val_str.strip()
                    if val_str.endswith("%"):
                        pct = float(val_str[:-1])
                        return int(round(pct * 2.55))
                    return int(round(float(val_str)))

                r = parse_channel(parts[0])
                g = parse_channel(parts[1])
                b = parse_channel(parts[2])

                a = 1.0
                if len(parts) == 4:
                    a_str = parts[3].strip()
                    if a_str.endswith("%"):
                        a = float(a_str[:-1]) / 100.0
                    else:
                        a = float(a_str)

                return RGBAColor(r, g, b, a, raw=color_str), "rgb"
            except Exception:
                return None, "invalid_rgb_syntax"

    # hsl(...) and hsla(...)
    hsl_match = re.match(r"^hsla?\s*\((.+)\)$", raw_clean)
    if hsl_match:
        content = hsl_match.group(1).strip()
        if "/" in content:
            hsl_part, a_part = content.split("/", 1)
            parts = [p for p in re.split(r"[\s,]+", hsl_part.strip()) if p]
            parts.append(a_part.strip())
        else:
            parts = [p for p in re.split(r"[\s,]+", content) if p]

        if len(parts) in (3, 4):
            try:
                # Hue
                h_str = parts[0].strip()
                if h_str.endswith("deg"):
                    h = float(h_str[:-3])
                elif h_str.endswith("rad"):
                    h = math.degrees(float(h_str[:-3]))
                elif h_str.endswith("turn"):
                    h = float(h_str[:-4]) * 360.0
                elif h_str.endswith("grad"):
                    h = float(h_str[:-4]) * 0.9
                else:
                    h = float(h_str)

                # Saturation
                s_str = parts[1].strip()
                s = float(s_str[:-1]) if s_str.endswith("%") else float(s_str)

                # Lightness
                l_str = parts[2].strip()
                l = float(l_str[:-1]) if l_str.endswith("%") else float(l_str)

                a = 1.0
                if len(parts) == 4:
                    a_str = parts[3].strip()
                    if a_str.endswith("%"):
                        a = float(a_str[:-1]) / 100.0
                    else:
                        a = float(a_str)

                return RGBAColor.from_hsl(h, s, l, a, raw=color_str), "hsl"
            except Exception:
                return None, "invalid_hsl_syntax"

    return None, "unrecognized_color_format"
