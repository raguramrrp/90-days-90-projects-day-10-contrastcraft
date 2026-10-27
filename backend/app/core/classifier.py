"""
ContrastCraft — WCAG 2.1 / 2.2 Classification Engine
Evaluates contrast ratios against official WCAG Success Criteria:
- 1.4.3 Contrast (Minimum) (Level AA) - Normal text 4.5:1, Large text 3.0:1
- 1.4.6 Contrast (Enhanced) (Level AAA) - Normal text 7.0:1, Large text 4.5:1
- 1.4.11 Non-text Contrast (Level AA) - UI components and graphical objects 3.0:1
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ClassificationResult:
    ratio: float
    formatted_ratio: str
    target_threshold: float
    criterion_name: str
    criterion_id: str
    is_large_text: bool
    element_role: str  # text, heading, link, button, input_border, focus_ring, icon, token
    pass_aa: bool
    pass_aaa: bool
    pass_non_text: Optional[bool]
    status: str  # pass, fail_aa, fail_aaa, fail_non_text, unresolved
    confidence: str  # verified, potential, needs_browser_verification
    severity: str  # critical, high, medium, low, info
    explanation: str
    recommendation_target: float


def is_large_text_evaluation(font_size_px: Optional[float], font_weight: Optional[str]) -> bool:
    """
    WCAG defines large scale text as:
    - At least 18pt (24px) regular font weight.
    - At least 14pt (18.66px / ~19px) bold font weight (weight >= 700 or 'bold').
    """
    if font_size_px is None:
        return False

    is_bold = False
    if font_weight:
        fw_clean = str(font_weight).strip().lower()
        if fw_clean in ("bold", "bolder", "700", "800", "900"):
            is_bold = True
        else:
            try:
                num = int(fw_clean)
                if num >= 700:
                    is_bold = True
            except ValueError:
                pass

    if is_bold:
        return font_size_px >= 18.66
    else:
        return font_size_px >= 24.0


def classify_contrast(
    ratio: float,
    element_role: str = "text",
    font_size_px: Optional[float] = None,
    font_weight: Optional[str] = None,
    confidence: str = "verified"
) -> ClassificationResult:
    """
    Classify a calculated contrast ratio against applicable WCAG criteria.
    Internal calculation uses exact float, never rounded prematurely.
    """
    formatted_ratio = f"{ratio:.2f}:1"
    is_large = is_large_text_evaluation(font_size_px, font_weight)
    
    # Non-text UI components: buttons, input borders, focus indicators, icons
    if element_role in ("button_border", "input_border", "ui_component_boundary", "focus_indicator", "icon"):
        target_threshold = 3.0
        pass_non_text = ratio >= 3.0
        pass_aa = pass_non_text  # SC 1.4.11 is Level AA
        pass_aaa = ratio >= 4.5  # High standard advisory
        criterion_name = "WCAG 2.1 SC 1.4.11 Non-text Contrast (Level AA)"
        criterion_id = "1.4.11"
        recommendation_target = 3.0

        if pass_non_text:
            status = "pass"
            severity = "info"
            explanation = f"Meets non-text contrast requirement of at least 3.0:1 ({formatted_ratio})."
        else:
            status = "fail_non_text"
            severity = "high" if ratio < 2.0 else "medium"
            explanation = (
                f"Fails non-text contrast criterion (1.4.11). User interface component boundaries and graphical "
                f"objects require at least 3.0:1; got {formatted_ratio}."
            )

        return ClassificationResult(
            ratio=ratio,
            formatted_ratio=formatted_ratio,
            target_threshold=target_threshold,
            criterion_name=criterion_name,
            criterion_id=criterion_id,
            is_large_text=is_large,
            element_role=element_role,
            pass_aa=pass_aa,
            pass_aaa=pass_aaa,
            pass_non_text=pass_non_text,
            status=status,
            confidence=confidence,
            severity=severity,
            explanation=explanation,
            recommendation_target=recommendation_target
        )

    # Text elements (normal text, large text, headings, links, button text)
    if is_large:
        target_aa = 3.0
        target_aaa = 4.5
        criterion_name = "WCAG 2.1/2.2 SC 1.4.3 & 1.4.6 Contrast (Large Text)"
        criterion_id = "1.4.3-large"
        recommendation_target = 3.0
    else:
        target_aa = 4.5
        target_aaa = 7.0
        criterion_name = "WCAG 2.1/2.2 SC 1.4.3 & 1.4.6 Contrast (Normal Text)"
        criterion_id = "1.4.3-normal"
        recommendation_target = 4.5

    pass_aa = ratio >= target_aa
    pass_aaa = ratio >= target_aaa

    if pass_aaa:
        status = "pass"
        severity = "info"
        explanation = f"Passes both WCAG Level AA ({target_aa}:1) and Level AAA ({target_aaa}:1) with {formatted_ratio}."
    elif pass_aa:
        status = "pass_aa_only"
        severity = "low"
        explanation = (
            f"Passes WCAG Level AA ({target_aa}:1) with {formatted_ratio}, "
            f"but does not achieve Level AAA ({target_aaa}:1)."
        )
    else:
        status = "fail_aa"
        if ratio < 2.5:
            severity = "critical"
        else:
            severity = "high"
        explanation = (
            f"Fails WCAG Level AA minimum contrast. Requires at least {target_aa}:1 for "
            f"{'large' if is_large else 'normal'} text; got {formatted_ratio}."
        )

    return ClassificationResult(
        ratio=ratio,
        formatted_ratio=formatted_ratio,
        target_threshold=target_aa,
        criterion_name=criterion_name,
        criterion_id=criterion_id,
        is_large_text=is_large,
        element_role=element_role,
        pass_aa=pass_aa,
        pass_aaa=pass_aaa,
        pass_non_text=None,
        status=status,
        confidence=confidence,
        severity=severity,
        explanation=explanation,
        recommendation_target=recommendation_target
    )
