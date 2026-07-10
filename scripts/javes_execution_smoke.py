from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


os.environ.setdefault("JAVIS_SKIP_DOTENV", "1")

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "_apps" / "javis-local-interface" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import db  # noqa: E402
import repositories as repo  # noqa: E402
import safe_config  # noqa: E402
from execution import execution_approvals  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution._sanitize import sanitize_truncated  # noqa: E402
from execution.execution_facade import ExecutionFacade  # noqa: E402


CORE_PROJECT_ID = "javes-core"
MAX_TIMEOUT_SECONDS = 300
APPROVE_PHRASE = "APROVAR TESTE CONTROLADO"
RUN_PHRASE = "EXECUTAR TESTE CONTROLADO"
SMOKE_FILE = "docs/EXECUTION_SMOKE_TEST.md"
SMOKE_CONTENT = """# Javes Supervised Execution Smoke Test

- Executor supervisionado executado em worktree.
- Nenhuma alteração feita diretamente na master.
- Merge não realizado automaticamente.
"""
SMOKE_OBJECTIVE = (
    "R4.3A SMOKE TEST CONTROLADO.\n"
    f"Crie ou atualize somente `{SMOKE_FILE}` na worktree com exatamente este conteúdo:\n\n"
    f"{SMOKE_CONTENT}\n"
    "Não altere outros arquivos. Não faça commit, merge ou push."
)
SMOKE_TEST_COMMANDS = [
    ["python", "-m", "py_compile", "_apps/javis-local-interface/backend/execution/execution_task.py"],
]
_ACTIVE_STATUSES = tuple(sorted(et.ALL_STATES - et.TERMINAL_STATES))
_EXECUTED_STATUSES = {
    et.PREPARING_WORKSPACE,
    et.RUNNING,
    et.TESTING,
    et.AWAITING_REVIEW,
    et.APPROVED_FOR_MERGE,
    et.MERGED,
    et.COMPLETED,
    et.FAILED,
    et.TIMED_OUT,
    et.REVIEW_REJECTED,
}


def make_facade() -> ExecutionFacade:
    return ExecutionFacade()


def _print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _blocked(reason: str, **extra) -> dict:
    return {"status": "blocked", "reason": sanitize_truncated(reason, 300), **extra}


def _public_text(value: object, limit: int = 1200) -> str:
    text = sanitize_truncated(value, limit)
    root = str(ROOT)
    text = text.replace(root, "[REDACTED_PATH]")
    text = text.replace(root.replace("\\", "/"), "[REDACTED_PATH]")
    text = re.sub(r"(?i)\b[A-Z]:[\\/][^\s]+", "[REDACTED_PATH]", text)
    return text


def _load_task(task_id: str) -> dict | None:
    return repo.execution_tasks.get(et.validate_task_id(task_id), CORE_PROJECT_ID)


def _schema_present() -> bool:
    return bool(db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='execution_tasks'"
    ))


def _active_smoke_tasks(exclude_task_id: str = "") -> list[dict]:
    placeholders = ",".join("?" for _ in _ACTIVE_STATUSES)
    rows = db.query(
        f"SELECT * FROM execution_tasks WHERE project_id=? AND objective=? "
        f"AND status IN ({placeholders}) ORDER BY created_at DESC",
        (CORE_PROJECT_ID, SMOKE_OBJECTIVE, *_ACTIVE_STATUSES),
    )
    return [row for row in rows if row.get("task_id") != exclude_task_id]


def _running_smoke_tasks(exclude_task_id: str = "") -> list[dict]:
    rows = db.query(
        "SELECT * FROM execution_tasks WHERE project_id=? AND objective=? "
        "AND status IN ('preparing_workspace','running','testing')",
        (CORE_PROJECT_ID, SMOKE_OBJECTIVE),
    )
    return [row for row in rows if row.get("task_id") != exclude_task_id]


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        shell=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


