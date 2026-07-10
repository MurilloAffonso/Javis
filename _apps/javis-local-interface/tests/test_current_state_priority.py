"""R2.2.1 — CURRENT_STATE.md é a fonte canônica do estado.

Prova que, ao montar o estado injetado no cérebro (briefing.estado_resumido) e a
saudação, o CURRENT_STATE.md PREVALECE sobre os roadmaps antigos
(estado-atual.md / proximos-passos.md). Não roda servidor, não abre .env.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import briefing  # noqa: E402

CANONICO = """# CURRENT STATE — Javes (FONTE CANÔNICA)

## 🎯 PRÓXIMO PASSO OFICIAL

**R2.3 — Provider Registry + javes doctor**

R1/R2/R2.1/R2.2 concluídos.
"""

ROADMAP_ANTIGO_PROXIMOS = """# Próximos Passos — Javis

## 🎯 FRENTE ATIVA
- [ ] ROADMAP-ANTIGO-OBSOLETO: nenhuma frente escolhida
"""

ROADMAP_ANTIGO_ESTADO = """# Estado Atual — Javis

## Sessões recentes
- ROADMAP-ANTIGO-OBSOLETO: sessão velha
"""


@pytest.fixture
def estado_dir(tmp_path, monkeypatch):
    """Isola _estado/ e _logs/ num tmp e limpa o cache do briefing."""
    monkeypatch.setattr(briefing, "ESTADO_DIR", tmp_path)
    monkeypatch.setattr(briefing, "LOGS_DIR", tmp_path / "_logs_vazio")
    briefing._CACHE.update(ts=0.0, estado="", saudacao="")
    yield tmp_path
    briefing._CACHE.update(ts=0.0, estado="", saudacao="")


def _escrever(dir_: Path, canonico: bool):
    (dir_ / "proximos-passos.md").write_text(ROADMAP_ANTIGO_PROXIMOS, encoding="utf-8")
    (dir_ / "estado-atual.md").write_text(ROADMAP_ANTIGO_ESTADO, encoding="utf-8")
    if canonico:
        (dir_ / "CURRENT_STATE.md").write_text(CANONICO, encoding="utf-8")


# --- Prioridade: canônico vence e vem ANTES do histórico -------------------
def test_estado_resumido_prioriza_canonico(estado_dir):
    _escrever(estado_dir, canonico=True)
    out = briefing.estado_resumido()

    assert "R2.3" in out                       # próximo passo canônico presente
    assert "ESTADO CANÔNICO" in out            # marcado como fonte de verdade
    # o canônico aparece ANTES de qualquer roadmap antigo
    pos_canonico = out.index("R2.3")
    pos_antigo = out.index("ROADMAP-ANTIGO-OBSOLETO")
    assert pos_canonico < pos_antigo


def test_saudacao_usa_proximo_passo_oficial(estado_dir):
    _escrever(estado_dir, canonico=True)
    saud = briefing.saudacao_proativa()
    assert "R2.3" in saud
    assert "Próximo passo oficial" in saud
    assert "ROADMAP-ANTIGO-OBSOLETO" not in saud


def test_proximo_passo_oficial_extraido(estado_dir):
    _escrever(estado_dir, canonico=True)
    assert briefing._proximo_passo_oficial().startswith("R2.3")


# --- Degradação: sem canônico, cai no comportamento antigo (sem quebrar) ---
def test_sem_canonico_degrada_para_roadmap_antigo(estado_dir):
    _escrever(estado_dir, canonico=False)
    out = briefing.estado_resumido()
    assert "ESTADO CANÔNICO" not in out
    # sem canônico, o roadmap antigo é o que sobra
    assert "ROADMAP-ANTIGO-OBSOLETO" in out

    saud = briefing.saudacao_proativa()
    assert "Próximo passo oficial" not in saud


def test_current_state_vazio_quando_ausente(estado_dir):
    _escrever(estado_dir, canonico=False)
    assert briefing._current_state() == ""
    assert briefing._proximo_passo_oficial() == ""
