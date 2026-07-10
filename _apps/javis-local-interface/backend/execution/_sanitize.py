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


def _redact(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def sanitize(value: object, limit: int = 500) -> str:
    """Retorna texto sem tokens/chaves/senhas/credenciais-em-URL, truncado."""
    return _redact(str(value or ""))[:limit]


def sanitize_truncated(value: object, limit: int) -> str:
    """Como sanitize, mas com marcador explícito de truncagem.

    Redige SEMPRE o texto inteiro ANTES de truncar (evita vazar um segredo que
    ficaria na fronteira do corte) e só então limita ao tamanho pedido.
    """
    text = _redact(str(value or ""))
    if len(text) > limit:
        return text[:limit] + f"\n...[truncado em {limit} chars]"
    return text