def _repo_clean(repository_path: str) -> str:
    repo_path = Path(repository_path).resolve()
    if not repo_path.is_dir():
        return "repository_path_invalid"
    if _git(["diff", "--quiet"], repo_path).returncode != 0:
        return "tracked_changes_unstaged"
    if _git(["diff", "--cached", "--quiet"], repo_path).returncode != 0:
        return "tracked_changes_staged"
    git_dir = _git(["rev-parse", "--git-dir"], repo_path)
    if git_dir.returncode != 0:
        return "git_dir_unavailable"
    git_path = repo_path / (git_dir.stdout or ".git").strip()
    for marker in ("MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"):
        if (git_path / marker).exists():
            return "git_operation_in_progress"
    return ""


def _approval_consumed(task: dict) -> bool:
    approval_id = task.get("approval_id")
    if not approval_id:
        return False
    approval = repo.approvals.get(int(approval_id))
    return bool(
        approval
        and approval.get("status") == "approved"
        and approval.get("consumed_at")
        and approval.get("task_id") == task["task_id"]
        and approval.get("project_id") == CORE_PROJECT_ID
        and approval.get("action") == execution_approvals.ACTION_START
    )


def _executor_available(executor: str) -> str:
    if executor == "codex":
        if not shutil.which("codex"):
            return "codex_binary_unavailable"
        if os.environ.get("JAVIS_CODEX_SANDBOX_VERIFIED", "") != "workspace-write":
            return "secure_codex_sandbox_unavailable"
    elif executor == "claude":
        if not shutil.which("claude"):
            return "claude_binary_unavailable"
    else:
        return "executor_invalid"
    return ""


def _preflight_run(task: dict) -> dict:
    if not (ROOT / "_estado" / "CURRENT_STATE.md").exists():
        return _blocked("current_state_missing")
    if not _schema_present():
        return _blocked("execution_schema_missing")
    if os.environ.get("JAVIS_ENABLE_SUPERVISED_EXEC", "") != "1":
        return _blocked("supervised_execution_disabled")
    if not safe_config.supervised_execution_enabled():
        return _blocked("supervised_execution_disabled")
    if task.get("project_id") != CORE_PROJECT_ID:
        return _blocked("project_id_mismatch")
    if task.get("objective") != SMOKE_OBJECTIVE:
        return _blocked("not_smoke_task")
    if task.get("status") in _EXECUTED_STATUSES or task.get("worktree_path"):
        return _blocked("task_already_executed")
    if task.get("status") != et.APPROVED:
        return _blocked("task_not_approved")
    if not _approval_consumed(task):
        return _blocked("approval_not_consumed")
    if int(task.get("timeout_seconds") or 0) > MAX_TIMEOUT_SECONDS:
        return _blocked("timeout_above_smoke_limit")
    try:
        et.validate_work_branch(task.get("work_branch") or "")
    except Exception:
        return _blocked("work_branch_invalid")
    if _running_smoke_tasks(exclude_task_id=task["task_id"]):
        return _blocked("another_smoke_running")
    clean_reason = _repo_clean(task.get("repository_path") or "")
    if clean_reason:
        return _blocked(clean_reason)
    executor_reason = _executor_available(task.get("executor") or "")
    if executor_reason:
        return _blocked(executor_reason)
    return {"status": "ok"}


def cmd_prepare(args: argparse.Namespace) -> int:
    if args.project_id != CORE_PROJECT_ID:
        _print_json(_blocked("project_id_not_allowed", project_id=args.project_id))
        return 2
    if _active_smoke_tasks():
        _print_json(_blocked("active_smoke_exists"))
        return 2
    out = make_facade().create_task_and_request_start(
        objective=SMOKE_OBJECTIVE,
        project_id=CORE_PROJECT_ID,
        executor=args.executor,
        timeout_seconds=MAX_TIMEOUT_SECONDS,
    )
    _print_json({
        "status": out.get("status"),
        "task_id": out.get("task_id"),
        "project_id": CORE_PROJECT_ID,
        "executor": args.executor,
        "approval_id": out.get("approval_id"),
        "next": (
            "python scripts/javes_execution_smoke.py approve-start "
            f"--task-id {out.get('task_id')} --approval-id {out.get('approval_id')} "
            f"--confirm \"{APPROVE_PHRASE}\""
        ),
    })
    return 0


