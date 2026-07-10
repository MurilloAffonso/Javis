from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import gate  # noqa: E402
import history_store  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", "test-local-token")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


def test_javes_core_cria_e_le_sessao():
    out = history_store.ensure_session(gate.CORE_SCOPE, "core-session")
    assert out["status"] == "ok"

    history_store.append(gate.CORE_SCOPE, "core-session", {"role": "user", "content": "status do Javes"})

    rows = history_store.load(gate.CORE_SCOPE, "core-session")
    assert [row["content"] for row in rows] == ["status do Javes"]


def test_project_cerebro_jampa_cria_sessao_separada():
    history_store.ensure_session(gate.CORE_SCOPE, "core-session")
    history_store.ensure_session(gate.CEREBRO_JAMPA_SCOPE, "jampa-session")

    assert history_store.get_session("core-session")["project_id"] == gate.CORE_SCOPE
    assert history_store.get_session("jampa-session")["project_id"] == gate.CEREBRO_JAMPA_SCOPE


def test_session_id_de_outro_projeto_retorna_scope_mismatch():
    history_store.ensure_session(gate.CEREBRO_JAMPA_SCOPE, "jampa-session")

    out = history_store.ensure_session(gate.CORE_SCOPE, "jampa-session")

    assert out["status"] == "blocked"
    assert out["reason"] == "project_scope_mismatch"


def test_chat_sem_project_id_usa_javes_core(monkeypatch):
    import server

    def fake_brain(text, history, use_conclave=False, project_id=gate.CORE_SCOPE):
        assert project_id == gate.CORE_SCOPE
        assert isinstance(history, list)
        return {
            "text": "ok core",
            "intent": "conversa",
            "brain": "fake",
            "status": "ok",
            "tools": [],
            "route": {"intent": "conversa", "risk_level": "none"},
            "orch": None,
        }

    monkeypatch.setattr(server, "_brain", fake_brain)
    req = server.ChatRequest(message="oi")

    resp = asyncio.run(server.chat(req, x_javes_local_token="test-local-token"))
    body = json.loads(bytes(resp.body))

    assert body["project_id"] == gate.CORE_SCOPE
    assert body["session_id"] == history_store.DEFAULT_SESSION_ID
    assert body["response"] == "ok core"


def test_frontend_envia_project_id_e_session_id():
    app_js = (Path(__file__).resolve().parents[1] / "frontend" / "command-center" / "app.js").read_text(encoding="utf-8")
    chat_js = (Path(__file__).resolve().parents[1] / "frontend" / "command-center" / "js" / "views" / "chat.js").read_text(encoding="utf-8")

    assert "projectIdForAgent" in app_js
    assert "getChatSessionId" in app_js
    assert "setChatSessionId" in app_js
    assert "payload.project_id = projectId" in chat_js
    assert "session_id: sessionId" in chat_js
