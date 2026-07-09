from __future__ import annotations

import asyncio
import importlib
import json
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
    return importlib.import_module("server")


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def test_project_id_required_for_vp_jampa_task_and_wa_routes(monkeypatch):
    server = _server(monkeypatch)

    bodies = [
        _json(asyncio.run(server.vp_passeios_add(
            server.VPPasseioRequest(tipo="seixas", data="2026-07-09"),
        ))),
        _json(asyncio.run(server.jampa_squad_run(
            server.JampaSquadRequest(tarefa="planejar"),
        ))),
        _json(asyncio.run(server.task_run_studio("task-1"))),
        _json(asyncio.run(server.wa_analyze(server.WAAnalyzeRequest(text="x")))),
        _json(asyncio.run(server.wa_save_voice(server.WASaveRequest(content="x")))),
    ]

    assert all(body["status"] == "blocked" for body in bodies)
    assert all(body["reason"] == "project_id_required" for body in bodies)
    assert all(body["scope"] == server.gate.CEREBRO_JAMPA_SCOPE for body in bodies)


def test_wrong_project_id_is_blocked(monkeypatch):
    server = _server(monkeypatch)

    body = _json(asyncio.run(server.jampa_squad_run(
        server.JampaSquadRequest(tarefa="planejar"),
        project_id="javes-core",
    )))

    assert body["status"] == "blocked"
    assert body["reason"] == "project_id_mismatch"
    assert body["scope"] == server.gate.CEREBRO_JAMPA_SCOPE


def test_correct_project_id_allows_safe_template_gate(monkeypatch):
    server = _server(monkeypatch)
    monkeypatch.setitem(
        sys.modules,
        "studio",
        SimpleNamespace(run_studio=lambda task_id: {"ok": True, "task_id": task_id}),
    )

    body = _json(asyncio.run(server.task_run_studio(
        "task-1",
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
    )))

    assert body == {"ok": True, "task_id": "task-1"}


def test_javes_core_does_not_load_cerebro_jampa_implicitly(monkeypatch):
    server = _server(monkeypatch)
    import knowledge

    assert knowledge._external_vaults() == []
    body = _json(asyncio.run(server.wa_analyze(
        server.WAAnalyzeRequest(text="x"),
        project_id="javes-core",
    )))
    assert body["reason"] == "project_id_mismatch"
