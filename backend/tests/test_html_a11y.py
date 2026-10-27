"""
Unit tests for ContrastCraft Extended HTML Accessibility Auditor
"""

import pytest
from backend.app.core.html_a11y import HTMLA11yAuditor


def test_html_missing_lang():
    auditor = HTMLA11yAuditor()
    html_without_lang = "<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
    findings = auditor.audit(html_without_lang)
    rule_ids = [f.rule_id for f in findings]
    assert "html-missing-lang" in rule_ids

    html_with_lang = "<html lang=\"en\"><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
    findings_valid = auditor.audit(html_with_lang)
    rule_ids_valid = [f.rule_id for f in findings_valid]
    assert "html-missing-lang" not in rule_ids_valid


def test_image_alt_detection():
    auditor = HTMLA11yAuditor()
    html = """
    <div>
        <img src="pic1.png">
        <img src="pic2.jpg" alt="photo">
        <img src="pic3.jpg" alt="Detailed diagram of neural network">
    </div>
    """
    findings = auditor.audit(html)
    rule_ids = [f.rule_id for f in findings]
    assert "img-missing-alt" in rule_ids
    assert "img-redundant-alt" in rule_ids


def test_form_label_associations():
    auditor = HTMLA11yAuditor()
    html = """
    <form>
        <input type="text" id="unlabeled" name="username">
        <label for="labeled-input">Email Address</label>
        <input type="email" id="labeled-input" name="email">
        <label>Password <input type="password" name="pwd"></label>
        <input type="text" aria-label="Search site">
    </form>
    """
    findings = auditor.audit(html)
    unlabeled_findings = [f for f in findings if f.rule_id == "input-missing-label"]
    assert len(unlabeled_findings) == 1
    assert "unlabeled" in unlabeled_findings[0].selector


def test_empty_and_generic_links():
    auditor = HTMLA11yAuditor()
    html = """
    <div>
        <a href="/target"></a>
        <a href="/docs">Click here</a>
        <a href="/report">Read annual financial report</a>
    </div>
    """
    findings = auditor.audit(html)
    rule_ids = [f.rule_id for f in findings]
    assert "link-empty-content" in rule_ids
    assert "link-uninformative-text" in rule_ids


def test_heading_hierarchy_skips():
    auditor = HTMLA11yAuditor()
    # Skips from h1 directly to h3
    html = "<div><h1>Title</h1><h3>Subtopic</h3></div>"
    findings = auditor.audit(html)
    rule_ids = [f.rule_id for f in findings]
    assert "heading-skipped-level" in rule_ids


def test_button_missing_accessible_name():
    auditor = HTMLA11yAuditor()
    html = """
    <div>
        <button class="icon-only"></button>
        <button class="named">Submit Application</button>
        <button aria-label="Close dialog"></button>
    </div>
    """
    findings = auditor.audit(html)
    btn_findings = [f for f in findings if f.rule_id == "button-missing-name"]
    assert len(btn_findings) == 1


def test_css_focus_outline_suppression():
    auditor = HTMLA11yAuditor()
    html = '<button class="bad-focus">Click</button>'
    css = ".bad-focus:focus { outline: none; }"
    findings = auditor.audit(html, custom_css=css)
    rule_ids = [f.rule_id for f in findings]
    assert "focus-indicator-suppressed" in rule_ids
