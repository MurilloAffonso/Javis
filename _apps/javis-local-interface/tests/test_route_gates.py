from __future__ import annotations

import asyncio
import importlib
import json
import sys
from io import BytesIO
from pathlib import Path

from starlette.datastructures import UploadFile

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


def _upload(name: str, content: bytes) -> UploadFile:
    return UploadFile(filename=name, file=BytesIO(content))


def _external_off(monkeypatch):
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "false")
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "false")
    monkeypatch.setenv("JAVIS_ENABLE_VP_EFFECTS", "false")


def _external_on(monkeypatch):
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_VP_EFFECTS", "true")


def _temp_db(monkeypatch, tmp_path):
    import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(db, "_initialized", False)


def test_external_adapters_off_blocks_llm_and_network_routes(monkeypatch):
    _external_off(monkeypatch)
    server = _server(monkeypatch)

    responses = [
        _json(asyncio.run(server.knowledge_dna(server.DnaReq(text="x"), x_javes_local_token=TEST_TOKEN))),
        _json(asyncio.run(server.knowledge_ingest("", x_javes_local_token=TEST_TOKEN))),
        _json(asyncio.run(server.knowledge_reindex(x_javes_local_token=TEST_TOKEN))),
        _json(asyncio.run(server.knowledge_search("x", x_javes_local_token=TEST_TOKEN))),
        _json(asyncio.run(server.wa_analyze(
            server.WAAnalyzeRequest(text="x"),
            project_id=server.gate.CEREBRO_JAMPA_SCOPE,
            x_javes_local_token=TEST_TOKEN,
        ))),
        _json(asyncio.run(server.upload_file(_upload("safe.txt", b"hello"), x_javes_local_token=TEST_TOKEN))),
    ]

    assert all(r["status"] == "disabled_by_default" for r in responses)
    assert all(r["reason"] == "requires_explicit_enable" for r in responses)


def test_approval_required_before_expensive_or_writing_routes(monkeypatch, tmp_path):
    _external_on(monkeypatch)
    server = _server(monkeypatch)
    _temp_db(monkeypatch, tmp_path)

    dna = _json(asyncio.run(server.knowledge_dna(server.DnaReq(text="x"), x_javes_local_token=TEST_TOKEN)))
    ingest = _json(asyncio.run(server.knowledge_ingest("", x_javes_local_token=TEST_TOKEN)))
    upload = _json(asyncio.run(server.upload_file(_upload("safe.txt", b"hello"), x_javes_local_token=TEST_TOKEN)))
    save_voice = _json(asyncio.run(server.wa_save_voice(
        server.WASaveRequest(content="voice"),
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        x_javes_local_token=TEST_TOKEN,
    )))

    for body in (dna, ingest, upload, save_voice):
        assert body["status"] == "approval_required"
        assert body["reason"] == "human_approval_required"


def test_ingest_path_traversal_blocks_before_execution(monkeypatch):
    _external_on(monkeypatch)
    server = _server(monkeypatch)

    body = _json(asyncio.run(server.knowledge_ingest("../segredo", x_javes_local_token=TEST_TOKEN)))

    assert body["status"] == "blocked"
    assert body["reason"] == "path_traversal"


def test_upload_blocks_dangerous_extensions(monkeypatch):
    _external_on(monkeypatch)
    server = _server(monkeypatch)

    for filename in ("bad.exe", "bad.bat", "bad.ps1", "bad.sh"):
        body = _json(asyncio.run(server.upload_file(_upload(filename, b"x"), x_javes_local_token=TEST_TOKEN)))
        assert body["status"] == "blocked"
        assert body["reason"] == "blocked_file_type"


def test_upload_blocks_oversized_file_before_analysis(monkeypatch, tmp_path):
    _external_on(monkeypatch)
    server = _server(monkeypatch)
    _temp_db(monkeypatch, tmp_path)
    monkeypatch.setattr(server.gate, "MAX_UPLOAD_BYTES", 4)
    import repositories as repo
    approval_id = repo.approvals.add(
        "upload test",
        kind="route_gate",
        action="upload",
        route="/upload",
        risk_level="high",
    )
    repo.approvals.decide(approval_id, True, approved_by="test")

    body = _json(asyncio.run(server.upload_file(
        _upload("safe.txt", b"12345"),
        approval_id=approval_id,
        x_javes_local_token=TEST_TOKEN,
    )))

    assert body["status"] == "blocked"
    assert body["reason"] == "upload_too_large"
