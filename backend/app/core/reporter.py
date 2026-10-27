"""
ContrastCraft — Report Generation Module
Generates structured JSON exports, standalone print-ready HTML accessibility reports,
and downloadable corrected CSS stylesheets.
"""

from __future__ import annotations
import csv
import datetime
import html
import io
import json
from typing import Dict, List, Any


def generate_json_report(audit_data: Dict[str, Any], session_name: str = "ContrastCraft Audit") -> str:
    """Generates formatted JSON audit report."""
    report = {
        "report_title": session_name,
        "tool": "ContrastCraft Automated Accessibility Contrast Auditor",
        "version": "1.0.0",
        "generated_at": datetime.datetime.now().isoformat(),
        "summary": audit_data.get("summary", {}),
        "findings": audit_data.get("findings", []),
        "design_tokens": audit_data.get("tokens", []),
        "disclaimer": (
            "ContrastCraft performs deterministic static analysis against WCAG 2.1/2.2 Success Criteria. "
            "Items marked 'needs_browser_verification' require runtime browser validation."
        )
    }
    return json.dumps(report, indent=2)


def generate_html_report(audit_data: Dict[str, Any], session_name: str = "ContrastCraft Audit") -> str:
    """Generates self-contained, responsive, printable HTML report with safe escaping."""
    summary = audit_data.get("summary", {})
    findings = audit_data.get("findings", [])
    tokens = audit_data.get("tokens", [])
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    score = summary.get("compliance_score", 0.0)
    total = summary.get("total_analyzed", 0)
    pass_aa = summary.get("pass_aa_count", 0)
    fail_aa = summary.get("fail_aa_count", 0)
    pass_aaa = summary.get("pass_aaa_count", 0)
    fail_aaa = summary.get("fail_aaa_count", 0)
    unresolved = summary.get("needs_verification_count", 0)

    # Build rows
    rows_html = []
    for f in findings:
        status_badge_class = "badge-pass" if f.get("pass_aa") else "badge-fail"
        status_label = "AA PASS" if f.get("pass_aa") else "AA FAIL"
        if f.get("status") == "unresolved":
            status_badge_class = "badge-unresolved"
            status_label = "VERIFY"

        fg_hex = html.escape(f.get("effective_fg", "#000000"))
        bg_hex = html.escape(f.get("effective_bg", "#FFFFFF"))
        ratio_str = html.escape(f.get("formatted_ratio", "N/A"))
        selector_str = html.escape(f.get("selector", ""))
        text_sample = html.escape(f.get("text_sample", ""))
        role_str = html.escape(f.get("element_role", ""))
        crit_str = html.escape(f.get("criterion_id", ""))
        expl_str = html.escape(f.get("explanation", ""))

        sugg = f.get("suggested_fix")
        sugg_html = "-"
        if sugg:
            s_hex = html.escape(sugg.get("suggested_hex", ""))
            s_ratio = html.escape(sugg.get("formatted_projected_ratio", ""))
            sugg_html = f"""
            <div style="display:flex;align-items:center;gap:6px;">
                <span class="color-swatch" style="background-color:{s_hex};border:1px solid #94A3B8;"></span>
                <code>{s_hex}</code>
                <span class="badge-mini">{s_ratio}</span>
            </div>
            """

        row = f"""
        <tr>
            <td><span class="badge {status_badge_class}">{status_label}</span></td>
            <td>
                <strong>{role_str}</strong>
                <div class="code-sm">{selector_str}</div>
                <div class="sample-text">"{text_sample}"</div>
            </td>
            <td>
                <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                    <span class="color-swatch" style="background-color:{fg_hex};"></span>
                    <span class="color-label">FG: {fg_hex}</span>
                </div>
                <div style="display:flex;align-items:center;gap:6px;">
                    <span class="color-swatch" style="background-color:{bg_hex};border:1px solid #CBD5E1;"></span>
                    <span class="color-label">BG: {bg_hex}</span>
                </div>
            </td>
            <td>
                <strong style="font-size:1.1rem;">{ratio_str}</strong>
                <div class="code-sm">Req: {f.get('target_threshold', 4.5)}:1</div>
            </td>
            <td>
                <span class="crit-tag">{crit_str}</span>
                <div class="expl-sm">{expl_str}</div>
            </td>
            <td>{sugg_html}</td>
        </tr>
        """
        rows_html.append(row)

    findings_tbody = "\n".join(rows_html) if rows_html else "<tr><td colspan='6' style='text-align:center;'>No findings recorded.</td></tr>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ContrastCraft Audit Report — {html.escape(session_name)}</title>
    <style>
        :root {{
            --bg: #F8FAFC;
            --surface: #FFFFFF;
            --text: #0F172A;
            --text-muted: #64748B;
            --border: #E2E8F0;
            --primary: #0284C7;
            --pass-bg: #DCFCE7;
            --pass-text: #15803D;
            --fail-bg: #FEE2E2;
            --fail-text: #B91C1C;
            --warn-bg: #FEF3C7;
            --warn-text: #B45309;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #0B0F19;
                --surface: #111827;
                --text: #F1F5F9;
                --text-muted: #94A3B8;
                --border: #1F2937;
                --primary: #38BDF8;
                --pass-bg: #064E3B;
                --pass-text: #6EE7B7;
                --fail-bg: #7F1D1D;
                --fail-text: #FCA5A5;
                --warn-bg: #78350F;
                --warn-text: #FDE68A;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 32px 24px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        h1 {{ margin: 0 0 6px 0; font-size: 1.6rem; letter-spacing: -0.02em; }}
        .meta {{ color: var(--text-muted); font-size: 0.9rem; }}
        .score-pill {{
            background: var(--surface);
            border: 2px solid var(--primary);
            padding: 12px 24px;
            border-radius: 12px;
            text-align: center;
        }}
        .score-val {{ font-size: 2rem; font-weight: 800; color: var(--primary); line-height: 1; }}
        .score-lbl {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); margin-top: 4px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 20px;
        }}
        .stat-num {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 4px; }}
        .stat-title {{ font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; }}
        .table-wrap {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow-x: auto;
            margin-bottom: 32px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }}
        th, td {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }}
        th {{
            background: rgba(0,0,0,0.02);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.8rem;
            text-transform: uppercase;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }}
        .badge-pass {{ background: var(--pass-bg); color: var(--pass-text); }}
        .badge-fail {{ background: var(--fail-bg); color: var(--fail-text); }}
        .badge-unresolved {{ background: var(--warn-bg); color: var(--warn-text); }}
        .badge-mini {{
            background: var(--pass-bg);
            color: var(--pass-text);
            font-size: 0.72rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 700;
        }}
        .color-swatch {{
            display: inline-block;
            width: 16px;
            height: 16px;
            border-radius: 4px;
            vertical-align: middle;
        }}
        .color-label {{ font-family: ui-monospace, monospace; font-size: 0.8rem; }}
        .code-sm {{ font-family: ui-monospace, monospace; font-size: 0.75rem; color: var(--text-muted); }}
        .sample-text {{ font-size: 0.82rem; color: var(--text-muted); margin-top: 2px; font-style: italic; }}
        .crit-tag {{
            display: inline-block;
            background: rgba(0,0,0,0.06);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
        }}
        .expl-sm {{ font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }}
        .footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div>
                <h1>ContrastCraft — Accessibility Contrast Audit</h1>
                <div class="meta">
                    Target: <strong>{html.escape(session_name)}</strong> • Generated: <strong>{timestamp}</strong>
                </div>
            </div>
            <div class="score-pill">
                <div class="score-val">{score}%</div>
                <div class="score-lbl">Compliance Score</div>
            </div>
        </header>

        <section class="stats-grid">
            <div class="stat-card">
                <div class="stat-num">{total}</div>
                <div class="stat-title">Total Evaluated</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color:var(--pass-text);">{pass_aa}</div>
                <div class="stat-title">WCAG Level AA Passes</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color:var(--fail-text);">{fail_aa}</div>
                <div class="stat-title">WCAG Level AA Failures</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">{pass_aaa}</div>
                <div class="stat-title">WCAG Level AAA Passes</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">{unresolved}</div>
                <div class="stat-title">Needs Verification</div>
            </div>
        </section>

        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Element & Context</th>
                        <th>Colors (FG / BG)</th>
                        <th>Ratio</th>
                        <th>WCAG Criterion & Reason</th>
                        <th>Suggested Fix</th>
                    </tr>
                </thead>
                <tbody>
                    {findings_tbody}
                </tbody>
            </table>
        </div>

        <footer class="footer">
            Generated locally by ContrastCraft — Automated Web Accessibility Contrast Auditor (WCAG 2.1 / 2.2 Compliant)
        </footer>
    </div>
