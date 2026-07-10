from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import categoria  # noqa: E402
import gate  # noqa: E402
import knowledge  # noqa: E402


class FakeHybrid:
    def __init__(self):
        self.calls = []

    def search(self, query, k, escopo=None):
        self.calls.append(("search", query, k, escopo))
        return [{"path": "_estado/CURRENT_STATE.md", "chunk": "R3", "score": 1.0, "categoria": "projeto"}]

    def answer_context(self, query, k, escopo=None):
        self.calls.append(("answer_context", query, k, escopo))
        return "contexto"


def test_rag_javes_core_exclui_documentos_vp(monkeypatch):
    fake = FakeHybrid()
    monkeypatch.setattr(knowledge, "_hybrid", lambda: fake)

    knowledge.search("fases atuais", project_id=gate.CORE_SCOPE)

    assert fake.calls[-1][3] == ["pessoal", "projeto"]


def test_rag_jampa_exige_project_id_explicito(monkeypatch):
    fake = FakeHybrid()
    monkeypatch.setattr(knowledge, "_hybrid", lambda: fake)

    knowledge.search("lead jampa", project_id=gate.CEREBRO_JAMPA_SCOPE)

    assert fake.calls[-1][3] == "vp"


def test_busca_sem_project_id_usa_javes_core(monkeypatch):
    fake = FakeHybrid()
    monkeypatch.setattr(knowledge, "_hybrid", lambda: fake)

    knowledge.search("estado atual")

    assert fake.calls[-1][3] == ["pessoal", "projeto"]


def test_current_state_pertence_ao_contexto_javes_core():
    assert categoria.de_path("_estado/CURRENT_STATE.md") == "projeto"
    assert "projeto" in knowledge.scope_for_project(gate.CORE_SCOPE)
    assert knowledge.scope_for_project(gate.CEREBRO_JAMPA_SCOPE) == "vp"
