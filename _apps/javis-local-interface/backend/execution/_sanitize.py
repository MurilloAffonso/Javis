"""Sanitizador pequeno e INDEPENDENTE (sem deps de backend, sem import circular).

Remove segredos de mensagens de erro antes de retornar/persistir. Espelha os
padrões de provider_errors, mas é standalone de propósito: o pacote execution
não deve acoplar-se ao runtime de chat.
"""
from __future__ import annotations

import re

_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(authorization|api[_-]?key|token|secret|password|passwd)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\b(?:sk-or-v1-|sk-|ghp_|gho_|xox[baprs]-)[A-Za-z0-9_-]{6,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{8,}\b"),
    re.compile(r"://[^/\s:@]+:[^/\s@]+@"),  # credenciais em URL user:pass@
)


def sanitize(value: object, limit: int = 500) -> str:
    """Retorna texto sem tokens/chaves/senhas/credenciais-em-URL, truncado."""
    text = str(value or "")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text[:limit]
