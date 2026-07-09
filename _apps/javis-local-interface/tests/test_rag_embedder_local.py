from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from types import ModuleType

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _blocked_openai() -> ModuleType:
    module = ModuleType("openai")

    def _getattr(name: str):
        raise AssertionError(f"openai import should not happen on local RAG path: {name}")

    module.__getattr__ = _getattr  # type: ignore[attr-defined]
    return module


def _knowledge(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVIS_RAG_EMBEDDER", "local")
    monkeypatch.setenv("JAVIS_RAG", "legacy")
    monkeypatch.setitem(sys.modules, "openai", _blocked_openai())
    sys.modules.pop("knowledge", None)
    knowledge = importlib.import_module("knowledge")
    monkeypatch.setattr(knowledge, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(knowledge, "INDEX_FILE", tmp_path / "_memoria" / "knowledge_index.json")
    monkeypatch.setattr(knowledge, "_external_vaults", lambda: [])
    monkeypatch.setattr(knowledge, "_hybrid", lambda: None)
    return knowledge


def test_local_embedder_builds_and_searches_without_openai(monkeypatch, tmp_path):
    knowledge = _knowledge(monkeypatch, tmp_path)
    note = tmp_path / "_memoria" / "note.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("alpha beta alpha", encoding="utf-8")

    build = knowledge.build_index(force=True)
    hits = knowledge.search("alpha")

    assert build["status"] == "ok"
    assert build["chunks"] > 0
    assert hits
    assert hits[0]["score"] >= 0
    assert knowledge._selected_embedder().name == "local"


def test_local_embedder_is_deterministic(monkeypatch, tmp_path):
    knowledge = _knowledge(monkeypatch, tmp_path)
    embedder = knowledge._selected_embedder()

    left = embedder.embed(["texto local deterministico"])[0]
    right = embedder.embed(["texto local deterministico"])[0]
    other = embedder.embed(["outra frase"])[0]

    assert left == right
    assert left != other
    assert len(left) == 256
