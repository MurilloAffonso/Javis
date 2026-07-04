"""Testes do módulo delegacao — política de delegação Claude→Codex."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest
from delegacao import should_delegate, montar_brief, enabled


def test_should_delegate_programa():
    """Verbo 'programa' é execução."""
    assert should_delegate("programa uma função que faz X") is True


def test_should_delegate_implementa():
    """Verbo 'implementa' é execução."""
    assert should_delegate("implementa o algoritmo de sort") is True


def test_should_delegate_refatora():
    """Verbo 'refatora' é execução."""
    assert should_delegate("refatora o arquivo X") is True


def test_should_delegate_roda():
    """Verbo 'roda' é execução."""
    assert should_delegate("roda os testes do projeto") is True


def test_should_delegate_cria_arquivo():
    """Verbo 'cria' com arquivo é execução."""
    assert should_delegate("cria o arquivo main.py") is True


def test_should_delegate_corrige_bug():
    """Verbo 'corrige' é execução."""
    assert should_delegate("corrige o bug na linha 42") is True


def test_should_delegate_normal_pergunta():
    """Pergunta normal não delega."""
    assert should_delegate("qual é a capital do Brasil?") is False


def test_should_delegate_raciocinio():
    """Tarefa de raciocínio não delega."""
    assert should_delegate("analisa este código e explica o que faz") is False


def test_should_delegate_planning():
    """Planejamento não delega."""
    assert should_delegate("qual é a melhor estratégia pra organizar o projeto?") is False


def test_montar_brief_sem_plano():
    """montar_brief inclui preâmbulo de guarda."""
    result = montar_brief("programa uma função")
    assert "GUARDRAILS" in result
    assert "git commit" in result
    assert "git push" in result
    assert "programa uma função" in result


def test_montar_brief_com_plano():
    """montar_brief com plano inclui contexto."""
    result = montar_brief("programa X", plano="Use o algoritmo Y")
    assert "GUARDRAILS" in result
    assert "CONTEXTO" in result
    assert "algoritmo Y" in result


def test_enabled_default_false():
    """JAVIS_AUTO_CODEX default False."""
    os.environ.pop("JAVIS_AUTO_CODEX", None)
    assert enabled() is False


def test_enabled_true():
    """JAVIS_AUTO_CODEX=1 returns True."""
    os.environ["JAVIS_AUTO_CODEX"] = "1"
    assert enabled() is True
    os.environ.pop("JAVIS_AUTO_CODEX")


def test_enabled_case_insensitive():
    """JAVIS_AUTO_CODEX=true (case-insensitive)."""
    os.environ["JAVIS_AUTO_CODEX"] = "TRUE"
    assert enabled() is True
    os.environ.pop("JAVIS_AUTO_CODEX")
