from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _server(monkeypatch):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_VP_EFFECTS", "true")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", "test-local-token")
    return importlib.import_module("server")


def test_chat_scopes_rag_by_project_id(monkeypatch):
    server = _server(monkeypatch)
    import knowledge

    monkeypatch.setattr(server, "_is_fast_path", lambda *args, **kwargs: False)
    monkeypatch.setattr(server.command_router, "route", lambda text: {"intent": "conversa", "risk_level": "low"})

    seen = []

    def fake_answer_context(query, k=5, escopo=None):
        seen.append(escopo)
        return "VP-CHUNK" if escopo == "vp" else "CORE-CHUNK"

    monkeypatch.setattr(knowledge, "answer_context", fake_answer_context)

    def fake_respond(user_text, history=None, max_rounds=5, project_id=""):
        scope = knowledge.scope_for_project(project_id)
        ctx = knowledge.answer_context("pergunta", escopo=scope)
        return {
            "text": ctx,
            "intent": "buscar_conhecimento",
            "brain": "main",
            "status": "agent",
            "tools": [],
            "route": {"intent": "conversa"},
            "orch": None,
        }

    monkeypatch.setitem(sys.modules, "agent", SimpleNamespace(respond=fake_respond))

    core = server._brain("consulta comum", [], False, server.gate.CORE_SCOPE)
    vp = server._brain("consulta comum", [], False, server.gate.CEREBRO_JAMPA_SCOPE)

    assert core["text"] == "CORE-CHUNK"
    assert vp["text"] == "VP-CHUNK"
    assert seen == [["pessoal", "projeto"], "vp"]
