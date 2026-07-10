"""R2.1 — project_id nunca fica indefinido.

Cobre o bug `NameError: name 'project_id' is not defined` que derrubava a tool
`buscar_conhecimento`, e a regra de default "javes-core". Não abre .env, não
sobe servidor, não chama provider externo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import agent  # noqa: E402
import gate  # noqa: E402


# --- A/B: normalização e default -------------------------------------------
@pytest.mark.parametrize("raw", ["", None, "   "])
def test_project_id_vazio_vira_javes_core(raw):
    assert agent._normalize_project_id(raw) == "javes-core"


def test_project_id_explicito_preservado():
    assert agent._normalize_project_id("project:cerebro-jampa") == "project:cerebro-jampa"


def test_current_project_id_default_sem_contexto():
    # Sem nada setado, o default do contextvar responde "javes-core".
    assert agent._current_project_id() == "javes-core"


# --- Bug project_id: buscar_conhecimento não pode lançar NameError ----------
def test_buscar_conhecimento_usa_escopo_normalizado(monkeypatch):
    capturado = {}

    fake_knowledge = type(sys)("knowledge")
    fake_knowledge.scope_for_project = lambda pid: capturado.setdefault("pid", pid) or ["s"]
    fake_knowledge.answer_context = lambda pergunta, escopo=None: "ctx-ok"
    monkeypatch.setitem(sys.modules, "knowledge", fake_knowledge)

    # Sem project_id explícito no contexto → cai no default "javes-core".
    agent._PROJECT_CTX.set("javes-core")
    out = agent._exec_tool("buscar_conhecimento", {"pergunta": "quem sou eu"})

    assert out == "ctx-ok"
    assert capturado["pid"] == "javes-core"  # nunca indefinido


def test_buscar_conhecimento_respeita_project_id_de_projeto(monkeypatch):
    capturado = {}
    fake_knowledge = type(sys)("knowledge")
    fake_knowledge.scope_for_project = lambda pid: capturado.setdefault("pid", pid) or ["s"]
    fake_knowledge.answer_context = lambda pergunta, escopo=None: "ctx"
    monkeypatch.setitem(sys.modules, "knowledge", fake_knowledge)

    agent._PROJECT_CTX.set("project:cerebro-jampa")
    agent._exec_tool("buscar_conhecimento", {"pergunta": "x"})
    assert capturado["pid"] == "project:cerebro-jampa"


# --- G: rotas VP/Jampa continuam exigindo project_id explícito --------------
def test_vp_jampa_exige_project_id_explicito():
    # project_id vazio em escopo restrito → bloqueia.
    blocked = gate.require_project_scope("", scope=gate.CEREBRO_JAMPA_SCOPE)
    assert blocked is not None

    # project_id correto → passa.
    ok = gate.require_project_scope(gate.CEREBRO_JAMPA_SCOPE, scope=gate.CEREBRO_JAMPA_SCOPE)
    assert ok is None
