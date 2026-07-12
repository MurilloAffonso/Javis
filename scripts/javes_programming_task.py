from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


os.environ.setdefault("JAVIS_SKIP_DOTENV", "1")
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "_apps" / "javis-local-interface" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from execution.programming_task_admission import prepare_file, validate_file  # noqa: E402
from execution.programming_task_flow import ProgrammingTaskFlow  # noqa: E402
from execution.programming_task_spec import SpecValidationError  # noqa: E402
import db  # noqa: E402


def make_flow() -> ProgrammingTaskFlow:
    return ProgrammingTaskFlow()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Admissão segura de tarefas de programação")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "prepare"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--spec", required=True)
    approve = sub.add_parser("approve-start")
    approve.add_argument("--task-id", required=True)
    approve.add_argument("--approval-id", required=True, type=int)
    approve.add_argument("--confirm", required=True)
    run = sub.add_parser("run")
    run.add_argument("--task-id", required=True)
    run.add_argument("--confirm", required=True)
    status = sub.add_parser("status")
    status.add_argument("--task-id", required=True)
    request_merge = sub.add_parser("request-merge")
    request_merge.add_argument("--task-id", required=True)
    approve_merge = sub.add_parser("approve-merge")
    approve_merge.add_argument("--task-id", required=True)
    approve_merge.add_argument("--approval-id", required=True, type=int)
    approve_merge.add_argument("--confirm", required=True)
    merge = sub.add_parser("merge")
    merge.add_argument("--task-id", required=True)
    merge.add_argument("--confirm", required=True)
    reject = sub.add_parser("reject")
    reject.add_argument("--task-id", required=True)
    reject.add_argument("--confirm", required=True)
    reject_merge = sub.add_parser("reject-merge")
    reject_merge.add_argument("--task-id", required=True)
    reject_merge.add_argument("--confirm", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_file(args.spec)
        elif args.command == "prepare":
            result = prepare_file(args.spec)
        else:
            db.init_db()
            flow = make_flow()
            if args.command == "approve-start":
                result = flow.approve_start(args.task_id, args.approval_id, args.confirm)
            elif args.command == "run":
                result = flow.run(args.task_id, args.confirm)
            elif args.command == "status":
                result = flow.status(args.task_id)
            elif args.command == "request-merge":
                result = flow.request_merge(args.task_id)
            elif args.command == "approve-merge":
                result = flow.approve_merge(args.task_id, args.approval_id, args.confirm)
            elif args.command == "merge":
                result = flow.merge(args.task_id, args.confirm)
            elif args.command == "reject":
                result = flow.reject(args.task_id, args.confirm)
            else:
                result = flow.reject_merge(args.task_id, args.confirm)
    except SpecValidationError as exc:
        result = {"status": "blocked", "reason": exc.reason}
    except Exception:
        result = {"status": "blocked", "reason": "admission_internal_error"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
