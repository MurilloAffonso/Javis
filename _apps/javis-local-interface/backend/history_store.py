# history_store.py — sessões e histórico de chat isolados por project_id
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4

import db
import gate


_FILE = Path(__file__).parent.parent / "_data" / "chat_history.json"
MAX_ENTRIES = 200
DEFAULT_SESSION_ID = "default"
ACTIVE = "active"
ARCHIVED = "archived"


def normalize_project_id(project_id: str | None = None) -> str:
    return (project_id or "").strip() or gate.CORE_SCOPE


def normalize_session_id(session_id: str | None = None) -> str:
    return (session_id or "").strip() or DEFAULT_SESSION_ID


def new_session_id() -> str:
    return f"sess_{uuid4().hex}"


def _ensure_schema() -> None:
    db.init_db()
    for sql in (
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            title TEXT,
            status TEXT DEFAULT 'active',
            metadata_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_project ON chat_sessions(project_id, updated_at)",
    ):
        db.execute(sql)
    for col_sql in (
        "ALTER TABLE messages ADD COLUMN project_id TEXT",
        "ALTER TABLE messages ADD COLUMN session_id TEXT",
    ):
        try:
            db.execute(col_sql)
        except Exception:
            pass
    db.execute("CREATE INDEX IF NOT EXISTS idx_messages_project_session ON messages(project_id, session_id, id)")


def _legacy_messages() -> list[dict]:
    if not _FILE.exists():
        return []
    try:
        raw = json.loads(_FILE.read_text(encoding="utf-8"))[-MAX_ENTRIES:]
    except Exception:
        return []
    out = []
    for item in raw:
        role = (item.get("role") or "").strip()
        content = item.get("content")
        if role and content is not None:
            out.append({"role": role, "content": content, "ts": item.get("ts") or ""})
    return out


def get_session(session_id: str) -> dict | None:
    _ensure_schema()
    sid = normalize_session_id(session_id)
    return db.query_one("SELECT * FROM chat_sessions WHERE session_id=?", (sid,))


def session_scope_error(project_id: str, session_id: str) -> dict | None:
    _ensure_schema()
    pid = normalize_project_id(project_id)
    sid = normalize_session_id(session_id)
    row = get_session(sid)
    if not row:
        return None
    if row.get("project_id") != pid:
        return {"status": "blocked", "reason": "project_scope_mismatch"}
    return None


def ensure_session(
    project_id: str | None = None,
    session_id: str | None = None,
    title: str = "",
    metadata: dict | None = None,
) -> dict:
    _ensure_schema()
    pid = normalize_project_id(project_id)
    sid = normalize_session_id(session_id)
    existing = get_session(sid)
    if existing:
        if existing.get("project_id") != pid:
            return {"status": "blocked", "reason": "project_scope_mismatch", "session_id": sid, "project_id": pid}
        return {"status": "ok", "session_id": sid, "project_id": pid, "session": existing}
    meta = json.dumps(metadata, ensure_ascii=False) if metadata else None
    db.execute(
        """
        INSERT INTO chat_sessions(session_id, project_id, title, status, metadata_json, updated_at)
        VALUES(?,?,?,?,?,datetime('now'))
        """,
        (sid, pid, title or "", ACTIVE, meta),
    )
    return {
        "status": "ok",
        "session_id": sid,
        "project_id": pid,
        "session": get_session(sid),
        "created": True,
    }


