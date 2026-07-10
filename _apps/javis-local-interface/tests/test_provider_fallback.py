"""R2.1 — fallback de providers e modo local seguro.

Nenhum teste toca a rede real, abre .env ou sobe servidor: Ollama e os
provedores cloud são sempre mocks/monkeypatch.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import agent  # noqa: E402
import provider_health  # noqa: E402
import safe_config  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_provider_env(monkeypatch, tmp_path):
    monkeypatch.setattr(provider_health, "STATE_FILE", tmp_path / "provider_health.json")
    for name in (
        "JAVES_PROVIDER_MODE",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
        "GEMINI_API_KEY",
        "JAVIS_CHAT_FAST_BRAIN",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")


def _make_ollama(available: bool):
    mod = type(sys)("ollama_brain")
    mod.available = lambda timeout=2: available
    mod.answer = lambda q, context="", system=None: "resposta-local-ollama"
    return mod


# --- C/F: modo local usa Ollama e nunca cai na nuvem -----------------------
def test_modo_local_usa_ollama(monkeypatch):
    monkeypatch.setenv("JAVES_PROVIDER_MODE", "local")
    monkeypatch.setitem(sys.modules, "ollama_brain", _make_ollama(True))
    monkeypatch.setattr(agent, "_system", lambda: "")
    monkeypatch.setattr(agent, "_history_context", lambda h: "")

    out = agent.respond("oi", [], project_id="")
    assert out["text"] == "resposta-local-ollama"


def test_modo_local_sem_ollama_retorna_provider_unavailable(monkeypatch):
    monkeypatch.setenv("JAVES_PROVIDER_MODE", "local")
    monkeypatch.setitem(sys.modules, "ollama_brain", _make_ollama(False))

    # Se tentasse cloud, isto seria chamado — provamos que NÃO é.
    def _boom(*a, **k):
        raise AssertionError("modo local não pode chamar provider cloud")

    monkeypatch.setattr(agent, "_respond_gemini", _boom)
    monkeypatch.setattr(agent, "_respond_openai", _boom)
    monkeypatch.setattr(agent, "_respond_claude", _boom)
    monkeypatch.setattr(agent, "_respond_openrouter", _boom)

    out = agent.respond("oi", [], project_id="")
    assert out["status"] == "provider_unavailable"
    assert out["reason"] == "ollama_unavailable_or_model_missing"
    assert out["text"] == agent._PROVIDER_UNAVAILABLE_MSG


# --- A: chat sem project_id normaliza para javes-core ----------------------
def test_respond_normaliza_project_id_vazio(monkeypatch):
    monkeypatch.setenv("JAVES_PROVIDER_MODE", "local")
    monkeypatch.setitem(sys.modules, "ollama_brain", _make_ollama(False))
    agent.respond("oi", [], project_id="")
    assert agent._current_project_id() == "javes-core"


# --- D/E: cadeia cloud falhando não derruba e devolve msg amigável ---------
def test_cadeia_cloud_toda_falhando_retorna_msg_amigavel(monkeypatch):
    monkeypatch.setenv("JAVES_PROVIDER_MODE", "cloud")
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")  # só o último elo tem chave

    def _fail(*a, **k):
        raise RuntimeError("429 rate limit")

    monkeypatch.setattr(agent, "_respond_claude_subscription", lambda *a, **k: None)
    monkeypatch.setattr(agent, "_respond_openrouter", _fail)

    out = agent.respond("explique X", [], project_id="javes-core")
    assert out["text"] == agent._PROVIDER_UNAVAILABLE_MSG
    assert out["tools"] == []


def test_modo_cloud_nao_tenta_ollama(monkeypatch):
    monkeypatch.setenv("JAVES_PROVIDER_MODE", "cloud")
    boom = type(sys)("ollama_brain")

    def _no(*a, **k):
        raise AssertionError("modo cloud não deve tocar o Ollama")

    boom.available = _no
    monkeypatch.setitem(sys.modules, "ollama_brain", boom)
    monkeypatch.setattr(agent, "_respond_claude_subscription", lambda *a, **k: {"text": "cloud", "tools": []})

    out = agent.respond("oi", [], project_id="javes-core")
    assert out["text"] == "cloud"


# --- modo default é 'auto' -------------------------------------------------
def test_provider_mode_default_auto(monkeypatch):
    monkeypatch.delenv("JAVES_PROVIDER_MODE", raising=False)
    assert safe_config.provider_mode() == "auto"


@pytest.mark.parametrize("val,expected", [
    ("local", "local"), ("CLOUD", "cloud"), ("auto", "auto"), ("lixo", "auto"),
])
def test_provider_mode_parse(monkeypatch, val, expected):
    monkeypatch.setenv("JAVES_PROVIDER_MODE", val)
    assert safe_config.provider_mode() == expected
