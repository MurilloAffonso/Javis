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

TEST_TOKEN = "test-local-token"


def _server(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_VP_EFFECTS", "true")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    server = importlib.import_module("server")
    import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(db, "_initialized", False)
    return server


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def test_persisted_approval_writes_audit_trail_once(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    monkeypatch.setitem(
        sys.modules,
        "wa_analyzer",
        SimpleNamespace(save_voice_doc=lambda content: "fake/voz-murillo.md"),
    )

    approval_id = repo.approvals.add(
        "audit trail",
        kind="route_gate",
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        action="wa.save_voice",
        route="/wa/save-voice",
        risk_level="high",
        requested_by="murillo",
    )
    repo.approvals.decide(approval_id, True, approved_by="test")
    before = repo.logs.count()

    first = _json(asyncio.run(server.wa_save_voice(
        server.WASaveRequest(content="voice"),
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        approval_id=approval_id,
        x_javes_local_token=TEST_TOKEN,
    )))
    after_first = repo.logs.count()
    audit_log = repo.logs.recent(1)[0]

    second = _json(asyncio.run(server.wa_save_voice(
        server.WASaveRequest(content="voice"),
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        approval_id=approval_id,
        x_javes_local_token=TEST_TOKEN,
    )))
    after_second = repo.logs.count()

    assert first == {"status": "ok", "file": "fake/voz-murillo.md"}
    assert after_first == before + 1
    assert "approval_id=" in audit_log["message"]
    assert "route=/wa/save-voice" in audit_log["message"]
    assert "project_id=project:cerebro-jampa" in audit_log["message"]
    assert audit_log["intent"] == "wa.save_voice"
    assert second["status"] == "approval_required"
    assert second["approval_status"] == "consumed"
    assert after_second == after_first
