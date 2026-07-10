"""R4.2C1 — merge local controlado após segundo approval.

Usa apenas repositórios Git temporários, sem agentes reais, rede ou repo do Javes.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import repositories as repo  # noqa: E402
from execution import execution_approvals as ea  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution import worktree_manager as wtm  # noqa: E402
from execution.merge_service import ControlledMergeService  # noqa: E402


CORE = "javes-core"
JAMPA = "project:cerebro-jampa"


def _clean_env():
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
                "GIT_OBJECT_DIRECTORY", "GIT_NAMESPACE", "GIT_PREFIX"):
        env.pop(key, None)
    return env


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), shell=False,
                          capture_output=True, text=True, env=_clean_env())


def _has_git() -> bool:
    try:
        return subprocess.run(["git", "--version"], shell=False, capture_output=True).returncode == 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _has_git(), reason="git indisponível")


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


@pytest.fixture
def git_repo(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    assert _git(repo_path, "init").returncode == 0
    assert _git(repo_path, "config", "user.email", "t@example.test").returncode == 0
    assert _git(repo_path, "config", "user.name", "Tester").returncode == 0
    (repo_path / "file.txt").write_text("base\n", encoding="utf-8")
    assert _git(repo_path, "add", "file.txt").returncode == 0
    assert _git(repo_path, "commit", "-m", "base").returncode == 0
    source_branch = _git(repo_path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "master"
    worktree_root = tmp_path / "worktrees"
    manager = wtm.WorktreeManager(allowed_repo_roots=[repo_path], worktree_root=worktree_root)
    return repo_path, source_branch, worktree_root, manager


class FakeCollector:
    def __init__(self):
        self.calls = []

    def collect(self, task_id, project_id, worktree_path, stdout="", stderr="", test_report=""):
        self.calls.append((task_id, project_id, worktree_path, stdout, stderr, test_report))
        return {}


def _merge_approval(task_id: str, project_id: str = CORE) -> int:
    approval_id = repo.approvals.add(
        subject="merge",
        kind="execution_gate",
        task_id=task_id,
        project_id=project_id,
        action=ea.ACTION_MERGE,
        risk_level="high",
    )
    repo.approvals.decide(approval_id, True)
    assert repo.approvals.consume(approval_id) == 1
    return approval_id


def _prepared_task(git_repo, *, status=et.APPROVED_FOR_MERGE, project_id=CORE,
                   merge_approval=True, commit_change=True, source_commit: str | None = None):
    repo_path, source_branch, _, manager = git_repo
    tid = et.new_task_id()
    source_commit = source_commit if source_commit is not None else manager.branch_head(repo_path, source_branch)
    meta = manager.create(tid, repo_path, source_branch, project_id=project_id)
    worktree = Path(meta["worktree_path"])
    if commit_change:
        (worktree / "file.txt").write_text("base\nchange\n", encoding="utf-8")
        assert _git(worktree, "add", "file.txt").returncode == 0
        assert _git(worktree, "commit", "-m", "change").returncode == 0
    merge_approval_id = _merge_approval(tid, project_id) if merge_approval else None
    repo.execution_tasks.create(
        task_id=tid,
        project_id=project_id,
        executor="codex",
        objective="objective",
        repository_path=str(repo_path),
        source_branch=source_branch,
        source_commit=source_commit,
        work_branch=meta["work_branch"],
        worktree_path=meta["worktree_path"],
        status=status,
        approval_id=111,
        merge_approval_id=merge_approval_id,
    )
    return tid, meta


def _service(manager, collector=None, git_runner=None):
    return ControlledMergeService(
        worktree_manager=manager,
        result_collector=collector or FakeCollector(),
        git_runner=git_runner,
    )


def test_sem_approved_for_merge_bloqueia(git_repo):
    _, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo, status=et.AWAITING_REVIEW)
    result = _service(manager).merge(tid, CORE)
    assert result["status"] == "blocked"
    assert result["reason"] == "task_not_approved_for_merge"


def test_sem_merge_approval_id_bloqueia(git_repo):
    _, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo, merge_approval=False)
    result = _service(manager).merge(tid, CORE)
    assert result["status"] == "blocked"
    assert result["reason"] == "merge_approval_id_required"


def test_merge_approval_nao_consumido_bloqueia(git_repo):
    _, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo, merge_approval=False)
    approval_id = repo.approvals.add(
        subject="merge",
        kind="execution_gate",
        task_id=tid,
        project_id=CORE,
        action=ea.ACTION_MERGE,
        risk_level="high",
    )
    repo.approvals.decide(approval_id, True)
    repo.execution_tasks.set_merge_approval(tid, CORE, approval_id)
    result = _service(manager).merge(tid, CORE)
    assert result["status"] == "blocked"
    assert result["reason"] == "merge_approval_not_consumed"


def test_project_id_errado_bloqueia(git_repo):
    _, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo, project_id=CORE)
    result = _service(manager).merge(tid, JAMPA)
    assert result["status"] == "blocked"
    assert result["reason"] == "project_scope_mismatch"


def test_work_branch_master_main_bloqueia(git_repo):
    _, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo)
    repo.execution_tasks.set_workspace(tid, CORE, work_branch="master", worktree_path=str(manager.worktree_path_for(tid)))
    result = _service(manager).merge(tid, CORE)
    assert result["status"] == "blocked"
    assert result["reason"] == "protected_work_branch"


def test_source_branch_mudou_bloqueia(git_repo):
    repo_path, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo)
    (repo_path / "other.txt").write_text("moved\n", encoding="utf-8")
    assert _git(repo_path, "add", "other.txt").returncode == 0
    assert _git(repo_path, "commit", "-m", "source moved").returncode == 0
    result = _service(manager).merge(tid, CORE)
    assert result["status"] == "blocked"
    assert result["reason"] == "source_branch_moved"


def test_source_commit_ausente_bloqueia(git_repo):
    _, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo, source_commit="")

    result = _service(manager).merge(tid, CORE)

    assert result["status"] == "blocked"
    assert result["reason"] == "source_commit_required"


def test_repo_com_alteracao_rastreada_bloqueia(git_repo):
    repo_path, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo)
    (repo_path / "file.txt").write_text("dirty\n", encoding="utf-8")
    result = _service(manager).merge(tid, CORE)
    assert result["status"] == "blocked"
    assert result["reason"] == "tracked_changes_unstaged"


def test_merge_limpo_vai_merged_completed_e_remove_worktree(git_repo):
    _, _, _, manager = git_repo
    collector = FakeCollector()
    tid, meta = _prepared_task(git_repo)
    result = _service(manager, collector=collector).merge(tid, CORE)
    task = repo.execution_tasks.get(tid, CORE)
    assert result["status"] == et.COMPLETED
    assert task["status"] == et.COMPLETED
    assert not Path(meta["worktree_path"]).exists()
    assert collector.calls


def test_merge_nao_faz_push_e_usa_shell_false(git_repo):
    _, _, _, manager = git_repo
    tid, _ = _prepared_task(git_repo)
    seen = []

    def runner(argv, **kwargs):
        seen.append((argv, kwargs))
        return subprocess.run(argv, **kwargs)

    result = _service(manager, git_runner=runner).merge(tid, CORE)
    assert result["status"] == et.COMPLETED
    assert all("push" not in call[0] for call in seen)
    assert all(call[1]["shell"] is False for call in seen)


def test_conflito_e_abortado_e_preserva_worktree(git_repo):
    repo_path, _, _, manager = git_repo
    tid, meta = _prepared_task(git_repo)
    collector = FakeCollector()
    (repo_path / "file.txt").write_text("base\nmain conflict\n", encoding="utf-8")
    assert _git(repo_path, "add", "file.txt").returncode == 0
    assert _git(repo_path, "commit", "-m", "main conflict").returncode == 0
    repo.execution_tasks.set_source_commit(tid, CORE, manager.branch_head(repo_path, _git(repo_path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()))

    result = _service(manager, collector=collector).merge(tid, CORE)
    task = repo.execution_tasks.get(tid, CORE)
    assert result["status"] == et.REVIEW_REJECTED
    assert task["last_error"] == "merge_conflict"
    assert Path(meta["worktree_path"]).exists()
    assert collector.calls
    assert not (repo_path / ".git" / "MERGE_HEAD").exists()


def test_erro_nao_remove_evidencia(git_repo):
    _, _, _, manager = git_repo
    tid, meta = _prepared_task(git_repo)

    def runner(argv, **kwargs):
        if argv[1] == "rev-list":
            raise RuntimeError("boom token=abc")
        return subprocess.run(argv, **kwargs)

    result = _service(manager, git_runner=runner).merge(tid, CORE)
    task = repo.execution_tasks.get(tid, CORE)
    assert result["status"] == et.FAILED
    assert Path(meta["worktree_path"]).exists()
    assert "abc" not in task["last_error"]
