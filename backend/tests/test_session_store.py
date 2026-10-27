"""
Unit tests for SQLite Session Store
"""

import pytest
from pathlib import Path
from backend.app.database.session_store import SessionStore


def test_session_crud_and_comparison(tmp_path):
    db_file = tmp_path / "test_sessions.db"
    store = SessionStore(db_path=db_file)

    # 1. Save session A
    s_a_id = store.save_session(
        name="Baseline Scan",
        input_type="paste",
        html_content="<p>Test</p>",
        css_content="p { color: #aaa; }",
        summary={"compliance_score": 60.0, "total_analyzed": 10, "fail_aa_count": 4},
        findings=[{"id": "1", "ratio": 2.5}],
        tokens=[]
    )
    assert s_a_id is not None

    # 2. List sessions
    sessions = store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["name"] == "Baseline Scan"
    assert sessions[0]["compliance_score"] == 60.0

    # 3. Get session A
    loaded_a = store.get_session(s_a_id)
    assert loaded_a is not None
    assert loaded_a["html_content"] == "<p>Test</p>"

    # 4. Save session B (after fixes)
    s_b_id = store.save_session(
        name="Patched Scan",
        input_type="paste",
        html_content="<p>Test</p>",
        css_content="p { color: #333; }",
        summary={"compliance_score": 100.0, "total_analyzed": 10, "fail_aa_count": 0},
        findings=[{"id": "1", "ratio": 7.0}],
        tokens=[]
    )

    # 5. Compare sessions A and B
    comp = store.compare_sessions(s_a_id, s_b_id)
    assert comp is not None
    assert comp["improvements"]["score_delta"] == 40.0
    assert comp["improvements"]["fail_reduction"] == 4
    assert comp["improvements"]["is_better"] is True

    # 6. Rename session A
    rename_ok = store.rename_session(s_a_id, "Baseline v1.1")
    assert rename_ok is True
    assert store.get_session(s_a_id)["name"] == "Baseline v1.1"

    # 7. Delete session A
    del_ok = store.delete_session(s_a_id)
    assert del_ok is True
    assert store.get_session(s_a_id) is None
    assert len(store.list_sessions()) == 1
