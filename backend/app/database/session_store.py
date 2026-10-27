"""
ContrastCraft — SQLite Audit Session Persistence
Provides local session storage, retrieval, renaming, deletion, and cross-session comparisons.
"""

from __future__ import annotations
import datetime
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class SessionStore:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent.parent / "contrastcraft.db"
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    input_type TEXT NOT NULL,
                    html_content TEXT,
                    css_content TEXT,
                    summary_json TEXT NOT NULL,
                    findings_json TEXT NOT NULL,
                    tokens_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_session(
        self,
        name: str,
        input_type: str,
        html_content: str,
        css_content: str,
        summary: Dict[str, Any],
        findings: List[Dict[str, Any]],
        tokens: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> str:
        s_id = session_id or str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            # Check if exists
            cur = conn.execute("SELECT id FROM audit_sessions WHERE id = ?", (s_id,))
            exists = cur.fetchone() is not None

            if exists:
                conn.execute("""
                    UPDATE audit_sessions
                    SET name = ?, updated_at = ?, input_type = ?, html_content = ?,
                        css_content = ?, summary_json = ?, findings_json = ?, tokens_json = ?
                    WHERE id = ?
                """, (
                    name, now, input_type, html_content, css_content,
                    json.dumps(summary), json.dumps(findings), json.dumps(tokens), s_id
                ))
            else:
                conn.execute("""
                    INSERT INTO audit_sessions (
                        id, name, created_at, updated_at, input_type,
                        html_content, css_content, summary_json, findings_json, tokens_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    s_id, name, now, now, input_type,
                    html_content, css_content,
                    json.dumps(summary), json.dumps(findings), json.dumps(tokens)
                ))
            conn.commit()
        return s_id

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT id, name, created_at, updated_at, input_type, summary_json
                FROM audit_sessions
                ORDER BY updated_at DESC
            """)
            rows = cur.fetchall()
            sessions = []
            for r in rows:
                summary = json.loads(r["summary_json"])
                sessions.append({
                    "id": r["id"],
                    "name": r["name"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                    "input_type": r["input_type"],
                    "compliance_score": summary.get("compliance_score", 0.0),
                    "total_analyzed": summary.get("total_analyzed", 0),
                    "fail_aa_count": summary.get("fail_aa_count", 0)
                })
            return sessions

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT id, name, created_at, updated_at, input_type,
                       html_content, css_content, summary_json, findings_json, tokens_json
                FROM audit_sessions
                WHERE id = ?
            """, (session_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "name": row["name"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "input_type": row["input_type"],
                "html_content": row["html_content"],
                "css_content": row["css_content"],
                "summary": json.loads(row["summary_json"]),
                "findings": json.loads(row["findings_json"]),
                "tokens": json.loads(row["tokens_json"])
            }

    def rename_session(self, session_id: str, new_name: str) -> bool:
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cur = conn.execute("""
                UPDATE audit_sessions SET name = ?, updated_at = ? WHERE id = ?
            """, (new_name, now, session_id))
            conn.commit()
            return cur.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM audit_sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cur.rowcount > 0

    def compare_sessions(self, session_id_a: str, session_id_b: str) -> Optional[Dict[str, Any]]:
        s_a = self.get_session(session_id_a)
        s_b = self.get_session(session_id_b)
        if not s_a or not s_b:
            return None

        sum_a = s_a["summary"]
        sum_b = s_b["summary"]

        score_diff = round(sum_b.get("compliance_score", 0) - sum_a.get("compliance_score", 0), 1)
        fail_diff = sum_b.get("fail_aa_count", 0) - sum_a.get("fail_aa_count", 0)

        return {
            "session_a": {
                "id": s_a["id"],
                "name": s_a["name"],
                "score": sum_a.get("compliance_score", 0),
                "fail_aa": sum_a.get("fail_aa_count", 0),
                "total": sum_a.get("total_analyzed", 0)
            },
            "session_b": {
                "id": s_b["id"],
                "name": s_b["name"],
                "score": sum_b.get("compliance_score", 0),
                "fail_aa": sum_b.get("fail_aa_count", 0),
                "total": sum_b.get("total_analyzed", 0)
            },
            "improvements": {
                "score_delta": score_diff,
                "fail_reduction": -fail_diff,
                "is_better": score_diff > 0
            }
        }
