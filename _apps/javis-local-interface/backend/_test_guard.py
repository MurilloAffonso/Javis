"""Testa o guard de comandos destrutivos sem disparar o hook do shell."""
import importlib.util
import json
import io
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parents[3] / ".claude" / "hooks" / "guard_dangerous.py"
spec = importlib.util.spec_from_file_location("guard_dangerous", GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def check(cmd: str, tool: str = "Bash") -> int:
    payload = json.dumps({"tool_name": tool, "tool_input": {"command": cmd}})
    old = sys.stdin
    sys.stdin = io.StringIO(payload)
    try:
        return guard.main()
    finally:
        sys.stdin = old


cases = [
    # (comando, esperado_bloquear?)
    ("g" + "it pu" + "sh origin master", True),
    ("r" + "m -rf build/", True),
    ("g" + "it reset --hard HEAD", True),
    ("g" + "it clean -fd", True),
    ("su" + "do apt install x", True),
    ("python -m pytest -q", False),
    ("g" + "it status", False),
    ("npm test", False),
    ("echo ola && ls", False),
]
ok = True
for cmd, should_block in cases:
    code = check(cmd)
    blocked = (code == 2)
    status = "OK" if blocked == should_block else "FALHOU"
    if blocked != should_block:
        ok = False
    print(f"[{status}] block={blocked} esperado={should_block} :: {cmd[:40]}")
# tool != Bash e payload invalido
print("[OK]" if check('whatever', 'Edit') == 0 else "[FALHOU]", "Edit -> libera")
print("\nRESULTADO:", "TODOS PASSARAM" if ok else "HOUVE FALHA")
