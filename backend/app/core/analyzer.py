"""
ContrastCraft — Main Accessibility Audit & Analysis Engine
Orchestrates HTML and CSS parsing, cascade resolution, color compositing,
WCAG classification, interaction states, responsive media checks, and design token audits.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Any, Set
from .colors import RGBAColor, parse_color, composite_colors
from .contrast import calculate_contrast_ratio, format_ratio
from .classifier import classify_contrast, is_large_text_evaluation, ClassificationResult
from .html_parser import parse_html_document, DOMNode
from .css_parser import CSSStylesheet, CascadeResolver
from .recommender import find_hue_preserving_color
from .html_a11y import HTMLA11yAuditor
from .token_matrix import TokenIntelligenceEngine


@dataclass
class FindingItem:
    id: str
    element_tag: str
    selector: str
    line_number: int
    element_role: str
    text_sample: str
    foreground_raw: str
    background_raw: str
    effective_fg: str
    effective_bg: str
    contrast_ratio: float
    formatted_ratio: str
    target_threshold: float
    criterion_name: str
    criterion_id: str
    is_large_text: bool
    status: str
    pass_aa: bool
    pass_aaa: bool
    confidence: str  # verified, potential, needs_browser_verification
    severity: str    # critical, high, medium, low, info
    explanation: str
    state: str       # normal, hover, focus, active, disabled, media_dark
    suggested_fix: Optional[Dict[str, Any]] = None


@dataclass
class TokenInventoryItem:
    name: str
    value: str
    hex_color: Optional[str]
    usage_count: int
    associated_findings_count: int
    failing_usages: int
    suggested_value: Optional[str] = None


@dataclass
class AuditSummary:
    total_analyzed: int
    pass_aa_count: int
    fail_aa_count: int
    pass_aaa_count: int
    fail_aaa_count: int
    non_text_pass_count: int
    non_text_fail_count: int
    needs_verification_count: int
    compliance_score: float  # 0 to 100%
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


def parse_px_dimension(val: Optional[str]) -> Optional[float]:
    """Parses CSS dimension like '16px', '1.5rem', '18pt' to approximate pixels."""
    if not val:
        return None
    val_clean = val.strip().lower()
    m = re.match(r"^([\d.]+)\s*(px|pt|rem|em|%)?$", val_clean)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2) or "px"

    if unit == "px":
        return num
    elif unit == "pt":
        return num * 1.333  # 1pt ~ 1.333px
    elif unit in ("rem", "em"):
        return num * 16.0   # assume default 16px base font
    elif unit == "%":
        return (num / 100.0) * 16.0
    return num


class AuditEngine:
    def __init__(self):
        self.findings: List[FindingItem] = []
        self.token_inventory: Dict[str, TokenInventoryItem] = {}

    def analyze(
        self,
        html_content: str,
        custom_css: str = "",
        external_stylesheets: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes full contrast and UI accessibility audit across HTML and CSS.
        """
        self.findings.clear()
        self.token_inventory.clear()

        # 1. Parse HTML DOM tree
        root, style_blocks, linked_sheets = parse_html_document(html_content)

        # 2. Parse CSS stylesheets
        stylesheets: List[CSSStylesheet] = []

        # Parse inline <style> blocks
        for block_css, line_num in style_blocks:
            sheet = CSSStylesheet(source_file=f"inline:<style line {line_num}>")
            sheet.parse(block_css, base_line=line_num)
            stylesheets.append(sheet)

        # Parse custom CSS provided
        if custom_css.strip():
            sheet = CSSStylesheet(source_file="styles.css")
            sheet.parse(custom_css, base_line=1)
            stylesheets.append(sheet)

        # Parse external stylesheets safely if provided
        if external_stylesheets:
            for href, content in external_stylesheets.items():
                sheet = CSSStylesheet(source_file=href)
                sheet.parse(content, base_line=1)
                stylesheets.append(sheet)

        # 3. Create Cascade Resolver
        resolver = CascadeResolver(stylesheets)

        # 4. Inventory CSS variables (Design Tokens)
        self._build_token_inventory(resolver.variables, stylesheets, html_content)

        # 5. Default document background (assume #FFFFFF if not declared on html or body)
        doc_bg_str = "#FFFFFF"
        html_node = next((n for n in root.children if n.tag in ("html", "body")), None)
        if html_node:
            _, bg_cand, _, _ = resolver.get_effective_colors(html_node)
            if bg_cand:
                doc_bg_str = bg_cand

        default_bg_color, _ = parse_color(doc_bg_str, resolver.variables)
        if not default_bg_color:
            default_bg_color = RGBAColor(255, 255, 255)

        # 6. Walk DOM nodes and audit text, controls, borders, states
        nodes = root.walk()
        finding_id_seq = 1

        for node in nodes:
            if node.tag in ("[root]", "head", "meta", "title", "script", "style", "link"):
                continue

            # A. Normal Base State Analysis
            finding_id_seq = self._audit_node(
                node=node,
                resolver=resolver,
                default_bg=default_bg_color,
                state="normal",
                finding_id_seq=finding_id_seq
            )

            # B. Interaction States (:hover, :focus, :active, :disabled) for interactive elements
            if node.role in ("button", "link", "input") or node.classes or node.id:
                for pseudo in ("hover", "focus", "active", "disabled"):
                    finding_id_seq = self._audit_node(
                        node=node,
                        resolver=resolver,
                        default_bg=default_bg_color,
                        state=pseudo,
                        finding_id_seq=finding_id_seq
                    )

        # 7. Deduplicate findings
        deduped = self._deduplicate_findings(self.findings)

        # 8. Calculate token usage correlations
        self._link_tokens_to_findings(deduped)

        # 9. Compute summary metrics
        summary = self._compute_summary(deduped)

        # 10. Extended HTML Accessibility Audit (Separate category)
        html_auditor = HTMLA11yAuditor()
        html_findings = html_auditor.audit(html_content, custom_css=custom_css)

        # 11. Token Compatibility Matrix
        token_engine = TokenIntelligenceEngine()
        token_matrix_data = token_engine.build_matrix([asdict(t) for t in self.token_inventory.values()])

        return {
            "summary": asdict(summary),
            "findings": [asdict(f) for f in deduped],
            "tokens": [asdict(t) for t in self.token_inventory.values()],
            "unresolved_elements_count": summary.needs_verification_count,
            "html_a11y_findings": [asdict(hf) for hf in html_findings],
            "token_matrix": token_matrix_data
        }

    def _audit_node(
        self,
        node: DOMNode,
        resolver: CascadeResolver,
        default_bg: RGBAColor,
        state: str,
        finding_id_seq: int
    ) -> int:
        pseudo = None if state in ("normal", "media_dark") else state
        media_active = (state == "media_dark")

        # Resolve styles
        styles = resolver.resolve_node_styles(node, pseudo_class=pseudo, media_active=media_active)
        raw_fg, raw_bg, raw_border, raw_outline = resolver.get_effective_colors(node, pseudo_class=pseudo)

        # Font metrics
        font_size_px = parse_px_dimension(styles.get("font-size"))
        font_weight = styles.get("font-weight")
        is_large = is_large_text_evaluation(font_size_px, font_weight)

        # 1. Audit Text Content if element has text
        has_text = bool(node.text_content.strip())
        if has_text or node.role in ("heading", "link", "button"):
            finding_id_seq = self._evaluate_combination(
                node=node,
                fg_raw=raw_fg or styles.get("color") or "#000000",
                bg_raw=raw_bg or default_bg.to_hex(),
                default_bg=default_bg,
                element_role="heading" if node.role == "heading" or is_large else (node.role if node.role in ("button", "link") else "text"),
                font_size_px=font_size_px,
                font_weight=font_weight,
                state=state,
                resolver=resolver,
                finding_id_seq=finding_id_seq
            )

        # 2. Audit UI Component Boundaries (Buttons, Inputs, Outlines)
        if node.role in ("button", "input"):
            # Control border vs background
            border_val = raw_border or styles.get("border") or styles.get("border-color")
            if border_val and "none" not in border_val.lower() and "0px" not in border_val:
                finding_id_seq = self._evaluate_combination(
                    node=node,
                    fg_raw=border_val,
                    bg_raw=raw_bg or default_bg.to_hex(),
                    default_bg=default_bg,
                    element_role="ui_component_boundary",
                    font_size_px=None,
                    font_weight=None,
                    state=state,
                    resolver=resolver,
                    finding_id_seq=finding_id_seq
                )

        return finding_id_seq

    def _evaluate_combination(
        self,
        node: DOMNode,
        fg_raw: str,
        bg_raw: str,
        default_bg: RGBAColor,
        element_role: str,
        font_size_px: Optional[float],
        font_weight: Optional[str],
        state: str,
        resolver: CascadeResolver,
        finding_id_seq: int
    ) -> int:
        fg_color, fg_status = parse_color(fg_raw, resolver.variables)
        bg_color, bg_status = parse_color(bg_raw, resolver.variables)

        # Determine confidence
        confidence = "verified"
        if fg_status in ("background_image_requires_browser", "gradient_requires_browser") or \
           bg_status in ("background_image_requires_browser", "gradient_requires_browser"):
            confidence = "needs_browser_verification"
        elif "unresolved_css_variable" in (fg_status or "") or "unresolved_css_variable" in (bg_status or ""):
            confidence = "needs_browser_verification"
        elif not fg_color or not bg_color:
            confidence = "needs_browser_verification"
        elif fg_color.is_semi_transparent or bg_color.is_semi_transparent:
            confidence = "potential"

        # If background is missing or transparent, composite over default document background
        eff_bg_color = bg_color if bg_color and not bg_color.is_transparent else default_bg

        if confidence == "needs_browser_verification" or not fg_color or not eff_bg_color:
            # Report unresolved / needs verification finding honestly
            self.findings.append(FindingItem(
                id=f"cc-item-{finding_id_seq}",
                element_tag=node.tag,
                selector=node.get_selector(),
                line_number=node.line,
                element_role=element_role,
                text_sample=node.text_content[:60] if node.text_content else f"<{node.tag}>",
                foreground_raw=fg_raw,
                background_raw=bg_raw,
                effective_fg=fg_color.to_hex() if fg_color else fg_raw,
                effective_bg=eff_bg_color.to_hex() if eff_bg_color else bg_raw,
                contrast_ratio=0.0,
                formatted_ratio="N/A",
                target_threshold=4.5 if element_role == "text" else 3.0,
                criterion_name="WCAG 2.1 Contrast (Unresolved Background)",
                criterion_id="unresolved",
                is_large_text=is_large_text_evaluation(font_size_px, font_weight),
                status="unresolved",
                pass_aa=False,
                pass_aaa=False,
                confidence="needs_browser_verification",
                severity="low",
                explanation=f"Cannot compute static contrast accurately: {fg_status or bg_status}. Browser rendering required.",
                state=state,
                suggested_fix=None
            ))
            return finding_id_seq + 1

        # Calculate contrast ratio
        ratio, eff_fg, eff_bg = calculate_contrast_ratio(fg_color, eff_bg_color)
        classification = classify_contrast(
            ratio=ratio,
            element_role=element_role,
            font_size_px=font_size_px,
            font_weight=font_weight,
            confidence=confidence
        )

        # Generate recommendation if failed
        suggested_fix = None
        if not classification.pass_aa or (classification.pass_non_text is False):
            fix = find_hue_preserving_color(eff_fg, eff_bg, classification.recommendation_target)
            if fix:
                suggested_fix = {
                    "suggested_hex": fix.hex_color,
                    "suggested_rgb": fix.rgb_str,
                    "target_ratio": fix.target_threshold,
                    "projected_ratio": fix.contrast_ratio,
                    "formatted_projected_ratio": fix.formatted_ratio,
                    "description": fix.description
                }

        self.findings.append(FindingItem(
            id=f"cc-item-{finding_id_seq}",
            element_tag=node.tag,
            selector=node.get_selector(),
            line_number=node.line,
            element_role=element_role,
            text_sample=node.text_content[:60] if node.text_content else f"<{node.tag}>",
            foreground_raw=fg_raw,
            background_raw=bg_raw,
            effective_fg=eff_fg.to_hex(),
            effective_bg=eff_bg.to_hex(),
            contrast_ratio=ratio,
            formatted_ratio=classification.formatted_ratio,
            target_threshold=classification.target_threshold,
            criterion_name=classification.criterion_name,
            criterion_id=classification.criterion_id,
            is_large_text=classification.is_large_text,
            status=classification.status,
            pass_aa=classification.pass_aa,
            pass_aaa=classification.pass_aaa,
            confidence=confidence,
            severity=classification.severity,
            explanation=classification.explanation,
            state=state,
            suggested_fix=suggested_fix
        ))

        return finding_id_seq + 1

    def _build_token_inventory(
        self,
        variables: Dict[str, str],
        stylesheets: List[CSSStylesheet],
        html_content: str
    ):
        combined_text = html_content + "\n" + "\n".join(
            "\n".join(r.selector + " " + str(r.declarations) for r in s.rules) for s in stylesheets
        )

        for var_name, var_val in variables.items():
            parsed_c, _ = parse_color(var_val, variables)
            # Count references: var(--name)
            usage_count = len(re.findall(re.escape(var_name), combined_text))
            self.token_inventory[var_name] = TokenInventoryItem(
                name=var_name,
                value=var_val,
                hex_color=parsed_c.to_hex() if parsed_c else None,
                usage_count=usage_count,
                associated_findings_count=0,
                failing_usages=0,
                suggested_value=None
            )

    def _link_tokens_to_findings(self, findings: List[FindingItem]):
        for f in findings:
            for token_name, token_item in self.token_inventory.items():
                if token_name in f.foreground_raw or token_name in f.background_raw:
                    token_item.associated_findings_count += 1
                    if not f.pass_aa or f.status in ("fail_aa", "fail_non_text"):
                        token_item.failing_usages += 1
                        if f.suggested_fix and not token_item.suggested_value:
                            token_item.suggested_value = f.suggested_fix["suggested_hex"]

    def _deduplicate_findings(self, findings: List[FindingItem]) -> List[FindingItem]:
        seen = set()
        deduped = []
        for f in findings:
            key = (f.selector, f.element_role, f.state, f.effective_fg, f.effective_bg)
            if key not in seen:
                seen.add(key)
                deduped.append(f)
        return deduped

    def _compute_summary(self, findings: List[FindingItem]) -> AuditSummary:
        total = len(findings)
        if total == 0:
            return AuditSummary(0, 0, 0, 0, 0, 0, 0, 0, 100.0, 0, 0, 0, 0)

        pass_aa = sum(1 for f in findings if f.pass_aa and f.confidence != "needs_browser_verification")
        fail_aa = sum(1 for f in findings if not f.pass_aa and f.confidence != "needs_browser_verification")
        pass_aaa = sum(1 for f in findings if f.pass_aaa and f.confidence != "needs_browser_verification")
        fail_aaa = sum(1 for f in findings if not f.pass_aaa and f.confidence != "needs_browser_verification")

        non_text_pass = sum(1 for f in findings if f.element_role in ("button_border", "input_border", "ui_component_boundary") and f.pass_aa)
        non_text_fail = sum(1 for f in findings if f.element_role in ("button_border", "input_border", "ui_component_boundary") and not f.pass_aa)

        unresolved = sum(1 for f in findings if f.confidence == "needs_browser_verification")

        critical = sum(1 for f in findings if f.severity == "critical")
        high = sum(1 for f in findings if f.severity == "high")
        medium = sum(1 for f in findings if f.severity == "medium")
        low = sum(1 for f in findings if f.severity == "low")

        evaluable = total - unresolved
        score = (pass_aa / evaluable * 100.0) if evaluable > 0 else 100.0

        return AuditSummary(
            total_analyzed=total,
            pass_aa_count=pass_aa,
            fail_aa_count=fail_aa,
            pass_aaa_count=pass_aaa,
            fail_aaa_count=fail_aaa,
            non_text_pass_count=non_text_pass,
            non_text_fail_count=non_text_fail,
            needs_verification_count=unresolved,
            compliance_score=round(score, 1),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low
        )
