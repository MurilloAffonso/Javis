"""Testes do brain_switch.dispatch — override de engine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest
from unittest.mock import patch, Mock
import brain_switch


def test_dispatch_engine_override_codex():
    """engine='codex' força Codex mesmo que get_active() retorne claude."""
    mock_code_agent = Mock()
    mock_code_agent.available.return_value = True
    mock_code_agent.dispatch.return_value = "Codex rodou"

    mock_claude_exec = Mock()
    mock_claude_exec.available.return_value = False

    with patch.dict('sys.modules', {'code_agent': mock_code_agent, 'claude_exec': mock_claude_exec}):
        with patch("brain_switch.get_active", return_value="claude"):
            result = brain_switch.dispatch("programa X", engine="codex")
            assert mock_code_agent.dispatch.called
            assert result == "Codex rodou"


def test_dispatch_engine_none_uses_active():
    """engine=None usa get_active() normal."""
    mock_claude_exec = Mock()
    mock_claude_exec.available.return_value = True
    mock_claude_exec.dispatch.return_value = "Claude rodou"

    mock_code_agent = Mock()
    mock_code_agent.available.return_value = False

    with patch.dict('sys.modules', {'claude_exec': mock_claude_exec, 'code_agent': mock_code_agent}):
        with patch("brain_switch.get_active", return_value="claude"):
            result = brain_switch.dispatch("programa X", engine=None)
            assert mock_claude_exec.dispatch.called
            assert result == "Claude rodou"


def test_dispatch_engine_invalid():
    """engine inválida lança ValueError."""
    with pytest.raises(ValueError, match="engine deve ser"):
        brain_switch.dispatch("X", engine="invalid")
