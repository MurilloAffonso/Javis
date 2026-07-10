"""R3.1 — Correção 2: estado interno do Javes fora do prompt do Jampa.

Prova que `agent._system_dynamic()` só injeta briefing.estado_resumido()
(CURRENT_STATE.md, roadmap, fases R1..R4) quando o project_id corrente é
javes-core. Para project:cerebro-jampa, esse bloco não entra. Sem rede.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import agent  # noqa: E402
import gate  # noqa: E402
import knowledge  # noqa: E402

# Sentinela injetada no lugar do estado real — não depende do conteúdo do disco.
_SENTINEL = "SENTINEL_CURRENT_STATE R2.3 R3 R4 roadmap-interno-do-javes"


@pytest.fixture(autouse=True)
def _fake_briefing(monkeypatch):
    import briefing
    monkeypatch.setattr(briefing, "estado_resumido", lambda *a, **k: _SENTINEL)
    yield
    agent._PROJECT_CTX.set(agent._DEFAULT_PROJECT_ID)


def test_prompt_javes_core_contem_estado():
    agent._PROJECT_CTX.set(gate.CORE_SCOPE)
    dyn = agent._system_dynamic()
    assert _SENTINEL in dyn
    assert "Estado atual do projeto Javis" in dyn


def test_prompt_jampa_nao_contem_estado_interno():
    agent._PROJECT_CTX.set(gate.CEREBRO_JAMPA_SCOPE)
    dyn = agent._system_dynamic()
    for proibido in (_SENTINEL, "Estado atual do projeto Javis", "R2.3", "R3", "R4"):
        assert proibido not in dyn
    # mas o bloco neutro (hora) continua presente
    assert "Hora atual" in dyn


def test_system_completo_jampa_sem_estado_interno():
    agent._PROJECT_CTX.set(gate.CEREBRO_JAMPA_SCOPE)
    full = agent._system()
    assert _SENTINEL not in full


def test_default_sem_contexto_e_javes_core():
    # Sem project_id setado → default javes-core → estado presente (comportamento normal).
    agent._PROJECT_CTX.set(agent._DEFAULT_PROJECT_ID)
    assert _SENTINEL in agent._system_dynamic()


def test_rag_jampa_continua_somente_vp():
    assert knowledge.scope_for_project(gate.CEREBRO_JAMPA_SCOPE) == "vp"
    assert knowledge.scope_for_project(gate.CORE_SCOPE) == ["pessoal", "projeto"]
