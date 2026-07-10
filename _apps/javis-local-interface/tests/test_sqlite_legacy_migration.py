"""R4.3A1 — migração SQLite legada antes de índices dependentes."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import repositories as repo  # noqa: E402
import system_health  # noqa: E402


@pytest.fixture()
def isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    db._initialized = False
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "legacy-javis.db")
    yield db.DB_PATH
    db._initialized = False


def _columns(path: Path, table: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def _index_exists(path: Path, name: str) -> bool:
    conn = sqlite3.connect(path)
    try:
        return bool(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
            (name,),
        ).fetchone())
    finally:
        conn.close()


def _legacy_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT,
                created_at TEXT
            );
            INSERT INTO messages(role, content) VALUES('user', 'mensagem legada');

            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ext_id TEXT UNIQUE,
                title TEXT NOT NULL,
                status TEXT
            );
            INSERT INTO tasks(ext_id, title, status) VALUES('legacy-task', 'Tarefa legada', 'pending');

            CREATE TABLE approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT,
                subject TEXT NOT NULL,
                status TEXT
            );
            INSERT INTO approvals(kind, subject, status) VALUES('gate', 'Approval legado', 'pending');

            CREATE TABLE execution_tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT
            );
            INSERT INTO execution_tasks(task_id, status) VALUES('exec_legacy0001', 'draft');
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_init_db_migra_banco_legado_sem_project_id_e_preserva_linhas(isolated_db):
    _legacy_database(isolated_db)

    db.init_db()

    assert "project_id" in _columns(isolated_db, "messages")
    assert "session_id" in _columns(isolated_db, "messages")
    assert "project_id" in _columns(isolated_db, "tasks")
    assert "project_id" in _columns(isolated_db, "approvals")
    assert "project_id" in _columns(isolated_db, "execution_tasks")
    assert "source_commit" in _columns(isolated_db, "execution_tasks")

    assert _index_exists(isolated_db, "idx_messages_project_session")
    assert _index_exists(isolated_db, "idx_execution_tasks_project_status")

    conn = sqlite3.connect(isolated_db)
    try:
        assert conn.execute("SELECT content FROM messages WHERE id=1").fetchone()[0] == "mensagem legada"
        assert conn.execute("SELECT title FROM tasks WHERE ext_id='legacy-task'").fetchone()[0] == "Tarefa legada"
        assert conn.execute("SELECT status FROM execution_tasks WHERE task_id='exec_legacy0001'").fetchone()[0] == "draft"
        assert conn.execute("SELECT project_id FROM messages WHERE id=1").fetchone()[0] == "javes-core"
        assert conn.execute("SELECT project_id FROM tasks WHERE ext_id='legacy-task'").fetchone()[0] == "javes-core"
        assert conn.execute("SELECT project_id FROM execution_tasks WHERE task_id='exec_legacy0001'").fetchone()[0] == "javes-core"
    finally:
        conn.close()


def test_init_db_pode_rodar_duas_vezes_em_banco_legado(isolated_db):
    _legacy_database(isolated_db)

    db.init_db()
    db._initialized = False
    db.init_db()

    assert _index_exists(isolated_db, "idx_messages_project_session")
    assert _index_exists(isolated_db, "idx_execution_tasks_project_status")


def test_banco_novo_cria_execution_tasks_corretamente(isolated_db):
    db.init_db()

    repo.execution_tasks.create(
        task_id="exec_new0001",
        project_id="javes-core",
        executor="claude",
        objective="teste",
        repository_path="/repo",
        source_branch="master",
        work_branch="javes/exec/exec_new0001",
        worktree_path="/worktrees/exec_new0001",
        source_commit="abc123",
    )

    task = repo.execution_tasks.get("exec_new0001", "javes-core")
    assert task is not None
    assert task["project_id"] == "javes-core"
    assert task["source_commit"] == "abc123"


def test_doctor_enxerga_execution_schema_apos_migracao(monkeypatch, tmp_path, isolated_db):
    _legacy_database(isolated_db)
    monkeypatch.setattr(system_health, "JAVIS_ROOT", tmp_path)

    db.init_db()
    data = system_health.snapshot(probe_ollama=False)

    assert data["execution_schema_present"] is True
