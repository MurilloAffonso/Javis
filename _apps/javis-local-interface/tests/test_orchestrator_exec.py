"""Contrato legado atualizado: programação cria execution_task supervisionada."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import db  # noqa: E402
from orchestrator import Orchestrator  # noqa: E402
from execution import execution_task as et  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


def test_orchestrator_atalho_cria_task_sem_classificar(monkeypatch):
    orch = Orchestrator()
    monkeypatch.setattr("delegacao.enabled", lambda: True)
    monkeypatch.setattr("delegacao.should_delegate", lambda text: True)
    monkeypatch.setattr(orch, "_classify", lambda text: pytest.fail("_classify nao deveria rodar"))

    result = orch.process("programa uma função")

    assert result.brain == "exec"
    assert result.exec_running is False
    assert orch._last_exec_task["status"] == et.PENDING_APPROVAL


def test_orchestrator_brain_exec_from_classify_cria_task(monkeypatch):
    orch = Orchestrator()
    monkeypatch.setattr("delegacao.enabled", lambda: False)
    monkeypatch.setattr(orch, "_classify", lambda text: {
        "intent": "código",
        "complexity": "simple",
        "brain": "exec",
        "plan": "refatora X",
    })

    result = orch.process("refatora o código")

    assert result.brain == "exec"
    assert result.exec_running is False
    assert orch._last_exec_task["approval_id"]


def test_orchestrator_delegacao_disabled_mantem_main(monkeypatch):
    orch = Orchestrator()
    monkeypatch.setattr("delegacao.enabled", lambda: False)
    monkeypatch.setattr(orch, "_classify", lambda text: {
        "intent": "conversa",
        "complexity": "simple",
        "brain": "main",
    })
    monkeypatch.setattr(orch, "_main_brain", lambda text, history: "Resposta")

    result = orch.process("olá")

    assert result.brain == "main"
    assert result.response == "Resposta"