def load(project_id: str | None = None, session_id: str | None = None) -> list[dict]:
    _ensure_schema()
    pid = normalize_project_id(project_id)
    sid = normalize_session_id(session_id)
    rows = db.query(
        """
        SELECT role, content, created_at AS ts
        FROM messages
        WHERE COALESCE(project_id, ?) = ? AND COALESCE(session_id, ?) = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (gate.CORE_SCOPE, pid, DEFAULT_SESSION_ID, sid, MAX_ENTRIES),
    )
    out = [
        {"role": r.get("role"), "content": r.get("content") or "", "ts": r.get("ts") or ""}
        for r in reversed(rows)
    ]
    if out or pid != gate.CORE_SCOPE or sid != DEFAULT_SESSION_ID:
        return out
    return _legacy_messages()


def append(*args, **kwargs) -> None:
    _ensure_schema()
    if len(args) >= 2 and args[0] in {"user", "assistant", "system", "tool"}:
        project_id = gate.CORE_SCOPE
        session_id = DEFAULT_SESSION_ID
        role = args[0]
        content = args[1]
    elif len(args) >= 3:
        project_id = normalize_project_id(args[0])
        session_id = normalize_session_id(args[1])
        message = args[2] or {}
        role = message.get("role", "")
        content = message.get("content", message.get("text", ""))
    else:
        project_id = normalize_project_id(kwargs.get("project_id"))
        session_id = normalize_session_id(kwargs.get("session_id"))
        role = kwargs.get("role", "")
        content = kwargs.get("content", "")
    role = (role or "").strip()
    if not role:
        return
    ensured = ensure_session(project_id, session_id)
    if ensured.get("status") != "ok":
        return
    db.execute(
        "INSERT INTO messages(role, content, source, project_id, session_id) VALUES(?,?,?,?,?)",
        (role, str(content or ""), "chat", normalize_project_id(project_id), normalize_session_id(session_id)),
    )
    db.execute(
        "UPDATE chat_sessions SET updated_at=datetime('now') WHERE session_id=?",
        (normalize_session_id(session_id),),
    )


def clear(project_id: str | None = None, session_id: str | None = None) -> None:
    _ensure_schema()
    pid = normalize_project_id(project_id)
    sid = normalize_session_id(session_id)
    db.execute(
        "DELETE FROM messages WHERE COALESCE(project_id, ?) = ? AND COALESCE(session_id, ?) = ?",
        (gate.CORE_SCOPE, pid, DEFAULT_SESSION_ID, sid),
    )


def list_sessions(project_id: str | None = None) -> list[dict]:
    _ensure_schema()
    pid = normalize_project_id(project_id)
    return db.query(
        """
        SELECT s.*, COUNT(m.id) AS message_count
        FROM chat_sessions s
        LEFT JOIN messages m
          ON m.session_id=s.session_id AND COALESCE(m.project_id, ?) = s.project_id
        WHERE s.project_id=?
        GROUP BY s.session_id
        ORDER BY s.updated_at DESC, s.created_at DESC
        """,
        (gate.CORE_SCOPE, pid),
    )


def archive_session(project_id: str, session_id: str) -> dict:
    _ensure_schema()
    mismatch = session_scope_error(project_id, session_id)
    if mismatch:
        return mismatch
    row = get_session(session_id)
    if not row:
        return {"status": "not_found", "reason": "session_not_found"}
    db.execute(
        "UPDATE chat_sessions SET status=?, updated_at=datetime('now') WHERE session_id=?",
        (ARCHIVED, normalize_session_id(session_id)),
    )
    return {"status": "ok", "session_id": normalize_session_id(session_id)}


def stats() -> dict:
    _ensure_schema()
    rows = db.query("SELECT project_id, COUNT(*) AS n FROM chat_sessions GROUP BY project_id ORDER BY project_id")
    total = sum(int(r.get("n") or 0) for r in rows)
    legacy_found = bool(_legacy_messages())
    inconsistencies = db.query(
        """
        SELECT session_id, COUNT(DISTINCT project_id) AS projects
        FROM messages
        WHERE session_id IS NOT NULL AND project_id IS NOT NULL
        GROUP BY session_id
        HAVING COUNT(DISTINCT project_id) > 1
        """
    )
    return {
        "total_sessions": total,
        "sessions_by_project": {r["project_id"]: int(r["n"]) for r in rows},
        "javes_core_sessions": next((int(r["n"]) for r in rows if r["project_id"] == gate.CORE_SCOPE), 0),
        "legacy_history_found": legacy_found,
        "session_project_inconsistencies": len(inconsistencies),
    }
