"""Commit local controlado da worktree supervisionada (R4.3B1)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import execution_task as et
from ._gitcmd import run_git
from ._sanitize import sanitize, sanitize_truncated


INTERNAL_PROMPT_NAME = ".javes_execution_prompt.txt"
INTERNAL_PREFIX = ".javes_"
SENSITIVE_MARKERS = (".env", "token", "credential", "credentials", "secret", "key")


class CommitError(et.ExecutionError):
    pass


@dataclass(frozen=True)
class CommitResult:
    status: str
    commit_hash: str
    changed_count: int
    changed_files: tuple[str, ...]
    reason: str = ""


def _resolve(path) -> Path:
    return Path(path).resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return path == root


def _safe_relpath(raw: str, worktree: Path) -> str:
    rel = (raw or "").strip().strip('"').replace("\\", "/")
    if not rel:
        raise CommitError("empty_change_path")
    rel_path = Path(rel)
    if rel_path.is_absolute():
        raise CommitError("absolute_change_path")
    if ".." in rel_path.parts:
        raise CommitError("parent_traversal_change_path")
    lowered_parts = tuple(part.lower() for part in rel_path.parts)
    if any(part.startswith(INTERNAL_PREFIX) for part in lowered_parts):
        raise CommitError("internal_artifact_change_path")
    joined = "/".join(lowered_parts)
    if any(marker in lowered_parts or marker in joined for marker in SENSITIVE_MARKERS):
        raise CommitError("sensitive_change_path")
    target = _resolve(worktree / rel_path)
    if target.exists() and not _is_within(target, worktree):
        raise CommitError("change_path_outside_worktree")
    parent = _resolve(target.parent)
    if not _is_within(parent, worktree):
        raise CommitError("change_parent_outside_worktree")
    return rel


class ControlledCommitService:
    def __init__(self, git_runner=run_git):
        self.git_runner = git_runner

    def _git(self, cwd: Path, args: list[str], timeout: int = 30) -> tuple[int, str, str]:
        return self.git_runner(cwd, args, timeout=timeout)

    def cleanup_internal_prompt(self, task_id: str, project_id: str, worktree_path) -> dict:
        et.validate_task_id(task_id)
        et.normalize_project_id(project_id)
        worktree = _resolve(worktree_path)
        prompt = _resolve(worktree / INTERNAL_PROMPT_NAME)
        if prompt.parent != worktree or prompt.name != INTERNAL_PROMPT_NAME:
            return {"removed": False, "reason": "internal_prompt_path_invalid"}
        if not prompt.exists() and not prompt.is_symlink():
            return {"removed": False, "reason": "not_found"}
        if prompt.is_dir() and not prompt.is_symlink():
            return {"removed": False, "reason": "internal_prompt_not_file"}
        prompt.unlink()
        return {"removed": True, "reason": ""}

    def _ensure_worktree(self, worktree: Path) -> None:
        if not worktree.is_dir():
            raise CommitError("worktree_missing")
        rc, root, err = self._git(worktree, ["rev-parse", "--show-toplevel"])
        if rc != 0:
            raise CommitError("git_worktree_unavailable: " + sanitize(err, 200))
        if _resolve(root.strip()) != worktree:
            raise CommitError("git_root_mismatch")

    def _validate_branch(self, task: dict, worktree: Path) -> str:
        work_branch = et.validate_work_branch(task.get("work_branch") or "")
        rc, active, err = self._git(worktree, ["rev-parse", "--abbrev-ref", "HEAD"])
        if rc != 0:
            raise CommitError("active_branch_unavailable: " + sanitize(err, 200))
        active_branch = active.strip()
        if active_branch in {"master", "main"}:
            raise CommitError("work_branch_is_main")
        if active_branch != work_branch:
            raise CommitError("work_branch_mismatch")
        return work_branch

    def _validate_source_commit(self, task: dict, worktree: Path) -> str:
        source_commit = (task.get("source_commit") or "").strip()
        if not source_commit:
            raise CommitError("source_commit_required")
        rc, _, err = self._git(worktree, ["merge-base", "--is-ancestor", source_commit, "HEAD"])
        if rc != 0:
            raise CommitError("head_not_derived_from_source_commit: " + sanitize(err, 200))
        return source_commit

    def _collect_names(self, worktree: Path) -> list[str]:
        commands = (
            ["diff", "--name-only"],
            ["diff", "--cached", "--name-only"],
            ["ls-files", "--others", "--exclude-standard"],
        )
        names: list[str] = []
        seen: set[str] = set()
        for args in commands:
            rc, out, err = self._git(worktree, args)
            if rc != 0:
                raise CommitError("change_collection_failed: " + sanitize(err, 200))
            for line in out.splitlines():
                try:
                    rel = _safe_relpath(line, worktree)
                except CommitError:
                    continue
                if rel in seen:
                    continue
                seen.add(rel)
                names.append(rel)
        return names

    def collect_valid_changes(self, task: dict) -> tuple[str, ...]:
        et.validate_task_id(task.get("task_id"))
        et.normalize_project_id(task.get("project_id"))
        worktree = _resolve(task.get("worktree_path") or "")
        self._ensure_worktree(worktree)
        self._validate_branch(task, worktree)
        self._validate_source_commit(task, worktree)
        return tuple(self._collect_names(worktree))

    def commit_task_changes(self, task: dict) -> CommitResult:
        tid = et.validate_task_id(task.get("task_id"))
        et.normalize_project_id(task.get("project_id"))
        worktree = _resolve(task.get("worktree_path") or "")
        self._ensure_worktree(worktree)
        self._validate_branch(task, worktree)
        self._validate_source_commit(task, worktree)

        rc, before, err = self._git(worktree, ["rev-parse", "HEAD"])
        if rc != 0:
            raise CommitError("head_unavailable: " + sanitize(err, 200))
        before_head = before.strip()

        changes = self._collect_names(worktree)
        if not changes:
            raise CommitError("no_valid_changes")

        rc, _, err = self._git(worktree, ["add", "--", *changes])
        if rc != 0:
            raise CommitError("git_add_failed: " + sanitize(err, 300))

        message = f"javes({tid}): resultado da execução supervisionada"
        rc, _, err = self._git(worktree, ["commit", "-m", message], timeout=60)
        if rc != 0:
            raise CommitError("git_commit_failed: " + sanitize_truncated(err, 500))

        rc, after, err = self._git(worktree, ["rev-parse", "HEAD"])
        if rc != 0:
            raise CommitError("head_after_commit_unavailable: " + sanitize(err, 200))
        after_head = after.strip()
        if not after_head or after_head == before_head:
            raise CommitError("commit_head_unchanged")

        return CommitResult(
            status="committed",
            commit_hash=after_head,
            changed_count=len(changes),
            changed_files=tuple(changes),
        )
