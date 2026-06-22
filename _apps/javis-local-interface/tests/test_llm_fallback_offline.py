"""Testes offline da cascata LLM e do adaptador OpenRouter.

Toda tentativa de socket falha antes de sair do processo. Clientes de provedor
são sempre mocks; estas provas não carregam o .env real.
"""
from __future__ import annotations

import json
import runpy
import socket
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import agent


@pytest.fixture(autouse=True)
def zero_network_and_clean_env(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("rede bloqueada pelo teste offline")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    for name in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
        "GEMINI_API_KEY",
        "JAVIS_ALLOW_LIVE_OPENROUTER_TEST",
        "JAVIS_OPENROUTER_BENCHMARK_MAX_USD",
    ):
        monkeypatch.delenv(name, raising=False)


def test_ausencia_de_chave_pula_provedores_api(monkeypatch):
    chamados = []
    monkeypatch.setattr(
        agent, "_respond_claude_subscription",
        lambda *_args, **_kwargs: chamados.append("claude_subscription") or None,
    )

    def nao_deveria_chamar(*_args, **_kwargs):
        raise AssertionError("provedor API chamado sem chave")

    monkeypatch.setattr(agent, "_respond_openai", nao_deveria_chamar)
    monkeypatch.setattr(agent, "_respond_claude", nao_deveria_chamar)
    monkeypatch.setattr(agent, "_respond_openrouter", nao_deveria_chamar)

    assert agent.respond("olá") is None
    assert chamados == ["claude_subscription"]


def test_ordem_de_fallback(monkeypatch):
    ordem = []
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic")
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-openrouter")

    def assinatura(*_args, **_kwargs):
        ordem.append("claude_subscription")
        raise RuntimeError("indisponível")

    def openai(*_args, **_kwargs):
        ordem.append("openai")
        raise TimeoutError("timeout simulado")

    def anthropic(*_args, **_kwargs):
        ordem.append("anthropic")
        raise RuntimeError("erro simulado")

    def openrouter(*_args, **kwargs):
        ordem.append("openrouter")
        assert kwargs["fallback_used"] is True
        return {"text": "fallback ok", "tools": []}

    monkeypatch.setattr(agent, "_respond_claude_subscription", assinatura)
    monkeypatch.setattr(agent, "_respond_openai", openai)
    monkeypatch.setattr(agent, "_respond_claude", anthropic)
    monkeypatch.setattr(agent, "_respond_openrouter", openrouter)

    assert agent.respond("teste")["text"] == "fallback ok"
    assert ordem == ["claude_subscription", "openai", "anthropic", "openrouter"]


def test_timeout_avanca_para_proximo_provedor(monkeypatch):
    ordem = []
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic")
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-openrouter")
    monkeypatch.setattr(agent, "_respond_claude_subscription", lambda *_a, **_k: None)

    def openai(*_args, **_kwargs):
        ordem.append("openai")
        raise TimeoutError("timeout offline")

    def anthropic(*_args, **_kwargs):
        ordem.append("anthropic")
        return {"text": "claude api ok", "tools": []}

    monkeypatch.setattr(agent, "_respond_openai", openai)
    monkeypatch.setattr(agent, "_respond_claude", anthropic)
    monkeypatch.setattr(
        agent, "_respond_openrouter",
        lambda *_a, **_k: pytest.fail("OpenRouter não deveria ser alcançado"),
    )

    assert agent.respond("teste")["text"] == "claude api ok"
    assert ordem == ["openai", "anthropic"]


def test_erro_de_provedor_avanca_para_openrouter(monkeypatch):
    ordem = []
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-openrouter")
    monkeypatch.setattr(agent, "_respond_claude_subscription", lambda *_a, **_k: None)

    def openai(*_args, **_kwargs):
        ordem.append("openai")
        raise RuntimeError("erro offline")

    def openrouter(*_args, **_kwargs):
        ordem.append("openrouter")
        return {"text": "openrouter ok", "tools": []}

    monkeypatch.setattr(agent, "_respond_openai", openai)
    monkeypatch.setattr(agent, "_respond_openrouter", openrouter)

    assert agent.respond("teste")["text"] == "openrouter ok"
    assert ordem == ["openai", "openrouter"]


