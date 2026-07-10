from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "_apps" / "javis-local-interface" / "backend"


def test_orchestrator_nao_chama_dispatch_legado():
    src = (BACKEND / "orchestrator.py").read_text(encoding="utf-8")

    assert "brain_switch.dispatch" not in src
    assert "code_agent.dispatch" not in src
    assert "claude_exec.dispatch" not in src


def test_server_nao_usa_codex_exec_para_programacao_supervisionada():
    src = (BACKEND / "server.py").read_text(encoding="utf-8")

    assert "safe_config.codex_exec_enabled()" not in src
    assert "tools\": [\"execution_task\"]" in src


def test_legado_permanece_documentado_mas_sem_caller_operacional():
    assert (BACKEND / "code_agent.py").exists()
    assert (BACKEND / "claude_exec.py").exists()
    assert (BACKEND / "brain_switch.py").exists()
