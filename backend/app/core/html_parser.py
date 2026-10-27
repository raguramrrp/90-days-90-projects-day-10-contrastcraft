"""
ContrastCraft — HTML Parser Module
Lightweight, resilient DOM tree builder using Python's standard html.parser.
Extracts element nodes, inline styles, text content, line numbers, semantic roles,
and embedded style blocks / linked stylesheets.
"""

from __future__ import annotations
import re
from html.parser import HTMLParser
from typing import List, Dict, Optional, Tuple


class DOMNode:
    def __init__(
        self,
        tag: str,
        attrs: Dict[str, str],
        line: int = 1,
        parent: Optional[DOMNode] = None
    ):
        self.tag: str = tag.lower()
        self.attrs: Dict[str, str] = attrs
        self.line: int = line
        self.parent: Optional[DOMNode] = parent
        self.children: List[DOMNode] = []
        self.text_content: str = ""
        self.inline_styles: Dict[str, str] = self._parse_inline_style(attrs.get("style", ""))
        self.id: str = attrs.get("id", "").strip()
        self.classes: List[str] = [c.strip() for c in attrs.get("class", "").split() if c.strip()]
        self.role: str = self._determine_semantic_role()

    def _parse_inline_style(self, style_str: str) -> Dict[str, str]:
        styles: Dict[str, str] = {}
        if not style_str:
            return styles
        # Split on semicolons not within parentheses or quotes
        parts = re.split(r";(?=(?:[^\"']*\"[^\"']*\")*[^\"']*$)", style_str)
        for part in parts:
            if ":" in part:
                prop, val = part.split(":", 1)
                prop_clean = prop.strip().lower()
                val_clean = val.strip()
                if prop_clean and val_clean:
                    styles[prop_clean] = val_clean
        return styles

    def _determine_semantic_role(self) -> str:
        explicit_role = self.attrs.get("role", "").lower().strip()
        if explicit_role:
            return explicit_role

        if self.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return "heading"
        if self.tag == "a" and "href" in self.attrs:
            return "link"
        if self.tag == "button" or (self.tag == "input" and self.attrs.get("type") in ("button", "submit", "reset")):
            return "button"
        if self.tag in ("input", "textarea", "select"):
            return "input"
        if self.tag in ("p", "span", "li", "td", "th", "label", "blockquote", "dd", "dt", "figcaption"):
            return "text"
        return "container"

    def get_selector(self) -> str:
        """Constructs a readable CSS selector path for this element."""
        parts = []
        curr: Optional[DOMNode] = self
        while curr and curr.tag != "[root]":
            sel = curr.tag
            if curr.id:
                sel += f"#{curr.id}"
                parts.insert(0, sel)
                break
            elif curr.classes:
                sel += "." + ".".join(curr.classes[:2])
            parts.insert(0, sel)
            curr = curr.parent
            if len(parts) >= 4:  # Keep readable
                break
        return " > ".join(parts) if parts else self.tag

    def walk(self) -> List[DOMNode]:
        """Flatten tree depth-first."""
        nodes = [self]
        for child in self.children:
            nodes.extend(child.walk())
        return nodes


class HTMLTreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = DOMNode("[root]", {})
        self.current_node: DOMNode = self.root
        self.style_blocks: List[Tuple[str, int]] = []  # (css_content, line_number)
        self.linked_stylesheets: List[str] = []
        self._in_style_tag: bool = False
        self._current_style_text: str = ""
        self._current_style_line: int = 1

    def handle_starttag(self, tag: str, attrs_list: List[Tuple[str, Optional[str]]]):
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        line = self.getpos()[0]

        if tag.lower() == "style":
            self._in_style_tag = True
            self._current_style_text = ""
            self._current_style_line = line
            return

        if tag.lower() == "link":
            rel = attrs.get("rel", "").lower()
            href = attrs.get("href", "")
            if "stylesheet" in rel and href:
                self.linked_stylesheets.append(href)

        node = DOMNode(tag, attrs, line=line, parent=self.current_node)
        self.current_node.children.append(node)

        # Self-closing tags in HTML
        void_tags = {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"
        }
        if tag.lower() not in void_tags:
            self.current_node = node

    def handle_endtag(self, tag: str):
        if tag.lower() == "style":
            self._in_style_tag = False
            if self._current_style_text.strip():
                self.style_blocks.append((self._current_style_text, self._current_style_line))
            self._current_style_text = ""
            return

        if self.current_node.parent and self.current_node.tag == tag.lower():
            self.current_node = self.current_node.parent

    def handle_data(self, data: str):
        if self._in_style_tag:
            self._current_style_text += data
        else:
            cleaned = data.strip()
            if cleaned:
                if self.current_node.text_content:
                    self.current_node.text_content += " " + cleaned
                else:
                    self.current_node.text_content = cleaned


def parse_html_document(html_content: str) -> Tuple[DOMNode, List[Tuple[str, int]], List[str]]:
    """
    Parses HTML content into DOMNode tree, extracted style blocks, and linked stylesheet paths.
    Returns: (root_node, style_blocks, linked_stylesheets)
    """
    builder = HTMLTreeBuilder()
    builder.feed(html_content)
    builder.close()
    return builder.root, builder.style_blocks, builder.linked_stylesheets