def cmd_approve_start(args: argparse.Namespace) -> int:
    if args.confirm != APPROVE_PHRASE:
        _print_json(_blocked("confirmation_phrase_required"))
        return 2
    task = _load_task(args.task_id)
    if not task:
        _print_json(_blocked("task_not_found"))
        return 2
    approval = repo.approvals.get(int(args.approval_id))
    if not approval or approval.get("status") != "pending":
        _print_json(_blocked("approval_not_pending"))
        return 2
    if approval.get("task_id") != task["task_id"] or approval.get("project_id") != CORE_PROJECT_ID:
        _print_json(_blocked("approval_scope_mismatch"))
        return 2
    if approval.get("action") != execution_approvals.ACTION_START:
        _print_json(_blocked("approval_action_mismatch"))
        return 2
    repo.approvals.decide(int(args.approval_id), True, note="R4.3A smoke CLI", approved_by="smoke_cli")
    out = make_facade().approve_start(task["task_id"], CORE_PROJECT_ID, int(args.approval_id))
    _print_json({
        "status": out.get("status"),
        "task_id": task["task_id"],
        "project_id": CORE_PROJECT_ID,
        "approval_id": int(args.approval_id),
        "next": (
            "set JAVIS_ENABLE_SUPERVISED_EXEC=1 && "
            "python scripts/javes_execution_smoke.py run "
            f"--task-id {task['task_id']} --confirm \"{RUN_PHRASE}\""
        ),
    })
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if args.confirm != RUN_PHRASE:
        _print_json(_blocked("confirmation_phrase_required"))
        return 2
    task = _load_task(args.task_id)
    if not task:
        _print_json(_blocked("task_not_found"))
        return 2
    preflight = _preflight_run(task)
    if preflight.get("status") != "ok":
        _print_json(preflight)
        return 2
    out = make_facade().start_execution(task["task_id"], CORE_PROJECT_ID, SMOKE_TEST_COMMANDS)
    _print_json({
        "status": out.get("status"),
        "reason": out.get("reason", ""),
        "task_id": task["task_id"],
        "project_id": CORE_PROJECT_ID,
        "merge": "not_requested",
    })
    return 0 if out.get("status") == et.AWAITING_REVIEW else 1


def cmd_status(args: argparse.Namespace) -> int:
    task = _load_task(args.task_id)
    if not task:
        _print_json(_blocked("task_not_found"))
        return 2
    facade = make_facade()
    payload = facade.get_task(task["task_id"], CORE_PROJECT_ID)
    result = facade.result_summary(task["task_id"], CORE_PROJECT_ID)
    summary = result.get("summary") or {}
    tests_status = payload.get("tests_status") or "not_run"
    if task.get("status") in {et.FAILED, et.TIMED_OUT}:
        tests_status = "failed"
    worktree_path = task.get("worktree_path") or ""
    out = {
        "task_id": task["task_id"],
        "executor": task.get("executor") or "",
        "status": task.get("status") or "",
        "tests": tests_status,
        "changed_files_count": int(summary.get("changed_count") or payload.get("changed_files_count") or 0),
        "resultado_sanitizado": {
            "diff_stat": _public_text(summary.get("diff_stat") or "", 1200),
            "diff_truncated": bool(summary.get("diff_truncated")),
            "collected_at": summary.get("collected_at") or "",
        },
        "worktree_preservada": bool(worktree_path and Path(worktree_path).exists()),
    }
    _print_json(out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke test manual do executor supervisionado R4.3A.")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="Cria execution_task smoke e solicita approval.")
    prepare.add_argument("--executor", choices=("claude", "codex"), required=True)
    prepare.add_argument("--project-id", default=CORE_PROJECT_ID)
    prepare.set_defaults(func=cmd_prepare)

    approve = sub.add_parser("approve-start", help="Consome approval execution.start sem executar agente.")
    approve.add_argument("--task-id", required=True)
    approve.add_argument("--approval-id", type=int, required=True)
    approve.add_argument("--confirm", required=True)
    approve.set_defaults(func=cmd_approve_start)

    run = sub.add_parser("run", help="Executa o smoke aprovado até awaiting_review.")
    run.add_argument("--task-id", required=True)
    run.add_argument("--confirm", required=True)
    run.set_defaults(func=cmd_run)

    status = sub.add_parser("status", help="Mostra resumo sanitizado da execution_task smoke.")
    status.add_argument("--task-id", required=True)
    status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    db.init_db()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
