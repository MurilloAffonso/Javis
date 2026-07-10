"""Provider error classification and sanitization.

No provider secret, token or API key value is returned from this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import socket
import urllib.error


ERROR_TYPES = {
    "authentication_error",
    "rate_limited",
    "billing_error",
    "timeout",
    "unavailable",
    "invalid_request",
    "model_not_found",
    "unknown_error",
}

_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(authorization|api[_-]?key|token|secret)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\b(?:sk-or-v1-|sk-)[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{8,}\b"),
)


@dataclass(frozen=True)
class ProviderError:
    error_type: str
    public_message: str
    retry_after_seconds: int | None = None
    provider_failure: bool = True


def sanitize_message(value: object, limit: int = 240) -> str:
    text = str(value or "")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text[:limit]


def _status_code(exc: object, text: str) -> int | None:
    for attr in ("status_code", "status", "code"):
        raw = getattr(exc, attr, None)
        try:
            if raw is not None:
                return int(raw)
        except (TypeError, ValueError):
            pass
    match = re.search(r"\b(400|401|403|404|408|409|422|429|500|502|503|504)\b", text)
    return int(match.group(1)) if match else None


def _retry_after(exc: object, text: str) -> int | None:
    headers = getattr(exc, "headers", None) or {}
    raw = None
    try:
        raw = headers.get("retry-after") or headers.get("Retry-After")
    except Exception:
        raw = None
    if raw is None:
        match = re.search(r"retry[_ -]?after[^\d]{0,12}(\d{1,6})", text, re.I)
        raw = match.group(1) if match else None
    try:
        return max(0, int(float(raw))) if raw is not None else None
    except (TypeError, ValueError):
        return None


def classify_error(exc: object) -> ProviderError:
    text = sanitize_message(exc)
    low = text.lower()
    status = _status_code(exc, text)
    retry_after = _retry_after(exc, text)

    if "project_id" in low and status is None:
        return ProviderError("unknown_error", text or "unknown_error", provider_failure=False)
    if status in (401, 403):
        return ProviderError("authentication_error", "authentication_error")
    if status == 429:
        return ProviderError("rate_limited", "rate_limited", retry_after)
    if any(term in low for term in ("credit balance", "insufficient credits", "billing", "quota exceeded", "payment required", "sem crédito", "sem credito")):
        return ProviderError("billing_error", "billing_error")
    if any(term in low for term in ("model not found", "model_not_found", "does not exist", "unknown model", "modelo inexistente", "modelo ausente")):
        return ProviderError("model_not_found", "model_not_found")
    if isinstance(exc, (TimeoutError, socket.timeout)) or any(term in low for term in ("timed out", "timeout", "read timed out")):
        return ProviderError("timeout", "timeout")
    if isinstance(exc, urllib.error.URLError) or any(term in low for term in ("connection refused", "connection reset", "name or service not known", "temporary failure", "unavailable", "503", "502", "504")):
        return ProviderError("unavailable", "unavailable")
    if status in (400, 404, 409, 422) or any(term in low for term in ("bad request", "invalid request", "invalid_request")):
        return ProviderError("invalid_request", "invalid_request")
    return ProviderError("unknown_error", text or "unknown_error")
