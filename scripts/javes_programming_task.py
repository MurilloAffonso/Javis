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
from execution.programming_task_spec import SpecValidationError  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Admissão segura de tarefas de programação")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "prepare"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--spec", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = validate_file(args.spec) if args.command == "validate" else prepare_file(args.spec)
    except SpecValidationError as exc:
        result = {"status": "blocked", "reason": exc.reason}
    except Exception:
        result = {"status": "blocked", "reason": "admission_internal_error"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
