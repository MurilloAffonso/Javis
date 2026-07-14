"""CLI do Modo Madrugada (R4.5).

Roda, desassistida, a task que Murillo JÁ aprovou acordado (`approve-start`).
Para em `awaiting_review` e pede o approval de merge — que fica pending para a
revisão humana de manhã. Não aprova merge, não faz merge, não dá push.

Roda UMA task por noite: o executor só admite uma task real ativa por vez, e
duas tasks da mesma noite sairiam do mesmo commit — a segunda seria inmergeável
depois que a primeira movesse o master.

Uso típico:
    # antes de dormir, com a task já preparada e com approve-start feito:
    python scripts/javes_madrugada.py preflight
    python scripts/javes_madrugada.py run --confirm "ARMAR MADRUGADA"

    # abortar a Madrugada a qualquer momento:
    python scripts/javes_madrugada.py off
"""
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

from execution.night_mode import KILL_SWITCH, NightMode, NightWindow  # noqa: E402
import db  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Modo Madrugada — executa a task já aprovada")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("preflight", "run"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--start-hour", type=int, default=0)
        cmd.add_argument("--end-hour", type=int, default=6)
        if name == "run":
            cmd.add_argument("--confirm", required=True)

    sub.add_parser("off", help="ativa o kill switch: a Madrugada não inicia nada")
    sub.add_parser("on", help="desativa o kill switch")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "off":
            KILL_SWITCH.parent.mkdir(parents=True, exist_ok=True)
            KILL_SWITCH.write_text(
                "Madrugada desarmada. Remova este arquivo (ou rode\n"
                "`python scripts/javes_madrugada.py on`) para religar.\n",
                encoding="utf-8",
            )
            result = {"status": "ok", "kill_switch_active": True}
        elif args.command == "on":
            KILL_SWITCH.unlink(missing_ok=True)
            result = {"status": "ok", "kill_switch_active": False}
        else:
            db.init_db()
            night = NightMode(
                window=NightWindow(start_hour=args.start_hour, end_hour=args.end_hour)
            )
            result = night.preflight() if args.command == "preflight" else night.run(args.confirm)
    except Exception:
        result = {"status": "blocked", "reason": "night_mode_internal_error"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
