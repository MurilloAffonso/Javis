from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _knowledge(monkeypatch, tmp_path, embedder: str):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVIS_RAG_EMBEDDER", embedder)
    monkeypatch.setenv("JAVIS_RAG", "legacy")
    sys.modules.pop("knowledge", None)
    knowledge = importlib.import_module("knowledge")
    monkeypatch.setattr(knowledge, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(knowledge, "INDEX_FILE", tmp_path / "_memoria" / "knowledge_index.json")
    monkeypatch.setattr(knowledge, "_hybrid", lambda: None)
    return knowledge


@pytest.mark.parametrize("embedder", ["openai", "local", "ollama"])
def test_rag_scope_keeps_core_and_vp_isolated_for_each_embedder(monkeypatch, tmp_path, embedder):
    knowledge = _knowledge(monkeypatch, tmp_path, embedder)

    hits = [
        {"path": "_memoria/dna/core.md", "chunk": "core chunk", "score": 0.91},
        {"path": "[CEREBRO.JAMPA] docs/vp.md", "chunk": "vp chunk", "score": 0.88},
    ]

    monkeypatch.setattr(knowledge, "search", lambda query, k=5: hits)
    monkeypatch.setattr("categoria.de_path", lambda path: "vp" if path.startswith("[") else "projeto")

    assert knowledge._selected_embedder().name == embedder

    core = knowledge.answer_context("x", escopo=knowledge.scope_for_project("javes-core"))
    vp = knowledge.answer_context("x", escopo=knowledge.scope_for_project("project:cerebro-jampa"))

    assert "core chunk" in core
    assert "vp chunk" not in core
    assert "vp chunk" in vp
    assert "core chunk" not in vp
