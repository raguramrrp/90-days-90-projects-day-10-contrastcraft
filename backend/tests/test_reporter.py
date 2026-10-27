"""
Unit tests for Report Generation (JSON, HTML, CSS export)
"""

import json
import pytest
from backend.app.core.reporter import (
    generate_json_report,
    generate_html_report,
    generate_csv_report,
    export_corrected_css
)


def test_json_report_generation():
    sample_audit = {
        "summary": {"total_analyzed": 5, "compliance_score": 80.0},
        "findings": [
            {
                "id": "cc-1",
                "selector": "p.text",
                "effective_fg": "#0F172A",
                "effective_bg": "#FFFFFF",
                "contrast_ratio": 16.2,
                "pass_aa": True
            }
        ],
        "tokens": []
    }
    json_str = generate_json_report(sample_audit, session_name="Test Suite")
    data = json.loads(json_str)

    assert data["report_title"] == "Test Suite"
    assert data["version"] == "1.0.0"
    assert data["summary"]["compliance_score"] == 80.0
    assert len(data["findings"]) == 1


def test_html_report_escaping_and_structure():
    sample_audit = {
        "summary": {"compliance_score": 75.0, "total_analyzed": 2, "pass_aa_count": 1, "fail_aa_count": 1},
        "findings": [
            {
                "id": "cc-1",
                "selector": "h1 > span<script>alert(1)</script>",
                "text_sample": "<img src=x onerror=alert(1)> Title",
                "effective_fg": "#111827",
                "effective_bg": "#FFFFFF",
                "formatted_ratio": "17.40:1",
                "pass_aa": True,
                "status": "pass",
                "criterion_id": "1.4.3",
                "element_role": "heading",
                "explanation": "Valid contrast"
            }
        ],
        "tokens": []
    }
    html_output = generate_html_report(sample_audit, session_name="Escaped & Secure")
    assert "<!DOCTYPE html>" in html_output
    assert "Escaped &amp; Secure" in html_output
    # Ensure XSS injection payloads are safely HTML-escaped
    assert "<script>alert(1)</script>" not in html_output
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_output
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_output


def test_corrected_css_export():
    findings = [
        {
            "selector": ".footer-note",
            "element_role": "text",
            "suggested_fix": {
                "suggested_hex": "#475569",
                "formatted_projected_ratio": "5.20:1"
            }
        }
    ]
    css_res = export_corrected_css(findings)
    assert ".footer-note {" in css_res
    assert "color: #475569;" in css_res
    assert "5.20:1" in css_res


def test_csv_report_generation():
    sample_audit = {
        "findings": [
            {
                "id": "cc-1",
                "selector": ".hero-caption",
                "element_role": "text",
                "line_number": 15,
                "text_sample": "Subtitle sample",
                "effective_fg": "#94A3B8",
                "effective_bg": "#FFFFFF",
                "contrast_ratio": 2.60,
                "target_threshold": 4.5,
                "pass_aa": False,
                "pass_aaa": False,
                "criterion_id": "1.4.3",
                "severity": "high",
                "confidence": "verified",
                "explanation": "Contrast failure",
                "suggested_fix": {
                    "suggested_hex": "#596A82",
                    "formatted_projected_ratio": "4.62:1"
                }
            }
        ]
    }
    csv_output = generate_csv_report(sample_audit)
    lines = csv_output.strip().splitlines()
    assert len(lines) == 2  # Header + 1 row
    assert "Finding ID,Selector,Element Role" in lines[0]
    assert "cc-1,.hero-caption,text,15" in lines[1]
    assert "#94A3B8,#FFFFFF,2.6,4.5,FAIL,FAIL" in lines[1]
    assert "#596A82,4.62:1" in lines[1]

