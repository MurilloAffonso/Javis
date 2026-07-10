"""R4.2A — Doctor mostra SÓ contagens das filas de execução (sem conteúdo)."""
from __future__ import annotations

import sys
import subprocess
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


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), shell=False, capture_output=True, text=True)


def _mk_repo(path: Path) -> tuple[str, str]:
    path.mkdir(parents=True, exist_ok=True)
    assert _git(path, "init").returncode == 0
    assert _git(path, "config", "user.email", "tester@example.local").returncode == 0
    assert _git(path, "config", "user.name", "Javes Test").returncode == 0
    (path / "a.txt").write_text("a\n", encoding="utf-8")
    assert _git(path, "add", "a.txt").returncode == 0
    assert _git(path, "commit", "-m", "initial").returncode == 0
    source_commit = _git(path, "rev-parse", "HEAD").stdout.strip()
    (path / "b.txt").write_text("b\n", encoding="utf-8")
    assert _git(path, "add", "b.txt").returncode == 0
    assert _git(path, "commit", "-m", "work").returncode == 0
    return source_commit, _git(path, "rev-parse", "HEAD").stdout.strip()


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
    assert "awaiting_review_without_commit" in stats
    assert "internal_prompt_artifacts" in stats
    assert "execution_commits_ready" in stats


def test_doctor_conta_commit_ready_e_prompt_interno(tmp_path):
    wt_ready = tmp_path / "ready"
    source_commit, _ = _mk_repo(wt_ready)
    ready = _mk("awaiting_review")
    repo.execution_tasks.set_workspace(
        ready, CORE, work_branch=f"javes/exec/{ready}",
        worktree_path=str(wt_ready), source_commit=source_commit,
    )

    wt_stale = tmp_path / "stale"
    source_stale, _ = _mk_repo(wt_stale)
    (wt_stale / ".javes_execution_prompt.txt").write_text("interno", encoding="utf-8")
    stale = _mk("awaiting_review")
    repo.execution_tasks.set_workspace(
        stale, CORE, work_branch=f"javes/exec/{stale}",
        worktree_path=str(wt_stale), source_commit=_git(wt_stale, "rev-parse", "HEAD").stdout.strip(),
    )

    stats = system_health._execution_stats()

    assert stats["execution_commits_ready"] >= 1
    assert stats["awaiting_review_without_commit"] >= 1
    assert stats["internal_prompt_artifacts"] >= 1


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
    assert "awaiting_review_without_commit:" in text
    assert "internal_prompt_artifacts:" in text
    assert "execution_commits_ready:" in text
    # nunca imprime objetivo/stdout/diff
    assert "NAO_DEVE_VAZAR" not in text
    assert "objective" not in text.lower()
    assert "stdout" not in text.lower()
    assert "diff" not in text.lower()
