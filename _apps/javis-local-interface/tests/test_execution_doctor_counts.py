"""R4.2A — Doctor mostra SÓ contagens das filas de execução (sem conteúdo)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import repositories as repo  # noqa: E402
import system_health  # noqa: E402
from execution import execution_task as et  # noqa: E402

CORE = "javes-core"


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


def _mk(status: str, objective: str = "SEGREDO_OBJETIVO") -> str:
    tid = et.new_task_id()
    repo.execution_tasks.create(
        task_id=tid, project_id=CORE, executor="codex", objective=objective,
        repository_path="/repo", source_branch="main",
        work_branch=f"javes/exec/{tid}", worktree_path=f"/wt/{tid}", status=status,
    )
    return tid


def test_doctor_conta_filas():
    _mk("pending_approval")
    _mk("awaiting_review")
    _mk("running")
    _mk("testing")
    _mk("approved_for_merge")
    _mk("failed")
    _mk("timed_out")
    conflict = _mk("review_rejected")
    repo.execution_tasks.set_error(conflict, CORE, "merge_conflict")
    _mk("completed")  # terminal, não entra em nenhuma fila ativa
    stats = system_health._execution_stats()
    assert stats["awaiting_execution_approval"] == 1
    assert stats["awaiting_review"] == 1
    assert stats["awaiting_merge_approval"] == 1
    assert stats["failed_execution_tasks"] == 2  # failed + timed_out
    assert stats["execution_schema_present"] is True
    assert stats["supervised_adapters_present"] is True
    assert stats["executions_running"] == 1
    assert stats["executions_testing"] == 1
    assert stats["executions_timed_out"] == 1
    assert stats["executions_awaiting_review"] == 1
    assert stats["approved_for_merge"] == 1
    assert stats["merge_conflicts"] == 1
    assert stats["completed_execution_tasks"] == 1
    assert "preserved_worktrees" in stats


def test_doctor_render_so_contagens_sem_conteudo():
    _mk("pending_approval", objective="NAO_DEVE_VAZAR")
    data = dict(system_health._execution_stats())
    data["providers"] = []  # render_text espera a chave
    # completa mínimos que render_text acessa
    for k, v in {
        "branch": "x", "git_status": "", "python": "3", "sqlite_accessible": True,
        "provider_mode": "local", "rag_embedder": "ollama", "local_token_configured": False,
        "external_adapters": False, "local_actions": False, "vp_effects": False,
        "codex_exec": False, "claude_headless": False, "browser": False,
        "telegram": False, "mcp": False, "current_state_present": True,
        "rag_index_present": False, "pending_approvals": 0, "default_project_id": CORE,
    }.items():
        data.setdefault(k, v)
    text = system_health.render_text(data)
    assert "awaiting_execution_approval:" in text
    assert "failed_execution_tasks:" in text
    assert "supervised_adapters_present:" in text
    assert "executions_running:" in text
    assert "executions_testing:" in text
    assert "executions_timed_out:" in text
    assert "executions_awaiting_review:" in text
    assert "approved_for_merge:" in text
    assert "merge_conflicts:" in text
    assert "completed_execution_tasks:" in text
    assert "preserved_worktrees:" in text
    # nunca imprime objetivo/stdout/diff
    assert "NAO_DEVE_VAZAR" not in text
    assert "objective" not in text.lower()
    assert "stdout" not in text.lower()
    assert "diff" not in text.lower()
