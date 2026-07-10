"""Merge local controlado após segundo approval (R4.2C1)."""
from __future__ import annotations

from pathlib import Path
import subprocess

import db
import repositories as repo

from . import execution_task as et
from . import execution_approvals
from ._gitcmd import clean_git_env
from ._sanitize import sanitize, sanitize_truncated
from .result_collector import ResultCollector
from .worktree_manager import WorktreeManager


_TIMEOUT = 60
_PROTECTED_BRANCHES = {"master", "main"}


class ControlledMergeService:
    def __init__(self, *, repository=repo, worktree_manager=None,
                 result_collector=None, git_runner=None, timeout_seconds: int = _TIMEOUT):
        self.repository = repository
        self.worktree_manager = worktree_manager or WorktreeManager()
        self.result_collector = result_collector or ResultCollector()
        self.git_runner = git_runner or subprocess.run
        self.timeout_seconds = timeout_seconds

    def _blocked(self, reason: str) -> dict:
        return {"status": "blocked", "reason": sanitize(reason, 300)}

    def _task_exists_elsewhere(self, task_id: str, project_id: str) -> bool:
        try:
            row = db.query_one(
                "SELECT project_id FROM execution_tasks WHERE task_id=? AND project_id<>? LIMIT 1",
                (task_id, project_id),
            )
            return bool(row)
        except Exception:
            return False

    def _approval_consumed_for_merge(self, task: dict) -> bool:
        approval_id = task.get("merge_approval_id")
        if not approval_id:
            return False
        approval = self.repository.approvals.get(int(approval_id))
        if not approval:
            return False
        return (
            (approval.get("task_id") or "") == task["task_id"]
            and (approval.get("project_id") or "") == task["project_id"]
            and (approval.get("action") or "") == execution_approvals.ACTION_MERGE
            and (approval.get("status") or "") == "approved"
            and bool(approval.get("consumed_at"))
        )

    def _run_git(self, cwd: Path, args: list[str]) -> tuple[int, str, str]:
        proc = self.git_runner(
            ["git", *args],
            cwd=str(cwd),
            shell=False,
            env=clean_git_env(),
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        return int(proc.returncode), proc.stdout or "", proc.stderr or ""

    def _fail(self, task: dict, reason: str, *, worktree_path: str = "",
              status: str = et.FAILED, stdout: str = "", stderr: str = "") -> dict:
        safe_reason = sanitize(reason, 1000)
        self.repository.execution_tasks.update_status(task["task_id"], task["project_id"], status)
        self.repository.execution_tasks.set_error(task["task_id"], task["project_id"], safe_reason)
        if worktree_path and Path(worktree_path).exists():
            self.result_collector.collect(
                task["task_id"],
                task["project_id"],
                worktree_path,
                stdout=stdout,
                stderr=stderr,
                test_report=safe_reason,
            )
        return {"status": status, "reason": sanitize(reason, 300), "task_id": task["task_id"]}

    def _assert_clean_repo(self, repository_path: Path) -> str:
        for args, reason in (
            (["diff", "--quiet"], "tracked_changes_unstaged"),
            (["diff", "--cached", "--quiet"], "tracked_changes_staged"),
        ):
            rc, _, _ = self._run_git(repository_path, args)
            if rc != 0:
                return reason
        rc, out, err = self._run_git(repository_path, ["rev-parse", "--git-dir"])
        if rc != 0:
            return sanitize(err, 200) or "git_dir_unavailable"
        git_dir = (repository_path / out.strip()) if out.strip() else (repository_path / ".git")
        for marker in ("MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"):
            if (git_dir / marker).exists():
                return "git_operation_in_progress"
        for marker in ("rebase-merge", "rebase-apply"):
            if (git_dir / marker).exists():
                return "git_operation_in_progress"
        return ""

    def merge(self, task_id: str, project_id: str) -> dict:
        tid = et.validate_task_id(task_id)
        pid = et.normalize_project_id(project_id)
        task = self.repository.execution_tasks.get(tid, pid)
        if not task:
            reason = "project_scope_mismatch" if self._task_exists_elsewhere(tid, pid) else "task_not_found"
            return self._blocked(reason)
        if task["status"] != et.APPROVED_FOR_MERGE:
            return self._blocked("task_not_approved_for_merge")
        if not task.get("merge_approval_id"):
            return self._blocked("merge_approval_id_required")
        if not self._approval_consumed_for_merge(task):
            return self._blocked("merge_approval_not_consumed")

        try:
            repository_path = self.worktree_manager.validate_repository_path(task["repository_path"])
            source_branch = (task.get("source_branch") or "").strip()
            raw_work_branch = (task.get("work_branch") or "").strip()
            if raw_work_branch in _PROTECTED_BRANCHES:
                return self._blocked("protected_work_branch")
            work_branch = et.validate_work_branch(raw_work_branch)

            worktree_path = Path(task.get("worktree_path") or "").resolve()
            expected = self.worktree_manager.validate_existing(tid)
            if not expected.get("exists") or Path(expected["worktree_path"]).resolve() != worktree_path:
                return self._blocked("worktree_scope_mismatch")
            if not expected.get("is_expected_branch"):
                return self._blocked("unexpected_worktree_branch")

            clean_reason = self._assert_clean_repo(repository_path)
            if clean_reason:
                return self._blocked(clean_reason)

            expected_source_commit = (task.get("source_commit") or "").strip()
            current_source_commit = self.worktree_manager.branch_head(repository_path, source_branch)
            if expected_source_commit and current_source_commit != expected_source_commit:
                return self._blocked("source_branch_moved")

            rc, out, err = self._run_git(repository_path, ["rev-list", "--count", f"{source_branch}..{work_branch}"])
            if rc != 0:
                return self._fail(task, "work_branch_unreadable", worktree_path=str(worktree_path), stderr=err)
            if int((out or "0").strip() or "0") < 1:
                return self._blocked("work_branch_without_new_commit")

            rc, _, err = self._run_git(repository_path, ["checkout", source_branch])
            if rc != 0:
                return self._fail(task, "checkout_source_failed", worktree_path=str(worktree_path), stderr=err)

            rc, out, err = self._run_git(repository_path, ["merge", "--no-ff", "--no-edit", work_branch])
            if rc != 0:
                self._run_git(repository_path, ["merge", "--abort"])
                return self._fail(
                    task,
                    "merge_conflict",
                    worktree_path=str(worktree_path),
                    status=et.REVIEW_REJECTED,
                    stdout=out,
                    stderr=err,
                )

            et.validate_transition(task["status"], et.MERGED, merge_approval_id=task.get("merge_approval_id"))
            self.repository.execution_tasks.update_status(tid, pid, et.MERGED)
            task["status"] = et.MERGED
            self.result_collector.collect(
                tid,
                pid,
                str(worktree_path),
                stdout=sanitize_truncated(out, 4000),
                stderr=sanitize_truncated(err, 4000),
                test_report="merge_completed",
            )
            et.validate_transition(et.MERGED, et.COMPLETED, merge_approval_id=task.get("merge_approval_id"))
            self.repository.execution_tasks.update_status(tid, pid, et.COMPLETED)
            self.worktree_manager.remove(tid, status=et.COMPLETED)
            return {"status": et.COMPLETED, "reason": "", "task_id": tid}
        except Exception as exc:
            worktree_path = task.get("worktree_path") or ""
            return self._fail(task, str(exc), worktree_path=worktree_path)
