"""
ContrastCraft — Extended HTML Accessibility Analysis Module
Performs deterministic static analysis of structural HTML accessibility issues
complementary to color contrast evaluations (WCAG 2.1 / 2.2 Level A and AA).
"""

from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from .html_parser import parse_html_document, DOMNode


@dataclass
class HTMLA11yFinding:
    id: str
    rule_id: str
    wcag_sc: str
    element_tag: str
    selector: str
    line_number: int
    severity: str  # critical, high, medium, low, info
    description: str
    recommendation: str
    verification_type: str  # static_verified, needs_manual_review
    code_snippet: str = ""


class HTMLA11yAuditor:
    """
    Evaluates key structural HTML accessibility requirements according to WCAG 2.1/2.2:
    1. Images missing alt attributes (SC 1.1.1 Non-text Content)
    2. Form controls without associated labels (SC 1.3.1 Info and Relationships, 4.1.2)
    3. Empty or uninformative link text (SC 2.4.4 Link Purpose)
    4. Missing document language attribute (SC 3.1.1 Language of Page)
    5. Heading hierarchy skips and missing main heading (SC 1.3.1, 2.4.6)
    6. Buttons missing accessible names (SC 4.1.2 Name, Role, Value)
    7. Potential focus suppression in CSS (SC 2.4.7 Focus Visible)
    """

    GENERIC_LINK_TEXTS = {
        "click here", "here", "read more", "more", "learn more", "link",
        "details", "view more", "go", "continue", "info"
    }

    def audit(self, html_content: str, custom_css: str = "") -> List[HTMLA11yFinding]:
        findings: List[HTMLA11yFinding] = []
        if not html_content.strip():
            return findings

        root, _, _ = parse_html_document(html_content)
        nodes = root.walk()

        # 1. Document Language Check (SC 3.1.1)
        self._check_document_language(nodes, findings)

        # 2. Heading Hierarchy Check (SC 1.3.1, 2.4.6)
        self._check_heading_hierarchy(nodes, findings)

        # 3. Walk all individual DOM nodes
        label_for_map = self._collect_label_associations(nodes)

        for node in nodes:
            if node.tag == "img":
                self._check_image_alt(node, findings)
            elif node.tag in ("input", "select", "textarea"):
                self._check_form_label(node, label_for_map, findings)
            elif node.tag == "a":
                self._check_link_text(node, findings)
            elif node.tag == "button":
                self._check_button_accessible_name(node, findings)

        # 4. Check CSS focus outline suppression
        if custom_css:
            self._check_css_focus_suppression(custom_css, findings)

        return findings

    def _check_document_language(self, nodes: List[DOMNode], findings: List[HTMLA11yFinding]):
        html_node = next((n for n in nodes if n.tag == "html"), None)
        if html_node:
            lang = html_node.attrs.get("lang", "").strip()
            if not lang:
                findings.append(HTMLA11yFinding(
                    id=f"a11y-lang-{len(findings) + 1}",
                    rule_id="html-missing-lang",
                    wcag_sc="3.1.1 Language of Page (Level A)",
                    element_tag="html",
                    selector="html",
                    line_number=html_node.line,
                    severity="high",
                    description="The <html> root element is missing a valid 'lang' attribute.",
                    recommendation="Add a standard BCP 47 language code to the root element, e.g. <html lang=\"en\">.",
                    verification_type="static_verified",
                    code_snippet='<html>'
                ))
        else:
            # Document fragment without html root
            pass

    def _check_heading_hierarchy(self, nodes: List[DOMNode], findings: List[HTMLA11yFinding]):
        headings = [n for n in nodes if re.match(r"^h[1-6]$", n.tag)]
        if not headings:
            return

        has_h1 = any(n.tag == "h1" for n in headings)
        if not has_h1:
            findings.append(HTMLA11yFinding(
                id=f"a11y-heading-noh1-{len(findings) + 1}",
                rule_id="heading-missing-h1",
                wcag_sc="1.3.1 Info and Relationships (Level A)",
                element_tag="heading",
                selector=headings[0].tag,
                line_number=headings[0].line,
                severity="medium",
                description="The page contains headings but lacks a primary Level 1 Heading (<h1>).",
                recommendation="Provide an <h1> element representing the main topic or purpose of the page.",
                verification_type="static_verified",
                code_snippet=f"<{headings[0].tag}>{headings[0].text_content[:30]}</{headings[0].tag}>"
            ))

        # Check for skipped heading levels (e.g. h1 -> h3)
        last_level = 0
        for h in headings:
            level = int(h.tag[1])
            if last_level > 0 and level > last_level + 1:
                findings.append(HTMLA11yFinding(
                    id=f"a11y-heading-skip-{len(findings) + 1}",
                    rule_id="heading-skipped-level",
                    wcag_sc="1.3.1 Info and Relationships (Level A)",
                    element_tag=h.tag,
                    selector=self._build_selector(h),
                    line_number=h.line,
                    severity="low",
                    description=f"Heading level was skipped from <h{last_level}> directly to <h{level}>.",
                    recommendation=f"Structure heading levels sequentially without skipping (use <h{last_level + 1}> before <h{level}>).",
                    verification_type="static_verified",
                    code_snippet=f"<{h.tag}>{h.text_content[:30]}</{h.tag}>"
                ))
            last_level = level

    def _check_image_alt(self, node: DOMNode, findings: List[HTMLA11yFinding]):
        if "alt" not in node.attrs:
            findings.append(HTMLA11yFinding(
                id=f"a11y-img-alt-{len(findings) + 1}",
                rule_id="img-missing-alt",
                wcag_sc="1.1.1 Non-text Content (Level A)",
                element_tag="img",
                selector=self._build_selector(node),
                line_number=node.line,
                severity="critical",
                description="Image element is missing an 'alt' text attribute entirely.",
                recommendation="Add an informative alt attribute describing the image, or alt=\"\" if decorative.",
                verification_type="static_verified",
                code_snippet=f'<img src="{node.attrs.get("src", "")}">'
            ))
        else:
            alt_val = node.attrs["alt"].strip().lower()
            if alt_val in ("image", "photo", "picture", "graphic", "logo", "icon"):
                findings.append(HTMLA11yFinding(
                    id=f"a11y-img-redundant-{len(findings) + 1}",
                    rule_id="img-redundant-alt",
                    wcag_sc="1.1.1 Non-text Content (Level A)",
                    element_tag="img",
                    selector=self._build_selector(node),
                    line_number=node.line,
                    severity="medium",
                    description=f"Image alt text '{alt_val}' is redundant or uninformative.",
                    recommendation="Describe the actual subject or function of the image rather than generic words like 'image' or 'photo'.",
                    verification_type="needs_manual_review",
                    code_snippet=f'<img alt="{alt_val}">'
                ))

    def _collect_label_associations(self, nodes: List[DOMNode]) -> Dict[str, str]:
        label_for_map = {}
        for n in nodes:
            if n.tag == "label":
                target_id = n.attrs.get("for")
                if target_id:
                    label_for_map[target_id.strip()] = n.text_content.strip()
        return label_for_map

    def _check_form_label(self, node: DOMNode, label_for_map: Dict[str, str], findings: List[HTMLA11yFinding]):
        input_type = node.attrs.get("type", "text").strip().lower()
        if input_type in ("hidden", "submit", "button", "reset", "image"):
            return

        element_id = node.attrs.get("id", "").strip()
        has_aria_label = bool(node.attrs.get("aria-label", "").strip())
        has_aria_labelledby = bool(node.attrs.get("aria-labelledby", "").strip())
        has_associated_label = bool(element_id and element_id in label_for_map)

        # Check if wrapped in a <label>
        curr = node.parent
        wrapped_in_label = False
        while curr:
            if curr.tag == "label":
                wrapped_in_label = True
                break
            curr = curr.parent

        if not (has_associated_label or wrapped_in_label or has_aria_label or has_aria_labelledby):
            name_attr = node.attrs.get("name", "")
            findings.append(HTMLA11yFinding(
                id=f"a11y-input-label-{len(findings) + 1}",
                rule_id="input-missing-label",
                wcag_sc="1.3.1 Info and Relationships (Level A), 4.1.2 (Level A)",
                element_tag=node.tag,
                selector=self._build_selector(node),
                line_number=node.line,
                severity="critical",
                description=f"Form control <{node.tag} type=\"{input_type}\"> has no accessible label or name.",
                recommendation="Associate an explicit <label for=\"id\"> element, wrap inside <label>, or provide aria-label.",
                verification_type="static_verified",
                code_snippet=f'<{node.tag} type="{input_type}" name="{name_attr}">'
            ))

    def _check_link_text(self, node: DOMNode, findings: List[HTMLA11yFinding]):
        text = node.text_content.strip()
        aria_label = node.attrs.get("aria-label", "").strip()
        title = node.attrs.get("title", "").strip()

        # Check for child images with alt text
        has_img_alt = False
        for c in node.children:
            if c.tag == "img" and c.attrs.get("alt", "").strip():
                has_img_alt = True
                break

        if not text and not aria_label and not title and not has_img_alt:
            href = node.attrs.get("href", "#")
            findings.append(HTMLA11yFinding(
                id=f"a11y-link-empty-{len(findings) + 1}",
                rule_id="link-empty-content",
                wcag_sc="2.4.4 Link Purpose (In Context) (Level A)",
                element_tag="a",
                selector=self._build_selector(node),
                line_number=node.line,
                severity="critical",
                description="Link element <a> contains no readable text, aria-label, or image with alt text.",
                recommendation="Provide meaningful descriptive text inside the link or an aria-label explaining the link destination.",
                verification_type="static_verified",
                code_snippet=f'<a href="{href}"></a>'
            ))
        elif text.lower() in self.GENERIC_LINK_TEXTS and not aria_label:
            findings.append(HTMLA11yFinding(
                id=f"a11y-link-generic-{len(findings) + 1}",
                rule_id="link-uninformative-text",
                wcag_sc="2.4.4 Link Purpose (In Context) (Level A)",
                element_tag="a",
                selector=self._build_selector(node),
                line_number=node.line,
                severity="medium",
                description=f"Link text '{text}' is vague out of context for screen reader users.",
                recommendation="Replace generic link text with specific destination description (e.g. 'Read documentation' instead of 'Read more').",
                verification_type="needs_manual_review",
                code_snippet=f'<a href="{node.attrs.get("href", "#")}">{text}</a>'
            ))

    def _check_button_accessible_name(self, node: DOMNode, findings: List[HTMLA11yFinding]):
        text = node.text_content.strip()
        aria_label = node.attrs.get("aria-label", "").strip()
        has_img_alt = any(c.tag == "img" and c.attrs.get("alt", "").strip() for c in node.children)

        if not text and not aria_label and not has_img_alt:
            findings.append(HTMLA11yFinding(
                id=f"a11y-button-name-{len(findings) + 1}",
                rule_id="button-missing-name",
                wcag_sc="4.1.2 Name, Role, Value (Level A)",
                element_tag="button",
                selector=self._build_selector(node),
                line_number=node.line,
                severity="critical",
                description="Button element has no accessible text name, icon alt text, or aria-label.",
                recommendation="Include visible button label text or specify aria-label=\"Action description\".",
                verification_type="static_verified",
                code_snippet='<button></button>'
            ))

    def _check_css_focus_suppression(self, css: str, findings: List[HTMLA11yFinding]):
        # Match outline: none or outline: 0
        pattern = re.compile(
            r"([^{}]*?:focus[^{}]*?)\{\s*([^}]*?outline\s*:\s*(none|0\b)[^}]*?)\}",
            re.IGNORECASE | re.DOTALL
        )
        for match in pattern.finditer(css):
            selector_block = match.group(1).strip()
            decl_body = match.group(2).lower()

            # Check if an alternative focus styling is provided (box-shadow, border-color, background)
            has_alternative = ("box-shadow" in decl_body or "border-color" in decl_body or "background" in decl_body)
            if not has_alternative:
                findings.append(HTMLA11yFinding(
                    id=f"a11y-focus-outline-{len(findings) + 1}",
                    rule_id="focus-indicator-suppressed",
                    wcag_sc="2.4.7 Focus Visible (Level AA)",
                    element_tag="css_rule",
                    selector=selector_block,
                    line_number=1,
                    severity="high",
                    description=f"CSS rule '{selector_block}' removes the default focus outline without providing an alternative focus indicator.",
                    recommendation="Ensure keyboard focus remains clearly visible (e.g. outline: 2px solid var(--accent); outline-offset: 2px; or box-shadow).",
                    verification_type="static_verified",
                    code_snippet=f"{selector_block} {{ outline: none; }}"
                ))

    def _build_selector(self, node: DOMNode) -> str:
        tag = node.tag
        if node.id:
            return f"{tag}#{node.id}"
        if node.classes:
            return f"{tag}.{node.classes[0]}"
        return tag
