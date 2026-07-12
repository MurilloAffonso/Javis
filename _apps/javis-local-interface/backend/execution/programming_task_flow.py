"""Fluxo supervisionado R4.4B1 para tasks reais já admitidas."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import db
import repositories as repo
import safe_config

from . import execution_approvals
from . import execution_task as et
from ._sanitize import sanitize, sanitize_truncated
from .commit_service import INTERNAL_PROMPT_NAME
from .execution_facade import ExecutionFacade
from .executor_adapter import AdapterRequest, ClaudeCodeAdapter, CodexAdapter
from .merge_service import ControlledMergeService
from .programming_task_policy import (
    PolicyViolation,
    ProgrammingChangePolicy,
    ProgrammingTestProfiles,
    RealTaskCommitService,
    build_internal_prompt,
)
from .programming_task_spec import SpecValidationError, validate_snapshot
from .project_execution_registry import ProjectExecutionRegistry
from .result_collector import ResultCollector
from .worktree_manager import WorktreeManager


CORE_PROJECT_ID = "javes-core"
APPROVE_START_PHRASE = "APROVAR TAREFA REAL"
RUN_PHRASE = "EXECUTAR TAREFA REAL"
APPROVE_MERGE_PHRASE = "APROVAR MERGE REAL"
MERGE_PHRASE = "EXECUTAR MERGE REAL"
REJECT_PHRASE = "REJEITAR TAREFA REAL"
REJECT_MERGE_PHRASE = "REJEITAR MERGE REAL"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProgrammingTaskFlow:
    def __init__(
        self,
        *,
        registry: ProjectExecutionRegistry | None = None,
        repository=repo,
        worktree_manager: WorktreeManager | None = None,
        result_collector: ResultCollector | None = None,
        adapters: dict | None = None,
        change_policy: ProgrammingChangePolicy | None = None,
        test_profiles: ProgrammingTestProfiles | None = None,
        commit_service: RealTaskCommitService | None = None,
        merge_service: ControlledMergeService | None = None,
        monotonic=time.monotonic,
    ):
        self.registry = registry or ProjectExecutionRegistry()
        self.repo = repository
        project = self.registry.require(CORE_PROJECT_ID)
        self.worktree_manager = worktree_manager or WorktreeManager(
            allowed_repo_roots=[project.repository_path]
        )
        self.result_collector = result_collector or ResultCollector()
        self.adapters = adapters or {"claude": ClaudeCodeAdapter(), "codex": CodexAdapter()}
        self.change_policy = change_policy or ProgrammingChangePolicy()
        self.test_profiles = test_profiles or ProgrammingTestProfiles()
        self.commit_service = commit_service or RealTaskCommitService(self.change_policy)
        self.merge_service = merge_service or ControlledMergeService(
            repository=repository, worktree_manager=self.worktree_manager,
            result_collector=self.result_collector,
        )
        self.facade = ExecutionFacade(
            repository=repository, merge_service=self.merge_service,
            result_collector=self.result_collector,
            repository_path=project.repository_path, source_branch=project.source_branch,
        )
        self.monotonic = monotonic

    def _event(self, task_id: str, event_type: str, reason: str = "", **metadata) -> None:
        try:
            self.repo.task_events.add_event(
                task_id, event_type, "system", sanitize(reason or event_type, 300),
                metadata={key: value for key, value in metadata.items()
                          if isinstance(value, (str, int, bool))},
            )
        except Exception:
            pass

    def _blocked(self, reason: str, task_id: str = "", status: str = "blocked") -> dict:
        safe = sanitize(reason, 120)
        if task_id:
            self._event(task_id, "real_programming_blocked", safe)
        return {"status": status, "reason": safe, **({"task_id": task_id} if task_id else {})}

    def _task(self, task_id: str) -> dict | None:
        try:
            tid = et.validate_task_id(task_id)
        except Exception:
            return None
        return self.repo.execution_tasks.get(tid, CORE_PROJECT_ID)

    def _verified(self, task: dict) -> tuple[dict, dict]:
        snapshot = self.repo.execution_task_specs.get(task["task_id"], task["project_id"])
        if not snapshot:
            raise SpecValidationError("spec_not_found")
        validated = validate_snapshot(
            snapshot.get("snapshot_json") or "", snapshot.get("spec_hash") or "", self.registry
        )
        spec = validated.data
        project = self.registry.get(spec["project_id"])
        if not project:
            raise SpecValidationError("project_not_allowed")
        if (task.get("project_id") != project.project_id
                or task.get("executor") != spec["executor"]
                or Path(task.get("repository_path") or "").resolve() != project.repository_path.resolve()
                or task.get("source_branch") != project.source_branch
                or task.get("objective") != spec["objective"]):
            raise SpecValidationError("spec_hash_mismatch")
        return spec, snapshot

    def _context_or_blocked(self, task: dict) -> tuple[dict, dict] | dict:
        try:
            return self._verified(task)
        except SpecValidationError as exc:
            return self._blocked(exc.reason, task["task_id"])
        except Exception:
            return self._blocked("spec_hash_mismatch", task["task_id"])

    def _flag_real(self, task_id: str = "") -> dict | None:
        if not safe_config.real_programming_tasks_enabled():
            return self._blocked("real_programming_tasks_disabled", task_id)
        return None

    def approve_start(self, task_id: str, approval_id: int, confirm: str) -> dict:
        disabled = self._flag_real(task_id)
        if disabled:
            return disabled
        if confirm != APPROVE_START_PHRASE:
            return self._blocked("confirmation_phrase_required", task_id)
        task = self._task(task_id)
        if not task:
            return self._blocked("spec_not_found")
        if task["status"] != et.PENDING_APPROVAL:
            return self._blocked("invalid_state", task["task_id"])
        context = self._context_or_blocked(task)
        if isinstance(context, dict):
            return context
        spec, snapshot = context
        approval = self.repo.approvals.get(int(approval_id))
        if not approval or approval.get("status") != "pending" or approval.get("consumed_at"):
            return self._blocked("approval_not_pending", task["task_id"])
        if (approval.get("task_id") != task["task_id"]
                or approval.get("project_id") != CORE_PROJECT_ID
                or approval.get("action") != execution_approvals.ACTION_START):
            return self._blocked("approval_scope_mismatch", task["task_id"])
        if (approval.get("executor") != spec["executor"]
                or approval.get("spec_hash") != snapshot["spec_hash"]):
            return self._blocked("spec_hash_mismatch", task["task_id"])
        et.validate_transition(task["status"], et.APPROVED, approval_id=int(approval_id))
        conn = db.get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            current = conn.execute(
                "SELECT status FROM approvals WHERE id=? AND task_id=? AND project_id=?",
                (int(approval_id), task["task_id"], CORE_PROJECT_ID),
            ).fetchone()
            current_task = conn.execute(
                "SELECT status FROM execution_tasks WHERE task_id=? AND project_id=?",
                (task["task_id"], CORE_PROJECT_ID),
            ).fetchone()
            if not current or current["status"] != "pending" or not current_task or current_task["status"] != et.PENDING_APPROVAL:
                conn.rollback()
                return self._blocked("approval_not_pending", task["task_id"])
            updated = conn.execute(
                "UPDATE approvals SET status='approved', approved_by='programming_task_cli', "
                "decided_at=datetime('now'), consumed_at=datetime('now'), updated_at=datetime('now') "
                "WHERE id=? AND task_id=? AND project_id=? AND action=? "
                "AND executor=? AND spec_hash=? AND status='pending' AND consumed_at IS NULL",
                (int(approval_id), task["task_id"], CORE_PROJECT_ID,
                 execution_approvals.ACTION_START, spec["executor"], snapshot["spec_hash"]),
            ).rowcount
            transitioned = conn.execute(
                "UPDATE execution_tasks SET status=?, approval_id=? "
                "WHERE task_id=? AND project_id=? AND status=? AND executor=?",
                (et.APPROVED, int(approval_id), task["task_id"], CORE_PROJECT_ID,
                 et.PENDING_APPROVAL, spec["executor"]),
            ).rowcount
            if updated != 1 or transitioned != 1:
                conn.rollback()
                return self._blocked("approval_not_pending", task["task_id"])
            conn.commit()
        except Exception:
            conn.rollback()
            return self._blocked("approval_scope_mismatch", task["task_id"])
        finally:
            conn.close()
        self._event(task["task_id"], "real_programming_start_approved",
                    "Approval execution.start consumido", approval_id=int(approval_id))
        return {"status": et.APPROVED, "task_id": task["task_id"],
                "project_id": CORE_PROJECT_ID, "executor": spec["executor"],
                "spec_hash": snapshot["spec_hash"]}

    def _claim_run(self, task: dict, spec: dict | None = None,
                   snapshot: dict | None = None) -> bool:
        spec = spec or {"executor": task.get("executor"), "objective": task.get("objective")}
        snapshot = snapshot or self.repo.execution_task_specs.get(task["task_id"], CORE_PROJECT_ID) or {}
        conn = db.get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            snapshot = conn.execute(
                "SELECT 1 FROM execution_task_specs WHERE task_id=? AND project_id=? AND spec_hash=?",
                (task["task_id"], CORE_PROJECT_ID, snapshot.get("spec_hash") or ""),
            ).fetchone()
            if not snapshot:
                conn.rollback()
                return False
            changed = conn.execute(
                "UPDATE execution_tasks SET status=? WHERE task_id=? AND project_id=? AND status=? "
                "AND executor=? AND objective=?",
                (et.PREPARING_WORKSPACE, task["task_id"], CORE_PROJECT_ID, et.APPROVED,
                 spec["executor"], spec["objective"]),
            ).rowcount
            if changed != 1:
                conn.rollback()
                return False
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def _fail_run(self, task: dict, reason: str, *, stdout: str = "", stderr: str = "",
                  test_report: str = "") -> dict:
        safe = sanitize(reason, 120)
        try:
            self.repo.execution_tasks.update_status(task["task_id"], CORE_PROJECT_ID, et.FAILED)
            self.repo.execution_tasks.set_error(task["task_id"], CORE_PROJECT_ID, safe)
        except Exception:
            pass
        worktree = task.get("worktree_path") or ""
        if worktree and Path(worktree).is_dir():
            try:
                prompt = Path(worktree) / INTERNAL_PROMPT_NAME
                if prompt.exists() or prompt.is_symlink():
                    prompt.unlink()
            except Exception:
                pass
            try:
                self.result_collector.collect(
                    task["task_id"], CORE_PROJECT_ID, worktree, stdout=stdout,
                    stderr=stderr, test_report=test_report or safe,
                )
            except Exception:
                pass
        self._event(task["task_id"], "real_programming_failed", safe)
        return self._blocked(safe, task["task_id"], status=et.FAILED)

    def run(self, task_id: str, confirm: str) -> dict:
        disabled = self._flag_real(task_id)
        if disabled:
            return disabled
        if not safe_config.supervised_execution_enabled():
            return self._blocked("supervised_execution_disabled", task_id)
        if confirm != RUN_PHRASE:
            return self._blocked("confirmation_phrase_required", task_id)
        task = self._task(task_id)
        if not task:
            return self._blocked("spec_not_found")
        if task["status"] != et.APPROVED:
            return self._blocked("invalid_state", task["task_id"])
        context = self._context_or_blocked(task)
        if isinstance(context, dict):
            return context
        spec, snapshot = context
        active = self.repo.execution_task_specs.active_for_project(CORE_PROJECT_ID)
        if active and active.get("task_id") != task["task_id"]:
            return self._blocked("active_programming_task_exists", task["task_id"])
        if not self._claim_run(task, spec, snapshot):
            return self._blocked("invalid_state", task["task_id"])
        task["status"] = et.PREPARING_WORKSPACE
        started = self.monotonic()
        adapter_result = None
        test_report = ""
        try:
            project = self.registry.require(CORE_PROJECT_ID)
            workspace = self.worktree_manager.create(
                task["task_id"], project.repository_path, project.source_branch,
                project_id=CORE_PROJECT_ID,
            )
            task.update(workspace)
            self.repo.execution_tasks.set_workspace(
                task["task_id"], CORE_PROJECT_ID, work_branch=workspace["work_branch"],
                worktree_path=workspace["worktree_path"],
                source_commit=workspace["source_commit"], started_at=_utc_now(),
            )
            et.validate_transition(et.PREPARING_WORKSPACE, et.RUNNING)
            self.repo.execution_tasks.update_status(task["task_id"], CORE_PROJECT_ID, et.RUNNING)
            task["status"] = et.RUNNING
            prompt = Path(workspace["worktree_path"]) / INTERNAL_PROMPT_NAME
            prompt.write_text(build_internal_prompt(spec), encoding="utf-8")
            adapter = self.adapters[spec["executor"]]
            adapter_result = adapter.run(AdapterRequest(
                task_id=task["task_id"], project_id=CORE_PROJECT_ID,
                objective=build_internal_prompt(spec),
                worktree_path=workspace["worktree_path"],
                timeout_seconds=spec["limits"]["max_duration_seconds"],
                prompt_path=str(prompt), executor=spec["executor"],
            ))
            elapsed = self.monotonic() - started
            if adapter_result.timed_out or elapsed > spec["limits"]["max_duration_seconds"]:
                return self._fail_run(task, "max_duration_exceeded",
                                      stdout=adapter_result.stdout, stderr=adapter_result.stderr)
            if adapter_result.status != "success" or adapter_result.exit_code != 0:
                return self._fail_run(task, sanitize(adapter_result.status, 80),
                                      stdout=adapter_result.stdout, stderr=adapter_result.stderr)
            prompt.unlink(missing_ok=True)
            initial_changes = self.change_policy.validate(task, spec, committed=False)
            et.validate_transition(et.RUNNING, et.TESTING)
            self.repo.execution_tasks.update_status(task["task_id"], CORE_PROJECT_ID, et.TESTING)
            task["status"] = et.TESTING
            remaining = max(1, int(spec["limits"]["max_duration_seconds"] - elapsed))
            tests = self.test_profiles.run(
                spec["test_profile"], Path(workspace["worktree_path"]),
                initial_changes.stage_paths, remaining,
            )
            test_report = tests.report
            if self.monotonic() - started > spec["limits"]["max_duration_seconds"]:
                return self._fail_run(task, "max_duration_exceeded",
                                      stdout=adapter_result.stdout, stderr=adapter_result.stderr,
                                      test_report=test_report)
            if not tests.ok:
                return self._fail_run(task, "tests_failed", stdout=adapter_result.stdout,
                                      stderr=adapter_result.stderr, test_report=test_report)
            self.change_policy.validate(task, spec, committed=False)
            committed = self.commit_service.commit(task, spec)
            if not committed.commit_hash:
                return self._fail_run(task, "no_new_commit", test_report=test_report)
            collected = self.result_collector.collect(
                task["task_id"], CORE_PROJECT_ID, workspace["worktree_path"],
                stdout=adapter_result.stdout, stderr=adapter_result.stderr,
                test_report="status=passed\n" + test_report,
            )
            if int(collected.get("changed_count") or 0) < 1:
                return self._fail_run(task, "no_new_commit", test_report=test_report)
            et.validate_transition(et.TESTING, et.AWAITING_REVIEW)
            self.repo.execution_tasks.update_status(task["task_id"], CORE_PROJECT_ID,
                                                    et.AWAITING_REVIEW)
            self._event(task["task_id"], "real_programming_awaiting_review",
                        "Execução, testes e commit concluídos",
                        changed_files_count=committed.changed_count)
            return {"status": et.AWAITING_REVIEW, "task_id": task["task_id"],
                    "project_id": CORE_PROJECT_ID, "executor": spec["executor"],
                    "spec_hash": snapshot["spec_hash"]}
        except PolicyViolation as exc:
            return self._fail_run(
                task, exc.reason,
                stdout=getattr(adapter_result, "stdout", ""),
                stderr=getattr(adapter_result, "stderr", ""), test_report=test_report,
            )
        except Exception as exc:
            return self._fail_run(task, sanitize(str(exc), 120) or "invalid_state",
                                  stdout=getattr(adapter_result, "stdout", ""),
                                  stderr=getattr(adapter_result, "stderr", ""),
                                  test_report=test_report)

    def _evidence(self, task: dict) -> tuple[dict, str]:
        summary: dict = {}
        tests = "not_run"
        try:
            result = self.result_collector.results_dir_for(task["task_id"])
            result_file = result / "result.json"
            tests_file = result / "tests.txt"
            if result_file.exists():
                raw = json.loads(result_file.read_text(encoding="utf-8"))
                summary = {
                    "changed_count": int(raw.get("changed_count") or 0),
                    "diff_stat": sanitize_truncated(raw.get("diff_stat") or "", 1200),
                }
            if tests_file.exists():
                content = tests_file.read_text(encoding="utf-8", errors="replace")
                tests = "passed" if "status=passed" in content else "failed"
        except Exception:
            pass
        return summary, tests

    def status(self, task_id: str) -> dict:
        task = self._task(task_id)
        if not task:
            return self._blocked("spec_not_found")
        snapshot = self.repo.execution_task_specs.get(task["task_id"], CORE_PROJECT_ID)
        summary, tests = self._evidence(task)
        try:
            preserved = bool(self.worktree_manager.validate_existing(task["task_id"]).get("exists"))
        except Exception:
            preserved = False
        return {
            "task_id": task["task_id"], "project_id": CORE_PROJECT_ID,
            "executor": task.get("executor") or "", "status": task.get("status") or "",
            "spec_hash": (snapshot or {}).get("spec_hash") or "", "tests": tests,
            "changed_files_count": int(summary.get("changed_count") or 0),
            "diff_stat": summary.get("diff_stat") or "",
            "evidencias_presentes": bool(task.get("result_path") or task.get("diff_path")
                                         or task.get("test_report_path")),
            "worktree_preservada": preserved,
        }

    def _clean_worktree(self, task: dict) -> bool:
        worktree = Path(task.get("worktree_path") or "").resolve()
        if not worktree.is_dir():
            return False
        for args in (["diff", "--quiet"], ["diff", "--cached", "--quiet"]):
            rc, _, _ = self.change_policy._git(worktree, args)
            if rc != 0:
                return False
        rc, out, _ = self.change_policy._git(
            worktree, ["ls-files", "--others", "--exclude-standard"]
        )
        return rc == 0 and not out.strip()

    def _has_new_commit(self, task: dict) -> bool:
        worktree = Path(task.get("worktree_path") or "").resolve()
        source = (task.get("source_commit") or "").strip()
        if not source:
            return False
        rc, out, _ = self.change_policy._git(
            worktree, ["rev-list", "--count", f"{source}..HEAD"]
        )
        try:
            return rc == 0 and int(out.strip() or "0") > 0
        except ValueError:
            return False

    def request_merge(self, task_id: str) -> dict:
        disabled = self._flag_real(task_id)
        if disabled:
            return disabled
        task = self._task(task_id)
        if not task or task.get("status") != et.AWAITING_REVIEW:
            return self._blocked("invalid_state", task_id)
        context = self._context_or_blocked(task)
        if isinstance(context, dict):
            return context
        spec, snapshot = context
        summary, tests = self._evidence(task)
        if tests != "passed":
            return self._blocked("tests_failed", task["task_id"])
        if not self._has_new_commit(task):
            return self._blocked("no_new_commit", task["task_id"])
        if not self._clean_worktree(task):
            return self._blocked("dirty_worktree", task["task_id"])
        try:
            self.change_policy.validate(task, spec, committed=True)
        except PolicyViolation as exc:
            return self._blocked(exc.reason, task["task_id"])
        approval = self.facade.request_merge_approval(
            task["task_id"], CORE_PROJECT_ID, executor=spec["executor"],
            spec_hash=snapshot["spec_hash"],
        )
        return {"status": et.AWAITING_REVIEW, "task_id": task["task_id"],
                "approval_id": approval["merge_approval_id"],
                "project_id": CORE_PROJECT_ID, "executor": spec["executor"],
                "spec_hash": snapshot["spec_hash"]}

    def approve_merge(self, task_id: str, approval_id: int, confirm: str) -> dict:
        disabled = self._flag_real(task_id)
        if disabled:
            return disabled
        if confirm != APPROVE_MERGE_PHRASE:
            return self._blocked("confirmation_phrase_required", task_id)
        task = self._task(task_id)
        if not task or task.get("status") != et.AWAITING_REVIEW:
            return self._blocked("invalid_state", task_id)
        context = self._context_or_blocked(task)
        if isinstance(context, dict):
            return context
        spec, snapshot = context
        approval = self.repo.approvals.get(int(approval_id))
        if not approval or approval.get("status") != "pending" or approval.get("consumed_at"):
            return self._blocked("approval_not_pending", task["task_id"])
        if (approval.get("task_id") != task["task_id"]
                or approval.get("project_id") != CORE_PROJECT_ID
                or approval.get("action") != execution_approvals.ACTION_MERGE):
            return self._blocked("approval_scope_mismatch", task["task_id"])
        if (approval.get("executor") != spec["executor"]
                or approval.get("spec_hash") != snapshot["spec_hash"]):
            return self._blocked("spec_hash_mismatch", task["task_id"])
        et.validate_transition(task["status"], et.APPROVED_FOR_MERGE,
                               merge_approval_id=int(approval_id))
        conn = db.get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            updated = conn.execute(
                "UPDATE approvals SET status='approved', approved_by='programming_task_cli', "
                "decided_at=datetime('now'), consumed_at=datetime('now'), updated_at=datetime('now') "
                "WHERE id=? AND task_id=? AND project_id=? AND action=? "
                "AND executor=? AND spec_hash=? AND status='pending' AND consumed_at IS NULL",
                (int(approval_id), task["task_id"], CORE_PROJECT_ID,
                 execution_approvals.ACTION_MERGE, spec["executor"], snapshot["spec_hash"]),
            ).rowcount
            transitioned = conn.execute(
                "UPDATE execution_tasks SET status=?, merge_approval_id=? "
                "WHERE task_id=? AND project_id=? AND status=? AND executor=?",
                (et.APPROVED_FOR_MERGE, int(approval_id), task["task_id"],
                 CORE_PROJECT_ID, et.AWAITING_REVIEW, spec["executor"]),
            ).rowcount
            if updated != 1 or transitioned != 1:
                conn.rollback()
                return self._blocked("approval_not_pending", task["task_id"])
            conn.commit()
        except Exception:
            conn.rollback()
            return self._blocked("approval_scope_mismatch", task["task_id"])
        finally:
            conn.close()
        self._event(task["task_id"], "real_programming_merge_approved",
                    "Approval execution.merge consumido", approval_id=int(approval_id))
        return {"status": et.APPROVED_FOR_MERGE, "task_id": task["task_id"],
                "project_id": CORE_PROJECT_ID, "executor": spec["executor"],
                "spec_hash": snapshot["spec_hash"]}

    def merge(self, task_id: str, confirm: str) -> dict:
        disabled = self._flag_real(task_id)
        if disabled:
            return disabled
        if confirm != MERGE_PHRASE:
            return self._blocked("confirmation_phrase_required", task_id)
        task = self._task(task_id)
        if not task or task.get("status") != et.APPROVED_FOR_MERGE:
            return self._blocked("invalid_state", task_id)
        try:
            project = self.registry.require(CORE_PROJECT_ID)
            current = self.worktree_manager.branch_head(project.repository_path,
                                                        project.source_branch)
        except Exception:
            return self._blocked("project_not_allowed", task["task_id"])
        if not task.get("source_commit") or current != task.get("source_commit"):
            return self._blocked("source_branch_moved", task["task_id"])
        context = self._context_or_blocked(task)
        if isinstance(context, dict):
            return context
        spec, _ = context
        try:
            self.change_policy.validate(task, spec, committed=True)
        except PolicyViolation as exc:
            return self._blocked(exc.reason, task["task_id"])
        if not self._clean_worktree(task):
            return self._blocked("dirty_worktree", task["task_id"])
        result = self.facade.perform_merge(task["task_id"], CORE_PROJECT_ID)
        reason = result.get("reason") or ""
        if reason and "conflict" in reason:
            result["reason"] = "merge_conflict"
        return {key: value for key, value in result.items()
                if key in {"status", "reason", "task_id", "commit"}}

    def reject(self, task_id: str, confirm: str) -> dict:
        disabled = self._flag_real(task_id)
        if disabled:
            return disabled
        if confirm != REJECT_PHRASE:
            return self._blocked("confirmation_phrase_required", task_id)
        task = self._task(task_id)
        if not task:
            return self._blocked("spec_not_found")
        if task["status"] == et.REVIEW_REJECTED:
            return {"status": et.REVIEW_REJECTED, "task_id": task["task_id"]}
        if task["status"] != et.AWAITING_REVIEW:
            return self._blocked("invalid_state", task["task_id"])
        et.validate_transition(task["status"], et.REVIEW_REJECTED)
        self.repo.execution_tasks.update_status(task["task_id"], CORE_PROJECT_ID,
                                                et.REVIEW_REJECTED)
        self._event(task["task_id"], "real_programming_rejected",
                    "Revisão rejeitada; evidências preservadas")
        return {"status": et.REVIEW_REJECTED, "task_id": task["task_id"]}

    def reject_merge(self, task_id: str, confirm: str) -> dict:
        disabled = self._flag_real(task_id)
        if disabled:
            return disabled
        if confirm != REJECT_MERGE_PHRASE:
            return self._blocked("confirmation_phrase_required", task_id)
        task = self._task(task_id)
        if not task:
            return self._blocked("spec_not_found")
        if task["status"] == et.REVIEW_REJECTED:
            return {"status": et.REVIEW_REJECTED, "task_id": task["task_id"]}
        if task["status"] != et.APPROVED_FOR_MERGE:
            return self._blocked("invalid_state", task["task_id"])
        et.validate_transition(task["status"], et.REVIEW_REJECTED,
                               merge_approval_id=task.get("merge_approval_id"))
        self.repo.execution_tasks.update_status(task["task_id"], CORE_PROJECT_ID,
                                                et.REVIEW_REJECTED)
        self._event(task["task_id"], "real_programming_merge_rejected",
                    "Merge rejeitado; approval e evidências preservados")
        return {"status": et.REVIEW_REJECTED, "task_id": task["task_id"]}
