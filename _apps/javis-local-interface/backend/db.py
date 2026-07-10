"""db.py — camada de persistência SQLite do Javis (ADITIVA).

Decisão 20/06: SQLite entra como camada de persistência consultável, SEM
substituir os arquivos JSON/Markdown atuais (chat_history.json, codex_backlog.md,
logs JSONL). Tudo é dual-write: o sistema continua funcionando se o banco sumir.

Banco em `_data/javis.db`. Conexão por operação (sqlite é file-based; simples e
thread-safe pro uso do FastAPI em threadpool). `init_db()` é idempotente.
"""
from __future__ import annotations
import sqlite3
import threading
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent
DB_PATH = _BACKEND.parent / "_data" / "javis.db"
SCHEMA_PATH = _BACKEND / "migrations" / "schema.sql"

_init_lock = threading.Lock()
_initialized = False


def get_conn() -> sqlite3.Connection:
    """Conexão nova (row_factory = dict-like). Fechar após uso."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """Cria as tabelas (idempotente). Seguro chamar no boot toda vez."""
    global _initialized
    with _init_lock:
        if _initialized:
            return
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn = get_conn()
        try:
            conn.executescript(sql)
            # Migrações aditivas pra DBs já criados antes destas colunas existirem.
            # ALTER ADD COLUMN é seguro; ignora se a coluna já estiver lá.
            for col_sql in (
                "ALTER TABLE approvals ADD COLUMN task_id TEXT",
                "ALTER TABLE approvals ADD COLUMN note TEXT",
                "ALTER TABLE approvals ADD COLUMN project_id TEXT",
                "ALTER TABLE approvals ADD COLUMN action TEXT",
                "ALTER TABLE approvals ADD COLUMN route TEXT",
                "ALTER TABLE approvals ADD COLUMN risk_level TEXT",
                "ALTER TABLE approvals ADD COLUMN requested_by TEXT",
                "ALTER TABLE approvals ADD COLUMN approved_by TEXT",
                "ALTER TABLE approvals ADD COLUMN approval_token_id TEXT",
                "ALTER TABLE approvals ADD COLUMN consumed_at TEXT",
                "ALTER TABLE approvals ADD COLUMN reason TEXT",
                "ALTER TABLE approvals ADD COLUMN metadata_json TEXT",
                "ALTER TABLE approvals ADD COLUMN updated_at TEXT",
                "ALTER TABLE tasks ADD COLUMN completed_at TEXT",
                "ALTER TABLE tasks ADD COLUMN killed_at TEXT",
                "ALTER TABLE tasks ADD COLUMN digest_text TEXT",
                "ALTER TABLE tasks ADD COLUMN agent TEXT",
                "ALTER TABLE tasks ADD COLUMN project_id TEXT",
                "ALTER TABLE messages ADD COLUMN project_id TEXT",
                "ALTER TABLE messages ADD COLUMN session_id TEXT",
                "ALTER TABLE knowledge_chunks ADD COLUMN categoria TEXT",
            ):
                try:
                    conn.execute(col_sql)
                except Exception:
                    pass
            conn.commit()
        finally:
            conn.close()
        _initialized = True


def execute(sql: str, params: tuple = ()) -> int:
    """INSERT/UPDATE/DELETE — retorna lastrowid (ou rowcount em update)."""
    init_db()
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid if cur.lastrowid else cur.rowcount
    finally:
        conn.close()


def execute_rowcount(sql: str, params: tuple = ()) -> int:
    """INSERT/UPDATE/DELETE — retorna somente rowcount."""
    init_db()
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def query(sql: str, params: tuple = ()) -> list[dict]:
    """SELECT — lista de dicts."""
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def query_one(sql: str, params: tuple = ()) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def count(table: str, where: str = "", params: tuple = ()) -> int:
    sql = f"SELECT COUNT(*) AS n FROM {table}"
    if where:
        sql += f" WHERE {where}"
    r = query_one(sql, params)
    return int(r["n"]) if r else 0
