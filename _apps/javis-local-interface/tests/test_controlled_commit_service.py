"""R4.3B1 — commit local controlado da worktree supervisionada."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from execution import execution_task as et  # noqa: E402
from execution.commit_service import (  # noqa: E402
    CommitError,
    ControlledCommitService,
    INTERNAL_PROMPT_NAME,
)


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in (
        "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_NAMESPACE", "GIT_PREFIX",
    ):
        env.pop(key, None)
    return env


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        shell=False,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )


def _has_git() -> bool:
    try:
        return subprocess.run(["git", "--version"], capture_output=True, shell=False).returncode == 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _has_git(), reason="git indisponível")


class RecordingGit:
    def __init__(self):
        self.commands: list[list[str]] = []

    def __call__(self, cwd, args, timeout=30):
        self.commands.append(list(args))
        proc = _git(Path(cwd), *args)
        return proc.returncode, proc.stdout or "", proc.stderr or ""


def _make_repo(path: Path) -> tuple[str, str]:
    path.mkdir(parents=True, exist_ok=True)
    assert _git(path, "init").returncode == 0
    assert _git(path, "config", "user.email", "tester@example.local").returncode == 0
    assert _git(path, "config", "user.name", "Javes Test").returncode == 0
    (path / "README.md").write_text("# repo\n", encoding="utf-8")
    assert _git(path, "add", "README.md").returncode == 0
    assert _git(path, "commit", "-m", "initial").returncode == 0
    source_commit = _git(path, "rev-parse", "HEAD").stdout.strip()
    task_id = "exec_a834333b2799772a"
    work_branch = et.branch_for(task_id)
    assert _git(path, "checkout", "-b", work_branch).returncode == 0
    return source_commit, task_id


def _task(repo_path: Path, source_commit: str, task_id: str = "exec_a834333b2799772a") -> dict:
    return {
        "task_id": task_id,
        "project_id": "javes-core",
        "worktree_path": str(repo_path),
        "work_branch": et.branch_for(task_id),
        "source_commit": source_commit,
    }


@pytest.fixture()
def repo_path(tmp_path) -> Path:
    return tmp_path / "repo"


def test_untracked_valido_e_detectado_commitado_sem_alterar_source(repo_path):
    source_commit, task_id = _make_repo(repo_path)
    (repo_path / "docs").mkdir()
    smoke = repo_path / "docs" / "EXECUTION_SMOKE_TEST.md"
    smoke.write_text(
        "# Javes Supervised Execution Smoke Test\n\n"
        "- Executor supervisionado executado em worktree.\n"
        "- Nenhuma alteração feita diretamente na master.\n",
        encoding="utf-8",
    )
    (repo_path / INTERNAL_PROMPT_NAME).write_text("interno", encoding="utf-8")

    recorder = RecordingGit()
    service = ControlledCommitService(git_runner=recorder)
    cleanup = service.cleanup_internal_prompt(task_id, "javes-core", repo_path)
    result = service.commit_task_changes(_task(repo_path, source_commit, task_id))

    assert cleanup["removed"] is True
    assert not (repo_path / INTERNAL_PROMPT_NAME).exists()
    assert result.status == "committed"
    assert result.changed_files == ("docs/EXECUTION_SMOKE_TEST.md",)
    assert result.changed_count == 1
    assert _git(repo_path, "rev-parse", "master").stdout.strip() == source_commit
    assert _git(repo_path, "rev-parse", "HEAD").stdout.strip() != source_commit
    committed_files = _git(repo_path, "show", "--name-only", "--format=", "HEAD").stdout
    assert "docs/EXECUTION_SMOKE_TEST.md" in committed_files
    assert INTERNAL_PROMPT_NAME not in committed_files
    assert ["add", "--", "docs/EXECUTION_SMOKE_TEST.md"] in recorder.commands
    assert not any(cmd[:2] == ["add", "."] for cmd in recorder.commands)
    assert not any(cmd[:2] == ["add", "-A"] or cmd[:2] == ["add", "--all"] for cmd in recorder.commands)
    assert not any(cmd and cmd[0] == "push" for cmd in recorder.commands)


def test_tracked_modificado_e_deletado_sao_stageados_explicitamente(repo_path):
    source_commit, task_id = _make_repo(repo_path)
    (repo_path / "README.md").write_text("# mudou\n", encoding="utf-8")
    recorder = RecordingGit()
    result = ControlledCommitService(git_runner=recorder).commit_task_changes(
        _task(repo_path, source_commit, task_id)
    )

    assert result.changed_files == ("README.md",)
    assert ["add", "--", "README.md"] in recorder.commands


def test_no_valid_changes_falha_fechado(repo_path):
    source_commit, task_id = _make_repo(repo_path)
    with pytest.raises(CommitError, match="no_valid_changes"):
        ControlledCommitService().commit_task_changes(_task(repo_path, source_commit, task_id))


def test_recusa_master_main(repo_path):
    source_commit, task_id = _make_repo(repo_path)
    assert _git(repo_path, "checkout", "master").returncode == 0
    with pytest.raises(CommitError, match="work_branch_is_main"):
        ControlledCommitService().commit_task_changes(_task(repo_path, source_commit, task_id))


def test_recusa_head_nao_derivado_do_source_commit(repo_path):
    source_commit, task_id = _make_repo(repo_path)
    tree = _git(repo_path, "write-tree").stdout.strip()
    orphan = _git(repo_path, "commit-tree", tree, "-m", "orphan").stdout.strip()
    (repo_path / "a.txt").write_text("a\n", encoding="utf-8")
    with pytest.raises(CommitError, match="head_not_derived_from_source_commit"):
        ControlledCommitService().commit_task_changes(_task(repo_path, orphan, task_id))


def test_recusa_paths_sensiveis_e_prompt_interno(repo_path):
    source_commit, task_id = _make_repo(repo_path)
    (repo_path / ".env").write_text("SECRET=x\n", encoding="utf-8")
    (repo_path / "api_token.txt").write_text("x\n", encoding="utf-8")
    (repo_path / INTERNAL_PROMPT_NAME).write_text("prompt\n", encoding="utf-8")

    with pytest.raises(CommitError, match="no_valid_changes"):
        ControlledCommitService().commit_task_changes(_task(repo_path, source_commit, task_id))

    assert (repo_path / INTERNAL_PROMPT_NAME).exists()


def test_recusa_symlink_externo(repo_path, tmp_path):
    source_commit, task_id = _make_repo(repo_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("fora\n", encoding="utf-8")
    try:
        (repo_path / "link.txt").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlink indisponível neste ambiente: {exc}")

    with pytest.raises(CommitError, match="no_valid_changes"):
        ControlledCommitService().commit_task_changes(_task(repo_path, source_commit, task_id))


def test_utf8_permanece_valido(repo_path):
    source_commit, task_id = _make_repo(repo_path)
    path = repo_path / "docs"
    path.mkdir()
    utf8_file = path / "acentos.md"
    expected = "alteração válida em UTF-8\n"
    utf8_file.write_text(expected, encoding="utf-8")

    ControlledCommitService().commit_task_changes(_task(repo_path, source_commit, task_id))

    assert utf8_file.read_text(encoding="utf-8") == expected