</body>
</html>"""
    return html_content


def export_corrected_css(findings: List[Dict[str, Any]], original_css: str = "") -> str:
    """Exports clean corrected CSS rules based on approved fixes."""
    lines = [
        "/* =============================================================== */",
        "/* ContrastCraft Accessible CSS Patch                              */",
        "/* Automatically generated to resolve WCAG contrast violations    */",
        f"/* Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                 */",
        "/* =============================================================== */\n"
    ]

    applied_rules = []
    for f in findings:
        sugg = f.get("suggested_fix")
        if sugg:
            sel = f.get("selector", "")
            hex_val = sugg.get("suggested_hex")
            role = f.get("element_role")
            prop = "border-color" if "border" in role else "color"
            ratio = sugg.get("formatted_projected_ratio", "")
            
            rule_str = f"/* Passes target threshold ({ratio}) */\n{sel} {{\n  {prop}: {hex_val};\n}}\n"
            applied_rules.append(rule_str)

    if not applied_rules:
        lines.append("/* All analyzed elements already satisfy applicable WCAG contrast criteria. */\n")
    else:
        lines.extend(applied_rules)

    return "\n".join(lines)


def generate_csv_report(audit_data: Dict[str, Any]) -> str:
    """Generates RFC 4180 compliant CSV export of all audit findings."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        "Finding ID",
        "Selector",
        "Element Role",
        "Line Number",
        "Text Sample",
        "Effective FG",
        "Effective BG",
        "Contrast Ratio",
        "Target Threshold",
        "WCAG AA Status",
        "WCAG AAA Status",
        "WCAG Criterion",
        "Severity",
        "Confidence",
        "Explanation",
        "Proposed Fix Hex",
        "Projected Ratio"
    ])

    findings = audit_data.get("findings", [])
    for f in findings:
        sugg = f.get("suggested_fix") or {}
        writer.writerow([
            f.get("id", ""),
            f.get("selector", ""),
            f.get("element_role", ""),
            f.get("line_number", ""),
            f.get("text_sample", ""),
            f.get("effective_fg", ""),
            f.get("effective_bg", ""),
            f.get("contrast_ratio", ""),
            f.get("target_threshold", ""),
            "PASS" if f.get("pass_aa") else "FAIL",
            "PASS" if f.get("pass_aaa") else "FAIL",
            f.get("criterion_id", ""),
            f.get("severity", ""),
            f.get("confidence", ""),
            f.get("explanation", ""),
            sugg.get("suggested_hex", ""),
            sugg.get("formatted_projected_ratio", "")
        ])

    return output.getvalue()

