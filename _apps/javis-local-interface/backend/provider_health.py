"""Local provider health and cooldown state."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from provider_errors import ProviderError, classify_error


BACKEND_DIR = Path(__file__).resolve().parent
STATE_FILE = BACKEND_DIR.parent / "_data" / "provider_health.json"

HEALTHY = "healthy"
UNAVAILABLE = "unavailable"
RATE_LIMITED = "rate_limited"
AUTHENTICATION_ERROR = "authentication_error"
BILLING_BLOCKED = "billing_blocked"
COOLDOWN = "cooldown"
UNKNOWN = "unknown"

_COOLDOWNS = {
    "authentication_error": 24 * 60 * 60,
    "billing_error": 24 * 60 * 60,
    "rate_limited": 5 * 60,
    "timeout": 60,
    "unavailable": 2 * 60,
    "model_not_found": 60 * 60,
    "invalid_request": 10 * 60,
    "unknown_error": 60,
}


@dataclass
class ProviderHealth:
    provider_id: str
    health_status: str = HEALTHY
    last_error_type: str = ""
    last_error_at: str = ""
    cooldown_until: str = ""


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def _load() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get(provider_id: str) -> ProviderHealth:
    raw = _load().get(provider_id) or {}
    return ProviderHealth(
        provider_id=provider_id,
        health_status=raw.get("health_status") or HEALTHY,
        last_error_type=raw.get("last_error_type") or "",
        last_error_at=raw.get("last_error_at") or "",
        cooldown_until=raw.get("cooldown_until") or "",
    )


def is_in_cooldown(provider_id: str, at: datetime | None = None) -> bool:
    state = get(provider_id)
    until = _parse_ts(state.cooldown_until)
    return bool(until and until > (at or now_utc()))


def public_status(provider_id: str) -> dict:
    state = get(provider_id)
    in_cooldown = is_in_cooldown(provider_id)
    return {
        "provider_id": provider_id,
        "health_status": COOLDOWN if in_cooldown else state.health_status,
        "last_error_type": state.last_error_type,
        "last_error_at": state.last_error_at,
        "cooldown_until": state.cooldown_until,
        "in_cooldown": in_cooldown,
    }


def _health_status_for(error: ProviderError) -> str:
    if error.error_type == "authentication_error":
        return AUTHENTICATION_ERROR
    if error.error_type == "billing_error":
        return BILLING_BLOCKED
    if error.error_type == "rate_limited":
        return RATE_LIMITED
    if error.error_type in {"timeout", "unavailable", "model_not_found"}:
        return UNAVAILABLE
    return UNKNOWN


def record_failure(provider_id: str, exc: object, at: datetime | None = None) -> ProviderError:
    error = exc if isinstance(exc, ProviderError) else classify_error(exc)
    if not error.provider_failure:
        return error
    current = at or now_utc()
    seconds = error.retry_after_seconds if error.retry_after_seconds is not None else _COOLDOWNS.get(error.error_type, 60)
    data = _load()
    data[provider_id] = asdict(ProviderHealth(
        provider_id=provider_id,
        health_status=_health_status_for(error),
        last_error_type=error.error_type,
        last_error_at=_iso(current),
        cooldown_until=_iso(current + timedelta(seconds=max(0, int(seconds)))),
    ))
    _save(data)
    return error


def record_success(provider_id: str) -> None:
    data = _load()
    data[provider_id] = asdict(ProviderHealth(provider_id=provider_id, health_status=HEALTHY))
    _save(data)


def reset(provider_id: str | None = None) -> None:
    if provider_id is None:
        _save({})
        return
    data = _load()
    data.pop(provider_id, None)
    _save(data)
