"""Fachada única do executor supervisionado (R4.2C2).

API, Orchestrator e Command Center devem passar por este módulo. A fachada não
executa agentes por conta própria: cria tarefas, amarra approvals persistidos e
chama os serviços R4 apenas quando a ação explícita é solicitada.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gate
import repositories as repo

from . import execution_approvals
from . import execution_task as et
from ._sanitize import sanitize_truncated
from .execution_service import ExecutionService
from .merge_service import ControlledMergeService
from .result_collector import ResultCollector


JAVIS_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SOURCE_BRANCH = "master"


class ExecutionFacade:
    def __init__(
        self,
        *,
        repository=repo,
        execution_service: ExecutionService | None = None,
        merge_service: ControlledMergeService | None = None,
        result_collector: ResultCollector | None = None,
        repository_path: str | Path | None = None,
        source_branch: str = DEFAULT_SOURCE_BRANCH,
    ):
        self.repository = repository
        self.execution_service = execution_service or ExecutionService(repository=repository)
        self.merge_service = merge_service or ControlledMergeService(repository=repository)
        self.result_collector = result_collector or ResultCollector()
        self.repository_path = str(Path(repository_path or JAVIS_ROOT).resolve())
        self.source_branch = (source_branch or DEFAULT_SOURCE_BRANCH).strip() or DEFAULT_SOURCE_BRANCH

    def create_task(
        self,
        *,
        objective: str,
        project_id: str,
        executor: str = "codex",
        timeout_seconds: int = et.DEFAULT_TIMEOUT_SECONDS,
    ) -> dict:
        pid = et.normalize_project_id(project_id)
        task_id = et.new_task_id()
        executor_id = et.validate_executor(executor)
        objective_text = sanitize_truncated(objective or "", 8000).strip()
        if not objective_text:
            return {"status": "blocked", "reason": "objective_required"}
        work_branch = et.branch_for(task_id)
        self.repository.execution_tasks.create(
            task_id=task_id,
            project_id=pid,
            executor=executor_id,
            objective=objective_text,
            repository_path=self.repository_path,
            source_branch=self.source_branch,
            work_branch=work_branch,
            worktree_path="",
            status=et.DRAFT,
            timeout_seconds=int(timeout_seconds or et.DEFAULT_TIMEOUT_SECONDS),
        )
        self._event(task_id, "execution_task_created", "Tarefa supervisionada criada",
                    {"project_id": pid, "executor": executor_id})
        return self._task_payload(self.repository.execution_tasks.get(task_id, pid))

    def create_task_and_request_start(
        self,
        *,
        objective: str,
        project_id: str,
        executor: str = "codex",
        timeout_seconds: int = et.DEFAULT_TIMEOUT_SECONDS,
    ) -> dict:
        created = self.create_task(
            objective=objective,
            project_id=project_id,
            executor=executor,
            timeout_seconds=timeout_seconds,
        )
        if created.get("status") == "blocked":
            return created
        approval = self.request_start_approval(created["task_id"], created["project_id"])
        task = self.get_task(created["task_id"], created["project_id"])
        return {
            **task,
            "status": approval["status"],
            "approval_id": approval["approval_id"],
            "message": "Tarefa criada e aguardando aprovação para execução.",
        }

    def get_task(self, task_id: str, project_id: str) -> dict:
        task = self._load_task(task_id, project_id)
        if not task:
            return self._not_found_or_mismatch(task_id, project_id)
        return self._task_payload(task)

    def list_tasks(self, project_id: str, status: str | None = None) -> list[dict]:
        pid = et.normalize_project_id(project_id)
        rows = self.repository.execution_tasks.list_by_project(pid, status or "")
        return [self._task_payload(row) for row in rows]

    def request_start_approval(self, task_id: str, project_id: str) -> dict:
        return execution_approvals.request_execution_start(task_id, project_id)

    def approve_start(self, task_id: str, project_id: str, approval_id: int) -> dict:
        return execution_approvals.approve_execution_start(task_id, project_id, approval_id)

    def start_execution(self, task_id: str, project_id: str, test_commands: list[list[str]]) -> dict:
        return self.execution_service.run(task_id, project_id, test_commands=test_commands or [])

    def request_merge_approval(self, task_id: str, project_id: str) -> dict:
        return execution_approvals.request_merge(task_id, project_id)

    def approve_merge(self, task_id: str, project_id: str, approval_id: int) -> dict:
        return execution_approvals.approve_merge(task_id, project_id, approval_id)

    def perform_merge(self, task_id: str, project_id: str) -> dict:
        return self.merge_service.merge(task_id, project_id)

    def cancel_task(self, task_id: str, project_id: str) -> dict:
        task = self._load_task(task_id, project_id)
        if not task:
            return self._not_found_or_mismatch(task_id, project_id)
        if task["status"] not in {et.DRAFT, et.PENDING_APPROVAL, et.APPROVED}:
            return {"status": "blocked", "reason": "cancel_not_allowed", "task_id": task["task_id"]}
        et.validate_transition(task["status"], et.CANCELED)
        self.repository.execution_tasks.update_status(task["task_id"], task["project_id"], et.CANCELED)
        self._event(task["task_id"], "execution_task_canceled",
                    "Tarefa supervisionada cancelada; evidências preservadas",
                    {"project_id": task["project_id"]})
        return {"status": et.CANCELED, "task_id": task["task_id"], "project_id": task["project_id"]}

    def result_summary(self, task_id: str, project_id: str) -> dict:
        task = self._load_task(task_id, project_id)
        if not task:
            return self._not_found_or_mismatch(task_id, project_id)
        summary = self._safe_result_summary(task)
        diff_text = self._safe_result_file(task["task_id"], "diff.patch", limit=12000)
        tests_text = self._safe_result_file(task["task_id"], "tests.txt", limit=12000)
        return {
            "status": "ok",
            "task_id": task["task_id"],
            "project_id": task["project_id"],
            "summary": summary,
            "diff": diff_text,
            "tests": tests_text,
        }

    def _load_task(self, task_id: str, project_id: str) -> dict | None:
        tid = et.validate_task_id(task_id)
        pid = et.normalize_project_id(project_id)
        return self.repository.execution_tasks.get(tid, pid)

    def _not_found_or_mismatch(self, task_id: str, project_id: str) -> dict:
        tid = et.validate_task_id(task_id)
        pid = et.normalize_project_id(project_id)
        exists = self.repository.db.query_one(
            "SELECT project_id FROM execution_tasks WHERE task_id=? AND project_id<>? LIMIT 1",
            (tid, pid),
        ) if hasattr(self.repository, "db") else None
        if exists:
            return {"status": "blocked", "reason": "project_scope_mismatch"}
        return {"status": "not_found", "reason": "task_not_found"}

    def _task_payload(self, task: dict | None) -> dict:
        if not task:
            return {"status": "not_found", "reason": "task_not_found"}
        summary = self._safe_result_summary(task)
        approval_id = task.get("approval_id")
        merge_approval_id = task.get("merge_approval_id")
        return {
            "task_id": task["task_id"],
            "project_id": task["project_id"],
            "executor": task.get("executor") or "",
            "status": task.get("status") or "",
            "created_at": task.get("created_at") or "",
            "updated_at": task.get("updated_at") or "",
            "started_at": task.get("started_at") or "",
            "finished_at": task.get("finished_at") or "",
            "timeout_seconds": task.get("timeout_seconds") or et.DEFAULT_TIMEOUT_SECONDS,
            "execution_approval": "approved" if approval_id else "pending",
            "merge_approval": "approved" if merge_approval_id else "pending",
            "approval_id": approval_id,
            "merge_approval_id": merge_approval_id,
            "risk": "high",
            "tests_status": "passed" if task.get("status") in {et.AWAITING_REVIEW, et.APPROVED_FOR_MERGE, et.MERGED, et.COMPLETED} else "not_run",
            "changed_files_count": summary.get("changed_count", 0),
            "has_result": bool(summary),
            "actions": self._actions_for(task.get("status") or ""),
        }

    def _actions_for(self, status: str) -> list[str]:
        return {
            et.DRAFT: ["request_start_approval", "cancel"],
            et.PENDING_APPROVAL: ["open_approval", "cancel"],
            et.APPROVED: ["start", "cancel"],
            et.AWAITING_REVIEW: ["view_result", "request_merge_approval", "reject"],
            et.APPROVED_FOR_MERGE: ["perform_merge"],
            et.FAILED: ["view_result", "cancel"],
            et.TIMED_OUT: ["view_result", "cancel"],
            et.REVIEW_REJECTED: ["view_result", "cancel"],
            et.COMPLETED: ["view_result"],
        }.get(status, [])

    def _safe_result_summary(self, task: dict) -> dict[str, Any]:
        result_path = task.get("result_path") or ""
        if not result_path:
            return {}
        try:
            expected = self.result_collector.results_dir_for(task["task_id"]) / "result.json"
            if Path(result_path).resolve() != expected.resolve() or not expected.exists():
                return {}
            data = json.loads(expected.read_text(encoding="utf-8"))
            return {
                "changed_count": int(data.get("changed_count") or 0),
                "changed_files": [str(x)[:240] for x in (data.get("changed_files") or [])[:50]],
                "diff_stat": sanitize_truncated(data.get("diff_stat") or "", 4000),
                "diff_truncated": bool(data.get("diff_truncated")),
                "collected_at": data.get("collected_at") or "",
            }
        except Exception:
            return {}

    def _safe_result_file(self, task_id: str, filename: str, *, limit: int) -> str:
        try:
            path = self.result_collector.results_dir_for(task_id) / filename
            if path.parent != self.result_collector.results_dir_for(task_id) or not path.exists():
                return ""
            return sanitize_truncated(path.read_text(encoding="utf-8", errors="replace"), limit)
        except Exception:
            return ""

    def _event(self, task_id: str, event_type: str, message: str, metadata: dict | None = None) -> None:
        try:
            self.repository.task_events.add_event(task_id, event_type, "system", message, metadata=metadata)
        except Exception:
            pass


def create_task_and_request_start(objective: str, project_id: str, executor: str = "codex") -> dict:
    return ExecutionFacade().create_task_and_request_start(
        objective=objective,
        project_id=project_id or gate.CORE_SCOPE,
        executor=executor,
    )
