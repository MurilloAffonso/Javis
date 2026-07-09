from __future__ import annotations

import asyncio
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
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
    monkeypatch.setenv("JAVES_APPROVAL_TTL_MIN", "1")
    server = importlib.import_module("server")
    import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(db, "_initialized", False)
    return server


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def _old_iso(minutes: int = 5) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")


def test_expired_approval_blocks_and_is_marked_expired(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import db
    import repositories as repo

    monkeypatch.setitem(
        sys.modules,
        "wa_analyzer",
        SimpleNamespace(save_voice_doc=lambda content: "fake/voz-murillo.md"),
    )

    approval_id = repo.approvals.add(
        "ttl check",
        kind="route_gate",
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        action="wa.save_voice",
        route="/wa/save-voice",
        risk_level="high",
    )
    repo.approvals.decide(approval_id, True, approved_by="test")
    db.execute(
        "UPDATE approvals SET decided_at=?, updated_at=? WHERE id=?",
        (_old_iso(), _old_iso(), approval_id),
    )

    body = _json(asyncio.run(server.wa_save_voice(
        server.WASaveRequest(content="voice"),
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        approval_id=approval_id,
        x_javes_local_token=TEST_TOKEN,
    )))

    refreshed = repo.approvals.get(approval_id)

    assert body["status"] == "approval_required"
    assert body["approval_status"] == "expired"
    assert refreshed["status"] == "expired"
    assert refreshed["consumed_at"] is None
