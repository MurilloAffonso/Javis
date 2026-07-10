from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import agent  # noqa: E402
import actions  # noqa: E402


@pytest.fixture(autouse=True)
def _local_env(monkeypatch):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVES_PROVIDER_MODE", "local")
    monkeypatch.delenv("JAVIS_ENABLE_LOCAL_ACTIONS", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def _provider_boom(name: str):
    def _boom(*args, **kwargs):
        raise AssertionError(f"{name} nao deveria ser chamado para status_sistema")
    return _boom


@pytest.mark.parametrize("text", [
    "qual é o status do sistema?",
    "status do Javes",
    "como está o sistema?",
])
def test_status_sistema_nao_chama_providers(monkeypatch, text):
    ollama = type(sys)("ollama_brain")
    ollama.available = _provider_boom("ollama")
    ollama.answer = _provider_boom("ollama")
    monkeypatch.setitem(sys.modules, "ollama_brain", ollama)
    monkeypatch.setattr(agent, "_respond_gemini", _provider_boom("gemini"))
    monkeypatch.setattr(agent, "_respond_openai", _provider_boom("openai"))
    monkeypatch.setattr(agent, "_respond_claude", _provider_boom("claude"))
    monkeypatch.setattr(agent, "_respond_claude_subscription", _provider_boom("claude_headless"))
    monkeypatch.setattr(agent, "_respond_openrouter", _provider_boom("openrouter"))

    out = agent.respond(text, [], project_id="")

    assert out is not None
    assert out["tools"] == ["status_sistema"]
    assert "provider_mode: local" in out["text"]


def test_status_sistema_retorna_local_sem_tokens(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret")

    res = actions.execute("status_sistema", "status do Javes")

    assert res["status"] == "ok"
    assert res["provider_mode"] == "local"
    assert "token" not in res["message"].lower()
    assert "sk-test-secret" not in res["message"]
    assert "gemini-secret" not in res["message"]
