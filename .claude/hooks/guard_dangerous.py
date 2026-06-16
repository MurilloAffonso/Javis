#!/usr/bin/env python
"""PreToolUse guard — bloqueia comandos destrutivos no Bash do Claude Code.

Usado pela execução headless do Javis (claude_exec.py) e também protege as
sessões interativas do Murillo. Alinhado ao CLAUDE.md: nada de git push/reset,
delete ou commit sem aprovação.

Protocolo: lê o JSON do PreToolUse no stdin. Para BLOQUEAR, sai com código 2 e
escreve o motivo no stderr (o Claude vê e não roda o comando).

FAIL-OPEN: qualquer erro/exceção → libera (exit 0). Este hook é uma rede de
segurança extra, não a única proteção; nunca deve travar trabalho legítimo.
"""
import json
import re
import sys

# Padrões claramente destrutivos (case-insensitive).
_DANGEROUS = [
    r"\bgit\s+push\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[a-z]*f",
    r"\bgit\s+branch\s+-D\b",
    r"\bgit\s+checkout\s+--\s",
    r"\bgit\s+.*--force\b", r"\bgit\s+push\s+-f\b",
    r"\brm\s+-[a-z]*r[a-z]*f", r"\brm\s+-[a-z]*f[a-z]*r",  # rm -rf / -fr
    r"\bdel\s+/[fqs]", r"\brmdir\s+/s\b",
    r"\bformat\s+[a-z]:", r"\bmkfs\b",
    r"\bsudo\b",
    r">\s*/dev/sd[a-z]",
    r"\bshutdown\b", r"\bReinitialize\b",
]
_RX = [re.compile(p, re.I) for p in _DANGEROUS]


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # sem payload legível → libera

    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str) or not cmd.strip():
        return 0

    for rx in _RX:
        if rx.search(cmd):
            sys.stderr.write(
                "BLOQUEADO pelo guard do Javis: comando destrutivo "
                f"({rx.pattern}). Regra do CLAUDE.md — sem git push/reset/clean, "
                "delete ou format. Peça aprovação ao Murillo.\n"
            )
            return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # fail-open
