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


def _server(monkeypatch):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
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


def test_external_adapters_off_blocks_llm_and_network_routes(monkeypatch):
    _external_off(monkeypatch)
    server = _server(monkeypatch)

    responses = [
        _json(asyncio.run(server.knowledge_dna(server.DnaReq(text="x")))),
        _json(asyncio.run(server.knowledge_ingest(""))),
        _json(asyncio.run(server.knowledge_reindex())),
        _json(asyncio.run(server.knowledge_search("x"))),
        _json(asyncio.run(server.wa_analyze(
            server.WAAnalyzeRequest(text="x"),
            project_id=server.gate.CEREBRO_JAMPA_SCOPE,
        ))),
        _json(asyncio.run(server.upload_file(_upload("safe.txt", b"hello"), approved=True))),
    ]

    assert all(r["status"] == "disabled_by_default" for r in responses)
    assert all(r["reason"] == "requires_explicit_enable" for r in responses)


def test_approval_required_before_expensive_or_writing_routes(monkeypatch):
    _external_on(monkeypatch)
    server = _server(monkeypatch)

    dna = _json(asyncio.run(server.knowledge_dna(server.DnaReq(text="x"))))
    ingest = _json(asyncio.run(server.knowledge_ingest("")))
    upload = _json(asyncio.run(server.upload_file(_upload("safe.txt", b"hello"))))
    save_voice = _json(asyncio.run(server.wa_save_voice(
        server.WASaveRequest(content="voice"),
        project_id=server.gate.CEREBRO_JAMPA_SCOPE,
    )))

    for body in (dna, ingest, upload, save_voice):
        assert body["status"] == "approval_required"
        assert body["reason"] == "human_approval_required"


def test_ingest_path_traversal_blocks_before_execution(monkeypatch):
    _external_on(monkeypatch)
    server = _server(monkeypatch)

    body = _json(asyncio.run(server.knowledge_ingest("../segredo", approved=True)))

    assert body["status"] == "blocked"
    assert body["reason"] == "path_traversal"


def test_upload_blocks_dangerous_extensions(monkeypatch):
    _external_on(monkeypatch)
    server = _server(monkeypatch)

    for filename in ("bad.exe", "bad.bat", "bad.ps1", "bad.sh"):
        body = _json(asyncio.run(server.upload_file(_upload(filename, b"x"), approved=True)))
        assert body["status"] == "blocked"
        assert body["reason"] == "blocked_file_type"


def test_upload_blocks_oversized_file_before_analysis(monkeypatch):
    _external_on(monkeypatch)
    server = _server(monkeypatch)
    monkeypatch.setattr(server.gate, "MAX_UPLOAD_BYTES", 4)

    body = _json(asyncio.run(server.upload_file(_upload("safe.txt", b"12345"), approved=True)))

    assert body["status"] == "blocked"
    assert body["reason"] == "upload_too_large"
