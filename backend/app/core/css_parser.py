"""
ContrastCraft — CSS Parser and Cascade Resolver
Parses CSS declarations, custom properties, pseudo-classes, media queries,
calculates selector specificity, and resolves effective styles through the DOM cascade.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from .html_parser import DOMNode


@dataclass
class CSSDeclaration:
    property: str
    value: str
    important: bool = False
    source_line: int = 1


@dataclass
class CSSRule:
    selector: str
    declarations: Dict[str, CSSDeclaration]
    media_query: Optional[str] = None
    pseudo_class: Optional[str] = None  # hover, focus, focus-visible, active, disabled
    specificity: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (inline, id, class/pseudo, tag)
    source_line: int = 1
    source_file: str = "inline"


def calculate_specificity(selector: str) -> Tuple[int, int, int, int]:
    """
    Computes CSS Specificity (inline, ID, class/attr/pseudo, element).
    """
    clean_sel = re.sub(r"::(before|after|placeholder|first-line|first-letter)", "", selector)
    
    # IDs: #id
    id_count = len(re.findall(r"#[a-zA-Z0-9_\-]+", clean_sel))
    
    # Classes, attributes, pseudo-classes
    class_count = len(re.findall(r"\.[a-zA-Z0-9_\-]+", clean_sel))
    attr_count = len(re.findall(r"\[[^\]]+\]", clean_sel))
    pseudo_count = len(re.findall(r":[a-zA-Z0-9_\-]+(?:\([^)]*\))?", clean_sel))
    b_count = class_count + attr_count + pseudo_count
    
    # Elements & pseudo-elements
    # Remove strings, IDs, classes, attributes
    no_ids_classes = re.sub(r"#[a-zA-Z0-9_\-]+|\.[a-zA-Z0-9_\-]+|\[[^\]]+\]|:[a-zA-Z0-9_\-]+", " ", clean_sel)
    # Match tags
    tag_matches = re.findall(r"\b[a-zA-Z0-9_\-]+\b", no_ids_classes)
    # Exclude common combinators or keywords
    tag_count = len([t for t in tag_matches if t not in ("and", "not", "only", "screen", "all")])

    return (0, id_count, b_count, tag_count)


def strip_css_comments(css_text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)


class CSSStylesheet:
    def __init__(self, source_file: str = "inline"):
        self.source_file = source_file
        self.rules: List[CSSRule] = []
        self.variables: Dict[str, str] = {}
        self.media_rules: List[CSSRule] = []

    def parse(self, css_text: str, base_line: int = 1):
        clean_text = strip_css_comments(css_text)
        
        # Match @media blocks: @media (...) { ... }
        media_pattern = re.compile(r"@media\s*([^{]+)\{((?:[^{}]+|\{[^{}]*\})*)\}", re.DOTALL | re.IGNORECASE)
        
        last_end = 0
        for match in media_pattern.finditer(clean_text):
            # Parse preceding normal rules
            preceding = clean_text[last_end:match.start()]
            self._parse_rules_block(preceding, media_query=None, base_line=base_line)
            
            media_cond = match.group(1).strip()
            media_body = match.group(2)
            self._parse_rules_block(media_body, media_query=media_cond, base_line=base_line)
            last_end = match.end()

        # Parse remaining rules
        remaining = clean_text[last_end:]
        self._parse_rules_block(remaining, media_query=None, base_line=base_line)

    def _parse_rules_block(self, block_text: str, media_query: Optional[str], base_line: int):
        # Match standard rule: selector { property: value; ... }
        rule_pattern = re.compile(r"([^{]+)\{([^}]+)\}", re.DOTALL)
        for match in rule_pattern.finditer(block_text):
            selectors_raw = match.group(1).strip()
            declarations_raw = match.group(2).strip()

            if selectors_raw.startswith("@"):
                continue  # Skip unhandled @-rules like @keyframes, @font-face

            # Parse declarations
            decls: Dict[str, CSSDeclaration] = {}
            for item in re.split(r";(?=(?:[^\"']*\"[^\"']*\")*[^\"']*$)", declarations_raw):
                if ":" in item:
                    prop, val = item.split(":", 1)
                    prop_name = prop.strip().lower()
                    val_str = val.strip()
                    if not prop_name or not val_str:
                        continue
                    
                    is_important = "!important" in val_str.lower()
                    val_clean = re.sub(r"\s*!important\s*$", "", val_str, flags=re.IGNORECASE).strip()

                    decls[prop_name] = CSSDeclaration(
                        property=prop_name,
                        value=val_clean,
                        important=is_important,
                        source_line=base_line
                    )

                    # Extract CSS variables
                    if prop_name.startswith("--"):
                        self.variables[prop_name] = val_clean

            # Split comma-separated selectors
            selectors = [s.strip() for s in selectors_raw.split(",") if s.strip()]
            for sel in selectors:
                pseudo = None
                clean_sel = sel
                # Check for pseudo-classes
                pseudo_match = re.search(r":(hover|focus|focus-visible|active|disabled)\b", sel)
                if pseudo_match:
                    pseudo = pseudo_match.group(1)
                    clean_sel = re.sub(r":(hover|focus|focus-visible|active|disabled)\b", "", sel).strip()
                    if not clean_sel:
                        clean_sel = "*"

                spec = calculate_specificity(sel)
                rule = CSSRule(
                    selector=clean_sel,
                    declarations=decls,
                    media_query=media_query,
                    pseudo_class=pseudo,
                    specificity=spec,
                    source_line=base_line,
                    source_file=self.source_file
                )
                if media_query:
                    self.media_rules.append(rule)
                else:
                    self.rules.append(rule)


def selector_matches_node(selector: str, node: DOMNode) -> bool:
    """
    Lightweight, robust CSS selector matcher for static DOM analysis.
    Supports tag, #id, .class, [attr], descendant, and direct child.
    """
    sel = selector.strip()
    if not sel or sel == "*":
        return True

    # If selector has descendant or child combinators, match target against rightmost part
    if " > " in sel:
        parts = sel.split(" > ")
        target = parts[-1].strip()
        if not _match_single_compound_selector(target, node):
            return False
        # Parent check
        if node.parent and parts[0].strip() != "[root]":
            return selector_matches_node(" > ".join(parts[:-1]), node.parent)
        return False
    elif " " in sel:
        parts = sel.split()
        target = parts[-1].strip()
        if not _match_single_compound_selector(target, node):
            return False
        # Ancestor check
        ancestor_sel = " ".join(parts[:-1])
        curr = node.parent
        while curr and curr.tag != "[root]":
            if selector_matches_node(ancestor_sel, curr):
                return True
            curr = curr.parent
        return False
    else:
        return _match_single_compound_selector(sel, node)


def _match_single_compound_selector(sel: str, node: DOMNode) -> bool:
    """Matches a single compound selector (e.g. 'button.btn.btn-primary#submit[disabled]')."""
    if sel == "*":
        return True

    # ID check
    id_match = re.search(r"#([a-zA-Z0-9_\-]+)", sel)
    if id_match:
        if node.id != id_match.group(1):
            return False

    # Class checks
    class_matches = re.findall(r"\.([a-zA-Z0-9_\-]+)", sel)
    for c in class_matches:
        if c not in node.classes:
            return False

    # Attribute checks: [attr] or [attr=val]
    attr_matches = re.findall(r"\[([a-zA-Z0-9_\-]+)(?:=[\"']?([^\"'\]]+)[\"']?)?\]", sel)
    for attr_name, attr_val in attr_matches:
        if attr_name not in node.attrs:
            return False
        if attr_val and node.attrs.get(attr_name) != attr_val:
            return False

    # Tag check
    clean_tag = re.sub(r"#[a-zA-Z0-9_\-]+|\.[a-zA-Z0-9_\-]+|\[[^\]]+\]", "", sel).strip()
    if clean_tag and clean_tag != "*":
        if node.tag != clean_tag.lower():
            return False

    return True


class CascadeResolver:
    """
    Resolves the effective computed styles of DOM nodes based on CSS specificity,
    inheritance, and inline style overrides.
    """
    def __init__(self, stylesheets: List[CSSStylesheet], custom_variables: Optional[Dict[str, str]] = None):
        self.stylesheets = stylesheets
        self.variables: Dict[str, str] = {}
        for sheet in stylesheets:
            self.variables.update(sheet.variables)
        if custom_variables:
            self.variables.update(custom_variables)

    def resolve_node_styles(
        self,
        node: DOMNode,
        pseudo_class: Optional[str] = None,
        media_active: bool = False
    ) -> Dict[str, str]:
        """
        Resolves effective style declarations for a given DOM node.
        Includes cascade sorting, property inheritance, and inline style overrides.
        """
        matched_rules: List[CSSRule] = []

        # Find matching rules across stylesheets
        for sheet in self.stylesheets:
            rules_to_check = sheet.rules + (sheet.media_rules if media_active else [])
            for rule in rules_to_check:
                if rule.pseudo_class == pseudo_class:
                    if selector_matches_node(rule.selector, node):
                        matched_rules.append(rule)

        # Sort matching rules by specificity and source order
        matched_rules.sort(key=lambda r: (r.specificity[0], r.specificity[1], r.specificity[2], r.specificity[3]))

        # Flatten matched declarations
        computed: Dict[str, str] = {}
        for rule in matched_rules:
            for prop, decl in rule.declarations.items():
                computed[prop] = decl.value

        # Apply inline styles (highest specificity: 1, 0, 0, 0)
        for prop, val in node.inline_styles.items():
            computed[prop] = val

        return computed

    def get_effective_colors(
        self,
        node: DOMNode,
        pseudo_class: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Calculates effective (color, background_color, border_color, outline_color).
        Handles CSS inheritance for text color and background traversal for transparent nodes.
        Returns: (color, background_color, border_color, outline_color)
        """
        styles = self.resolve_node_styles(node, pseudo_class=pseudo_class)
        fg_color = styles.get("color")
        bg_color = styles.get("background-color") or styles.get("background")
        border_color = styles.get("border-color") or styles.get("border")
        outline_color = styles.get("outline-color") or styles.get("outline")

        # Inherit foreground color from ancestors if not declared on element
        if not fg_color:
            curr = node.parent
            while curr and curr.tag != "[root]":
                parent_styles = self.resolve_node_styles(curr, pseudo_class=pseudo_class)
                if "color" in parent_styles:
                    fg_color = parent_styles["color"]
                    break
                curr = curr.parent

        # Resolve background color up the tree if not explicitly defined or transparent
        if not bg_color or bg_color.strip().lower() == "transparent":
            curr = node.parent
            while curr and curr.tag != "[root]":
                parent_styles = self.resolve_node_styles(curr, pseudo_class=pseudo_class)
                p_bg = parent_styles.get("background-color") or parent_styles.get("background")
                if p_bg and p_bg.strip().lower() != "transparent":
                    bg_color = p_bg
                    break
                curr = curr.parent

        return fg_color, bg_color, border_color, outline_color
