from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from provider_errors import classify_error, sanitize_message  # noqa: E402


class ErrorWithStatus(Exception):
    def __init__(self, status_code: int, message: str = ""):
        super().__init__(message or str(status_code))
        self.status_code = status_code


def test_401_vira_authentication_error():
    assert classify_error(ErrorWithStatus(401)).error_type == "authentication_error"
    assert classify_error(ErrorWithStatus(403)).error_type == "authentication_error"


def test_429_vira_rate_limited_com_retry_after():
    exc = ErrorWithStatus(429, "rate limit")
    exc.headers = {"Retry-After": "12"}
    out = classify_error(exc)
    assert out.error_type == "rate_limited"
    assert out.retry_after_seconds == 12


def test_billing_vira_billing_error():
    assert classify_error(RuntimeError("credit balance is too low")).error_type == "billing_error"


def test_timeout_vira_timeout():
    assert classify_error(TimeoutError("timed out")).error_type == "timeout"


def test_modelo_inexistente_vira_model_not_found():
    assert classify_error(RuntimeError("model not found")).error_type == "model_not_found"


def test_erro_interno_project_id_nao_e_falha_de_provider():
    out = classify_error(NameError("name 'project_id' is not defined"))
    assert out.error_type == "unknown_error"
    assert out.provider_failure is False


def test_sanitize_nao_expoe_chaves():
    text = sanitize_message("api_key=sk-secret123 token: abcdef OPENAI_API_KEY=sk-other123")
    assert "sk-secret123" not in text
    assert "abcdef" not in text
