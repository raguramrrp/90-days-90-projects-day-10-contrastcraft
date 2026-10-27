"""
ContrastCraft — Design Token Intelligence & Compatibility Matrix
Analyzes CSS custom properties, detects duplicate color values, computes pairwise
foreground/background contrast ratios, and evaluates token remediation impact.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
from .colors import RGBAColor, parse_color
from .contrast import calculate_contrast_ratio, calculate_apca, format_ratio
from .classifier import classify_contrast


@dataclass
class TokenMatrixCell:
    fg_token: str
    bg_token: str
    fg_hex: str
    bg_hex: str
    contrast_ratio: float
    formatted_ratio: str
    apca_lc: float
    pass_normal_aa: bool
    pass_large_aa: bool
    pass_aaa: bool
    pass_ui: bool
    status: str  # pass_aaa, pass_aa, pass_large_only, fail


@dataclass
class TokenDuplicateGroup:
    hex_color: str
    token_names: List[str]
    count: int


@dataclass
class TokenImpactSummary:
    token_name: str
    current_value: str
    proposed_value: str
    affected_selectors: List[str]
    failing_usages_resolved: int
    net_contrast_gain: float


class TokenIntelligenceEngine:
    def __init__(self):
        pass

    def build_matrix(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds pairwise compatibility matrix for all detected color tokens.
        """
        color_tokens: List[Tuple[str, str, RGBAColor]] = []

        for t in tokens:
            name = t.get("name", "")
            val = t.get("value", "")
            rgba, _ = parse_color(val)
            if rgba:
                hex_val = rgba.to_hex()
                color_tokens.append((name, hex_val, rgba))

        # 1. Pairwise Matrix
        matrix_cells: List[Dict[str, Any]] = []
        token_names = [name for name, _, _ in color_tokens]

        for fg_name, fg_hex, fg_rgba in color_tokens:
            for bg_name, bg_hex, bg_rgba in color_tokens:
                if fg_name == bg_name:
                    continue

                cr, _, _ = calculate_contrast_ratio(fg_rgba, bg_rgba)
                apca = calculate_apca(fg_rgba, bg_rgba)

                res = classify_contrast(
                    ratio=cr,
                    element_role="text",
                    font_size_px=16.0,
                    font_weight="normal"
                )

                matrix_cells.append(asdict(TokenMatrixCell(
                    fg_token=fg_name,
                    bg_token=bg_name,
                    fg_hex=fg_hex,
                    bg_hex=bg_hex,
                    contrast_ratio=round(cr, 2),
                    formatted_ratio=format_ratio(cr),
                    apca_lc=apca,
                    pass_normal_aa=res.pass_aa,
                    pass_large_aa=cr >= 3.0,
                    pass_aaa=res.pass_aaa,
                    pass_ui=cr >= 3.0,
                    status=res.status
                )))

        # 2. Duplicate Detection
        color_groups: Dict[str, List[str]] = {}
        for name, hex_val, _ in color_tokens:
            color_groups.setdefault(hex_val.upper(), []).append(name)

        duplicates: List[Dict[str, Any]] = []
        for hex_code, names in color_groups.items():
            if len(names) > 1:
                duplicates.append(asdict(TokenDuplicateGroup(
                    hex_color=hex_code,
                    token_names=names,
                    count=len(names)
                )))

        return {
            "token_count": len(color_tokens),
            "tokens": [
                {"name": name, "hex": hex_val}
                for name, hex_val, _ in color_tokens
            ],
            "matrix_cells": matrix_cells,
            "duplicates": duplicates
        }

    def evaluate_token_impact(
        self,
        token_name: str,
        proposed_value: str,
        findings: List[Dict[str, Any]],
        tokens: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates what happens across all known uses when a token value is updated.
        """
        curr_token = next((t for t in tokens if t.get("name") == token_name), None)
        curr_val = curr_token.get("value", "") if curr_token else "unknown"

        affected_selectors: List[str] = []
        failing_usages_resolved = 0
        contrast_deltas = []

        prop_rgba, _ = parse_color(proposed_value)

        for f in findings:
            raw_fg = f.get("foreground_raw", "")
            raw_bg = f.get("background_raw", "")

            # Check if this finding utilizes the token
            if token_name in raw_fg or token_name in raw_bg:
                sel = f.get("selector", f.get("element_tag", ""))
                if sel not in affected_selectors:
                    affected_selectors.append(sel)

                # If it currently fails AA, check if new value resolves it
                if not f.get("pass_aa") and prop_rgba:
                    bg_color, _ = parse_color(f.get("effective_bg", "#FFFFFF"))
                    if bg_color:
                        new_ratio, _, _ = calculate_contrast_ratio(prop_rgba, bg_color)
                        if new_ratio >= f.get("target_threshold", 4.5):
                            failing_usages_resolved += 1
                        contrast_deltas.append(new_ratio - f.get("contrast_ratio", 1.0))

        net_gain = round(sum(contrast_deltas) / len(contrast_deltas), 2) if contrast_deltas else 0.0

        return asdict(TokenImpactSummary(
            token_name=token_name,
            current_value=curr_val,
            proposed_value=proposed_value,
            affected_selectors=affected_selectors,
            failing_usages_resolved=failing_usages_resolved,
            net_contrast_gain=net_gain
        ))
