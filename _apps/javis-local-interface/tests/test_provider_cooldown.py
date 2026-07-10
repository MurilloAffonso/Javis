from __future__ import annotations

from datetime import timedelta
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import provider_health  # noqa: E402
import provider_registry  # noqa: E402


class ErrorWithStatus(Exception):
    def __init__(self, status_code: int, message: str = ""):
        super().__init__(message or str(status_code))
        self.status_code = status_code


def test_rate_limit_respeita_retry_after(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "health.json")
    exc = ErrorWithStatus(429, "rate limit")
    exc.headers = {"Retry-After": "9"}

    provider_health.record_failure("openrouter", exc)
    state = provider_health.public_status("openrouter")

    assert state["last_error_type"] == "rate_limited"
    assert state["in_cooldown"] is True


def test_billing_error_vira_billing_blocked(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "health.json")

    provider_health.record_failure("openai", RuntimeError("billing hard limit reached"))

    assert provider_health.public_status("openai")["health_status"] == "cooldown"
    assert provider_health.get("openai").health_status == "billing_blocked"


def test_timeout_tem_cooldown_curto(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "health.json")
    start = provider_health.now_utc()

    provider_health.record_failure("ollama", TimeoutError("timed out"), at=start)
    until = provider_health._parse_ts(provider_health.get("ollama").cooldown_until)

    assert until is not None
    assert until - start <= timedelta(seconds=61)


def test_sucesso_remove_cooldown_transitorio(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "health.json")
    provider_health.record_failure("gemini", ErrorWithStatus(429))

    provider_health.record_success("gemini")

    state = provider_health.public_status("gemini")
    assert state["health_status"] == "healthy"
    assert state["in_cooldown"] is False
    assert state["last_error_type"] == ""


def test_registry_pula_provider_em_cooldown(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "health.json")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    provider_health.record_failure("openrouter", ErrorWithStatus(429))

    assert "openrouter" not in provider_registry.selected_provider_ids("cloud")
