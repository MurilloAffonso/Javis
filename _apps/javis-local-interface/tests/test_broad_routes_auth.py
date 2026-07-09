from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

TEST_TOKEN = "test-local-token"


def _server(monkeypatch):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_VP_EFFECTS", "true")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    return importlib.import_module("server")


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def test_broad_routes_require_local_auth_first(monkeypatch):
    server = _server(monkeypatch)

    bodies = [
        _json(asyncio.run(server.chat(server.ChatRequest(message="oi", project_id=""),))),
        _json(asyncio.run(server.chat_stream(server.ChatRequest(message="oi", project_id="")))),
        _json(asyncio.run(server.voice_input(server.VoiceRequest(transcript="oi", project_id="")))),
        _json(asyncio.run(server.voice_stream(server.VoiceRequest(transcript="oi", project_id="")))),
        _json(asyncio.run(server.agents_run(server.AgentRunRequest(agent_id="nova", task="x")))),
        _json(asyncio.run(server.train_youtube(server.TrainRequest(url="https://youtube.com/watch?v=x")))),
        _json(asyncio.run(server.browser_run(server.BrowserRequest(task="abrir site")))),
    ]

    assert all(body["status"] == "blocked" for body in bodies)
    assert all(body["reason"] == "unauthorized_local_token_required" for body in bodies)
