from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "_apps" / "javis-local-interface" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import system_health  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnostico local read-only do Javes.")
    parser.add_argument("--json", action="store_true", help="Saida em JSON sem segredos.")
    parser.add_argument("--no-probe", action="store_true", help="Nao testa porta local do Ollama.")
    parser.add_argument("--verbose", action="store_true", help="Inclui git status completo no texto.")
    args = parser.parse_args(argv)

    data = system_health.snapshot(probe_ollama=not args.no_probe)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    text = system_health.render_text(data)
    if args.verbose and data.get("git_status"):
        text += "\n- git_status_full:\n" + data["git_status"]
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
