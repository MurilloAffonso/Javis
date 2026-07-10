from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import db  # noqa: E402
import repositories as repo  # noqa: E402
from orchestrator import Orchestrator  # noqa: E402
from execution import execution_task as et  # noqa: E402

CORE = "javes-core"
JAMPA = "project:cerebro-jampa"


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


def _blocked_module(name: str) -> ModuleType:
    module = ModuleType(name)

    def _getattr(attr: str):
        raise AssertionError(f"{name}.{attr} nao deveria ser chamado")

    module.__getattr__ = _getattr  # type: ignore[attr-defined]
    return module


def test_programar_cria_task_e_approval_sem_brain_switch(monkeypatch):
    monkeypatch.setitem(sys.modules, "brain_switch", _blocked_module("brain_switch"))
    monkeypatch.setitem(sys.modules, "code_agent", _blocked_module("code_agent"))
    monkeypatch.setitem(sys.modules, "claude_exec", _blocked_module("claude_exec"))
    orch = Orchestrator()

    msg, running = orch._run_exec("programar uma função", project_id=CORE)

    out = orch._last_exec_task
    assert running is False
    assert out["status"] == et.PENDING_APPROVAL
    assert out["project_id"] == CORE
    assert out["approval_id"]
    assert "aguardando aprovação" in msg
    assert repo.execution_tasks.get(out["task_id"], CORE)["status"] == et.PENDING_APPROVAL


def test_process_delegado_nao_executa_agente_real(monkeypatch):
    monkeypatch.setattr("delegacao.enabled", lambda: True)
    monkeypatch.setattr("delegacao.should_delegate", lambda text: True)
    monkeypatch.setitem(sys.modules, "brain_switch", _blocked_module("brain_switch"))
    orch = Orchestrator()

    result = orch.process("programar endpoint", project_id=CORE)

    assert result.brain == "exec"
    assert result.exec_running is False
    assert orch._last_exec_task["status"] == et.PENDING_APPROVAL


def test_project_jampa_so_quando_explicito():
    orch = Orchestrator()

    orch._run_exec("programar algo", project_id=JAMPA)

    assert orch._last_exec_task["project_id"] == JAMPA