def test_tool_use_openrouter_e_telemetria_sao_offline(monkeypatch, tmp_path):
    secret = "sk-or-v1-segredo-que-nao-pode-vazar"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)
    # Fixa o modelo :free para o teste não herdar JAVIS_OPENROUTER_MODEL do .env real.
    monkeypatch.setenv("JAVIS_OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    monkeypatch.setattr(agent, "_USAGE_LOG_PATH", str(tmp_path / "usage.jsonl"))
    monkeypatch.setattr(agent, "_system", lambda: "system offline")
    monkeypatch.setattr(
        agent,
        "_gate_tools",
        lambda _text: [{
            "name": "hora_data",
            "description": "hora local",
            "input_schema": {"type": "object", "properties": {}},
        }],
    )

    tool_call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="hora_data", arguments="{}"),
    )
    responses = [
        SimpleNamespace(
            model="openrouter/mock-resolved",
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=2, cost=0.0),
            choices=[SimpleNamespace(message=SimpleNamespace(content="", tool_calls=[tool_call]))],
        ),
        SimpleNamespace(
            model="openrouter/mock-resolved",
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=3, cost=0.0),
            choices=[SimpleNamespace(message=SimpleNamespace(content="feito", tool_calls=[]))],
        ),
    ]
    requests = []

    class FakeCompletions:
        def create(self, **kwargs):
            requests.append(kwargs)
            return responses.pop(0)

    class FakeOpenAI:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == secret
            assert kwargs["base_url"] == "https://openrouter.ai/api/v1"
            self.chat = SimpleNamespace(completions=FakeCompletions())

    import openai
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)

    ferramentas = []
    monkeypatch.setattr(
        agent, "_exec_tool",
        lambda name, args, _history: ferramentas.append((name, args)) or "12:00",
    )

    result = agent._respond_openrouter("que horas são?", [], 3)

    assert result == {"text": "feito", "tools": ["hora_data"]}
    assert ferramentas == [("hora_data", {})]
    assert len(requests) == 2
    assert any(message["role"] == "tool" for message in requests[1]["messages"])

    records = [
        json.loads(line)
        for line in (tmp_path / "usage.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 2
    assert all(record["provider"] == "openrouter" for record in records)
    assert all(record["requested_model"].endswith(":free") for record in records)
    assert all(record["resolved_model"] == "openrouter/mock-resolved" for record in records)
    assert all(record["estimated_cost_usd"] == 0.0 for record in records)
    assert all(record["latency_ms"] is not None for record in records)
    assert all(record["error"] is None for record in records)
    assert secret not in (tmp_path / "usage.jsonl").read_text(encoding="utf-8")


def test_erro_openrouter_e_sanitizado(monkeypatch, tmp_path):
    secret = "sk-or-v1-segredo-timeout-123456"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)
    monkeypatch.setattr(agent, "_USAGE_LOG_PATH", str(tmp_path / "usage.jsonl"))
    monkeypatch.setattr(agent, "_system", lambda: "system offline")
    monkeypatch.setattr(agent, "_gate_tools", lambda _text: [])

    class FailingCompletions:
        def create(self, **_kwargs):
            raise TimeoutError(f"timeout api_key={secret}")

    class FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=FailingCompletions())

    import openai
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)

    with pytest.raises(TimeoutError):
        agent._respond_openrouter("teste", [], 1, fallback_used=True)

    raw = (tmp_path / "usage.jsonl").read_text(encoding="utf-8")
    record = json.loads(raw)
    assert secret not in raw
    assert "[REDACTED]" in record["error"]
    assert record["fallback_used"] is True
    assert record["provider"] == "openrouter"


def test_erro_final_openrouter_nao_vaza_segredo_na_resposta(monkeypatch):
    secret = "sk-or-v1-segredo-resposta-123456"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)
    monkeypatch.setattr(agent, "_respond_claude_subscription", lambda *_a, **_k: None)

    def falha(*_args, **_kwargs):
        raise RuntimeError(f"falha api_key={secret}")

    monkeypatch.setattr(agent, "_respond_openrouter", falha)
    result = agent.respond("teste")

    assert secret not in result["text"]
    assert "registrado sem credenciais" in result["text"]


def test_script_live_bloqueado_nao_imprime_prefixo(monkeypatch, capsys):
    secret = "sk-or-v1-prefixo-ultrassecreto-123456"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)
    script = BACKEND_DIR / "_scratch" / "_test_openrouter.py"

    runpy.run_path(str(script), run_name="__main__")

    output = capsys.readouterr().out
    assert "BLOQUEADO" in output
    assert secret not in output
    assert secret[:20] not in output


def test_guard_zero_rede_bloqueia_socket():
    with pytest.raises(AssertionError, match="rede bloqueada"):
        socket.create_connection(("example.invalid", 443))
