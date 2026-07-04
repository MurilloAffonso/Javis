import pytest
import sys
from unittest.mock import patch, MagicMock, Mock
from backend.orchestrator import Orchestrator


def test_orchestrator_atalho_should_delegate():
    """Atalho: should_delegate=True → _run_exec direto, sem _classify."""
    orch = Orchestrator()

    with patch("backend.delegacao.enabled", return_value=True):
        with patch("backend.delegacao.should_delegate", return_value=True):
            with patch.object(orch, "_run_exec", return_value=("Codex rodou", True)) as mock_exec:
                with patch.object(orch, "_classify") as mock_classify:
                    result = orch.process("programa uma função")

                    # Prova: _run_exec foi chamado, _classify NÃO
                    assert mock_exec.called
                    assert not mock_classify.called
                    assert result.brain == "exec"
                    assert result.exec_running is True


def test_orchestrator_brain_exec_from_classify():
    """Classificador marca brain='exec' → _run_exec chamado."""
    orch = Orchestrator()

    with patch("backend.delegacao.enabled", return_value=True):
        with patch("backend.delegacao.should_delegate", return_value=False):  # Atalho não bate
            with patch.object(orch, "_classify", return_value={
                "intent": "código",
                "complexity": "simple",
                "brain": "exec",
                "plan": "refatora X"
            }):
                with patch.object(orch, "_run_exec", return_value=("Codex rodou", True)) as mock_exec:
                    result = orch.process("refatora o código")

                    # Classificador foi chamado, depois _run_exec
                    assert mock_exec.called
                    assert result.brain == "exec"


def test_orchestrator_delegacao_disabled():
    """Com JAVIS_AUTO_CODEX=0, nada muda — comportamento atual."""
    orch = Orchestrator()

    with patch("backend.delegacao.enabled", return_value=False):
        with patch.object(orch, "_classify", return_value={
            "intent": "conversa",
            "complexity": "simple",
            "brain": "main"
        }):
            with patch.object(orch, "_main_brain", return_value="Resposta") as mock_main:
                result = orch.process("olá")

                # Comportamento intacto
                assert mock_main.called
                assert result.brain == "main"


def test_full_flow_atalho_to_codex():
    """Fluxo completo: input → should_delegate → _run_exec → Codex."""
    orch = Orchestrator()

    with patch("backend.delegacao.enabled", return_value=True):
        with patch("backend.delegacao.should_delegate", return_value=True):
            with patch("backend.brain_switch.dispatch") as mock_dispatch:
                mock_dispatch.return_value = "✓ Função criada e testada."

                result = orch.process("programa uma função que faz sort")

                # Verifica chamada ao dispatch com engine="codex"
                assert mock_dispatch.called
                call_args = mock_dispatch.call_args
                assert call_args.kwargs.get("engine") == "codex"
                assert "GUARDRAILS" in call_args.args[0]  # brief tem guardrails
                assert "git commit" in call_args.args[0].lower() or "git" in call_args.args[0].lower()


def test_disabled_ignores_should_delegate():
    """Com JAVIS_AUTO_CODEX=0, should_delegate é ignorado."""
    orch = Orchestrator()

    with patch("backend.delegacao.enabled", return_value=False):
        with patch("backend.delegacao.should_delegate", return_value=True):  # Mesmo que bata
            with patch.object(orch, "_classify", return_value={
                "intent": "conversa",
                "complexity": "simple",
                "brain": "main"
            }):
                with patch.object(orch, "_main_brain", return_value="Claude responde"):
                    result = orch.process("programa X")

                    # _main_brain foi chamado, não Codex
                    assert result.brain == "main"
