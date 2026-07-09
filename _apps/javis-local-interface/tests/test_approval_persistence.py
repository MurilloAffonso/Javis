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


def test_sensitive_action_without_persisted_approval_returns_gate(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)

    body = _json(asyncio.run(server.knowledge_dna(
        server.DnaReq(text="x"),
        x_javes_local_token=TEST_TOKEN,
    )))

    assert body["status"] == "approval_required"
    assert body["reason"] == "human_approval_required"
    assert body["approval_id"]
    assert body["approval_status"] == "pending"


def test_approved_true_does_not_bypass_persisted_approval(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    monkeypatch.setitem(
        sys.modules,
        "dna_extractor",
        SimpleNamespace(extract_and_index=lambda *args: (_ for _ in ()).throw(AssertionError("executed"))),
    )

    body = _json(asyncio.run(server.knowledge_dna(
        server.DnaReq(text="x"),
        approved=True,
        x_javes_local_token=TEST_TOKEN,
    )))

    assert body["status"] == "approval_required"
    assert body["approved_param_ignored"] is True


def test_valid_persisted_approval_allows_controlled_action(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo

    approval_id = repo.approvals.add(
        "wa.save_voice test",
        kind="route_gate",
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        action="wa.save_voice",
        route="/wa/save-voice",
        risk_level="high",
    )
    repo.approvals.decide(approval_id, True, approved_by="test")
    monkeypatch.setitem(
        sys.modules,
        "wa_analyzer",
        SimpleNamespace(save_voice_doc=lambda content: "fake/voz-murillo.md"),
    )

    body = _json(asyncio.run(server.wa_save_voice(
        server.WASaveRequest(content="voice"),
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        approval_id=approval_id,
        x_javes_local_token=TEST_TOKEN,
    )))

    assert body == {"status": "ok", "file": "fake/voz-murillo.md"}
