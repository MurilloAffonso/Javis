"""Orquestra execução supervisionada até awaiting_review (R4.2B)."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

import db
import repositories as repo
import safe_config

from . import execution_task as et
from ._sanitize import sanitize
from .executor_adapter import AdapterRequest, CodexAdapter, ClaudeCodeAdapter
from .result_collector import ResultCollector
from .test_runner import TestRunner
from .worktree_manager import WorktreeManager


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionService:
    def __init__(self, *, repository=repo, worktree_manager=None,
                 result_collector=None, test_runner=None, adapters=None,
                 enabled: bool | None = None):
        self.repository = repository
        self.worktree_manager = worktree_manager or WorktreeManager()
        self.result_collector = result_collector or ResultCollector()
        self.test_runner = test_runner or TestRunner()
        self.adapters = adapters or {
            "codex": CodexAdapter(),
            "claude": ClaudeCodeAdapter(),
        }
        self.enabled = enabled

    def _enabled(self) -> bool:
        return safe_config.supervised_execution_enabled() if self.enabled is None else bool(self.enabled)

    def _task_exists_elsewhere(self, task_id: str, project_id: str) -> bool:
        try:
            row = db.query_one(
                "SELECT project_id FROM execution_tasks WHERE task_id=? AND project_id<>? LIMIT 1",
                (task_id, project_id),
            )
            return bool(row)
        except Exception:
            return False

    def _transition(self, task: dict, status: str) -> None:
        et.validate_transition(
            task["status"],
            status,
            approval_id=task.get("approval_id"),
            merge_approval_id=task.get("merge_approval_id"),
        )
        self.repository.execution_tasks.update_status(task["task_id"], task["project_id"], status)
        task["status"] = status

    def _fail(self, task: dict, status: str, reason: str, *, worktree_path: str = "",
              stdout: str = "", stderr: str = "", test_report: str = "") -> dict:
        self.repository.execution_tasks.update_status(task["task_id"], task["project_id"], status)
        self.repository.execution_tasks.set_error(task["task_id"], task["project_id"], sanitize(reason, 1000))
        if worktree_path and Path(worktree_path).exists():
            self.result_collector.collect(
                task["task_id"],
                task["project_id"],
                worktree_path,
                stdout=stdout,
                stderr=stderr,
                test_report=test_report,
            )
        return {"status": status, "reason": sanitize(reason, 300), "task_id": task["task_id"]}

    def run(self, task_id: str, project_id: str, *, test_commands: list[list[str]]) -> dict:
        tid = et.validate_task_id(task_id)
        pid = et.normalize_project_id(project_id)
        task = self.repository.execution_tasks.get(tid, pid)
        if not task:
            reason = "project_scope_mismatch" if self._task_exists_elsewhere(tid, pid) else "task_not_found"
            return {"status": "blocked", "reason": reason}
        if task["status"] != et.APPROVED:
            return {"status": "blocked", "reason": "task_not_approved"}
        if not task.get("approval_id"):
            return {"status": "blocked", "reason": "approval_id_required"}
        if not self._enabled():
            return {"status": "blocked", "reason": "supervised_execution_disabled"}

        worktree_path = ""
        try:
            self._transition(task, et.PREPARING_WORKSPACE)
            workspace = self.worktree_manager.create(
                tid,
                task["repository_path"],
                task["source_branch"],
                project_id=pid,
            )
            worktree_path = workspace["worktree_path"]
            self.repository.execution_tasks.set_workspace(
                tid,
                pid,
                work_branch=workspace["work_branch"],
                worktree_path=worktree_path,
                source_commit=workspace.get("source_commit", ""),
                started_at=_utc_now(),
            )
            self._transition(task, et.RUNNING)

            prompt_path = Path(worktree_path).resolve() / ".javes_execution_prompt.txt"
            prompt_path.write_text(task["objective"] or "", encoding="utf-8")
            executor = et.validate_executor(task["executor"])
            adapter = self.adapters[executor]
            adapter_result = adapter.run(AdapterRequest(
                task_id=tid,
                project_id=pid,
                objective=task["objective"] or "",
                worktree_path=worktree_path,
                timeout_seconds=int(task.get("timeout_seconds") or 900),
                prompt_path=str(prompt_path),
                executor=executor,
            ))
            if adapter_result.timed_out:
                return self._fail(task, et.TIMED_OUT, "adapter_timed_out",
                                  worktree_path=worktree_path,
                                  stdout=adapter_result.stdout,
                                  stderr=adapter_result.stderr)
            if adapter_result.status != "success" or adapter_result.exit_code != 0:
                return self._fail(task, et.FAILED, adapter_result.status,
                                  worktree_path=worktree_path,
                                  stdout=adapter_result.stdout,
                                  stderr=adapter_result.stderr)

            self._transition(task, et.TESTING)
            test_report = self.test_runner.run(test_commands, worktree_path)
            if test_report.status == "timed_out":
                return self._fail(task, et.TIMED_OUT, "tests_timed_out",
                                  worktree_path=worktree_path,
                                  stdout=adapter_result.stdout,
                                  stderr=adapter_result.stderr,
                                  test_report=test_report.report)
            if not test_report.ok:
                return self._fail(task, et.FAILED, "tests_failed",
                                  worktree_path=worktree_path,
                                  stdout=adapter_result.stdout,
                                  stderr=adapter_result.stderr,
                                  test_report=test_report.report)

            self.result_collector.collect(
                tid,
                pid,
                worktree_path,
                stdout=adapter_result.stdout,
                stderr=adapter_result.stderr,
                test_report=test_report.report,
            )
            self._transition(task, et.AWAITING_REVIEW)
            return {"status": et.AWAITING_REVIEW, "reason": "", "task_id": tid}
        except Exception as exc:
            return self._fail(task, et.FAILED, str(exc), worktree_path=worktree_path)
