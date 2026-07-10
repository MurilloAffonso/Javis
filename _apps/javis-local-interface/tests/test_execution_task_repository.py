"""R4.1 — repositório de execution_tasks: sempre escopado por task_id+project_id."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import repositories as repo  # noqa: E402

CORE = "javes-core"
JAMPA = "project:cerebro-jampa"


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


def _mk(task_id: str, project_id: str, status: str = "draft"):
    repo.execution_tasks.create(
        task_id=task_id, project_id=project_id, executor="codex",
        objective="obj", repository_path="/repo", source_branch="main",
        work_branch=f"javes/exec/{task_id}", worktree_path=f"/wt/{task_id}",
        status=status,
    )


def test_create_e_get_escopado():
    _mk("exec_aaaa1111", CORE)
    got = repo.execution_tasks.get("exec_aaaa1111", CORE)
    assert got and got["executor"] == "codex"
    # project errado → None (isolamento)
    assert repo.execution_tasks.get("exec_aaaa1111", JAMPA) is None


def test_list_by_project_isola():
    _mk("exec_aaaa1111", CORE)
    _mk("exec_bbbb2222", JAMPA)
    core = repo.execution_tasks.list_by_project(CORE)
    jampa = repo.execution_tasks.list_by_project(JAMPA)
    assert [t["task_id"] for t in core] == ["exec_aaaa1111"]
    assert [t["task_id"] for t in jampa] == ["exec_bbbb2222"]


def test_list_by_project_filtra_status():
    _mk("exec_aaaa1111", CORE, status="draft")
    _mk("exec_bbbb2222", CORE, status="running")
    running = repo.execution_tasks.list_by_project(CORE, status="running")
    assert [t["task_id"] for t in running] == ["exec_bbbb2222"]


def test_update_status_e_set_helpers():
    _mk("exec_cccc3333", CORE)
    assert repo.execution_tasks.update_status("exec_cccc3333", CORE, "running") == 1
    repo.execution_tasks.set_workspace("exec_cccc3333", CORE,
                                       work_branch="javes/exec/exec_cccc3333",
                                       worktree_path="/wt/exec_cccc3333")
    repo.execution_tasks.set_error("exec_cccc3333", CORE, "boom")
    repo.execution_tasks.set_result_paths("exec_cccc3333", CORE, diff_path="/d.diff")
    got = repo.execution_tasks.get("exec_cccc3333", CORE)
    assert got["status"] == "running"
    assert got["last_error"] == "boom"
    assert got["diff_path"] == "/d.diff"


def test_update_status_project_errado_nao_altera():
    _mk("exec_dddd4444", CORE)
    # tentar alterar com project errado → 0 linhas
    assert repo.execution_tasks.update_status("exec_dddd4444", JAMPA, "running") == 0
    assert repo.execution_tasks.get("exec_dddd4444", CORE)["status"] == "draft"


def test_count_active_ignora_terminais():
    _mk("exec_eeee5555", CORE, status="running")
    _mk("exec_ffff6666", CORE, status="completed")
    assert repo.execution_tasks.count_active() == 1
