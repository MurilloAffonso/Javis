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
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    return importlib.import_module("server")


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def test_sensitive_route_without_local_token_is_blocked(monkeypatch):
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    server = _server(monkeypatch)

    body = _json(asyncio.run(server.knowledge_graph_build()))

    assert body["status"] == "blocked"
    assert body["reason"] == "unauthorized_local_token_required"


def test_sensitive_route_with_local_token_reaches_next_gate(monkeypatch):
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "false")
    server = _server(monkeypatch)

    body = _json(asyncio.run(server.knowledge_graph_build(x_javes_local_token=TEST_TOKEN)))

    assert body["status"] == "disabled_by_default"
    assert body["capability"] == "local_actions"


def test_invalid_local_token_is_blocked(monkeypatch):
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    server = _server(monkeypatch)

    body = _json(asyncio.run(server.knowledge_graph_build(x_javes_local_token="wrong")))

    assert body["status"] == "blocked"
    assert body["reason"] == "unauthorized_local_token_invalid"
