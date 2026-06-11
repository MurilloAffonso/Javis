"""Javis Local Interface — CLI v0. Stdlib only."""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import command_router
import actions
import logger

BANNER = """
╔══════════════════════════════════════╗
║   Javis Local Interface — CLI v0     ║
║   Digite 'sair' para encerrar        ║
╚══════════════════════════════════════╝
"""

RISK_ICONS = {"critical": "🔴", "medium": "🟡", "low": "🟢", "none": "⚪"}


def run() -> None:
    print(BANNER)
    while True:
        try:
            text = input("Javis › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo.")
            break

        if not text:
            continue
        if text.lower() in ("sair", "exit", "quit"):
            print("Até logo.")
            break

        start = time.monotonic()
        route = command_router.route(text)
        _print_route(route)

        approved: bool | None = None

        if route["risk_level"] == "critical":
            print(f"⛔  Ação bloqueada — intent: {route['intent']}")
            result = {"status": "blocked", "message": "Ação crítica — bloqueada pelo router."}
            logger.log("cli", text, route, result, approved=False,
                       duration_ms=_elapsed_ms(start))
            continue

        if route["requires_approval"]:
            answer = input(f"⚠️   Confirmar ação '{route['action']}'? (s/N): ").strip().lower()
            if answer != "s":
                print("Cancelado.")
                result = {"status": "cancelled", "message": "Aprovação negada pelo usuário."}
                logger.log("cli", text, route, result, approved=False,
                           duration_ms=_elapsed_ms(start))
                continue
            approved = True

        result = actions.execute(route["intent"], text)
        duration = _elapsed_ms(start)

        _print_result(result)
        logger.log("cli", text, route, result, approved=approved, duration_ms=duration)


def _print_route(route: dict) -> None:
    icon = RISK_ICONS.get(route["risk_level"], "⚪")
    print(f"  → intent: {route['intent']}  {icon} {route['risk_level']}  "
          f"({route['confidence']}) — {route['reason']}")


def _print_result(result: dict) -> None:
    status = result.get("status", "?")
    msg = result.get("message", "")
    if status == "ok":
        print(f"  ✅ {msg}")
    elif status == "llm":
        print(f"  💬 {msg}")
    elif status == "blocked":
        print(f"  ⛔ {msg}")
    else:
        print(f"  ⚠️  [{status}] {msg}")


def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


if __name__ == "__main__":
    run()
