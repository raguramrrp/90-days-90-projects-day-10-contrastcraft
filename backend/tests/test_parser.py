"""
Unit tests for HTML Parsing, CSS Parsing, Specificity, and Cascade Resolution
"""

import pytest
from backend.app.core.html_parser import parse_html_document
from backend.app.core.css_parser import (
    CSSStylesheet,
    CascadeResolver,
    calculate_specificity,
    selector_matches_node
)


def test_html_parsing_and_roles():
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
        <h1 id="main-title" class="title header-text">Welcome</h1>
        <p style="color: #333; font-size: 16px;">Hello world</p>
        <button class="btn btn-primary" role="button">Submit</button>
        <a href="/login" class="link">Login</a>
    </body>
    </html>
    """
    root, style_blocks, linked = parse_html_document(sample_html)
    nodes = root.walk()

    h1_node = next(n for n in nodes if n.tag == "h1")
    assert h1_node.id == "main-title"
    assert "title" in h1_node.classes
    assert h1_node.role == "heading"

    p_node = next(n for n in nodes if n.tag == "p")
    assert p_node.inline_styles.get("color") == "#333"
    assert p_node.text_content == "Hello world"

    btn_node = next(n for n in nodes if n.tag == "button")
    assert btn_node.role == "button"


def test_specificity_calculation():
    # Tag only: (0, 0, 0, 1)
    assert calculate_specificity("h1") == (0, 0, 0, 1)

    # Class + tag: (0, 0, 1, 1)
    assert calculate_specificity("h1.title") == (0, 0, 1, 1)

    # ID + class + tag + pseudo: (0, 1, 2, 1)
    # #nav .item:hover li has 1 ID (#nav), 1 class (.item), 1 pseudo (:hover), 1 tag (li)
    spec = calculate_specificity("#nav .item:hover li")
    assert spec[1] == 1  # 1 ID
    assert spec[2] == 2  # 1 class + 1 pseudo-class
    assert spec[3] == 1  # 1 tag (li)


def test_css_cascade_and_inheritance():
    html_doc = """
    <div id="wrapper" style="background-color: #F8FAFC;">
        <article class="card">
            <h2 class="card-title">Card Header</h2>
            <p class="card-desc">Card body text</p>
        </article>
    </div>
    """
    css_text = """
    :root {
        --theme-text: #1E293B;
    }
    .card {
        color: var(--theme-text);
    }
    .card-title {
        color: #0F172A;
        font-size: 24px;
        font-weight: bold;
    }
    """
    root, _, _ = parse_html_document(html_doc)
    sheet = CSSStylesheet("main.css")
    sheet.parse(css_text)

    resolver = CascadeResolver([sheet])

    p_node = next(n for n in root.walk() if n.tag == "p")
    # p inherits color from .card ancestor
    fg, bg, _, _ = resolver.get_effective_colors(p_node)
    assert fg == "var(--theme-text)"
    # p inherits transparent background traversing up to #wrapper
    assert bg == "#F8FAFC"

    h2_node = next(n for n in root.walk() if n.tag == "h2")
    fg_h2, bg_h2, _, _ = resolver.get_effective_colors(h2_node)
    assert fg_h2 == "#0F172A"
    assert bg_h2 == "#F8FAFC"
