from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _knowledge(monkeypatch, external_adapters: bool = True):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true" if external_adapters else "false")
    monkeypatch.setenv("JAVIS_RAG_EMBEDDER", "ollama")
    monkeypatch.setenv("JAVIS_OLLAMA_EMBED_MODEL", "nomic-embed-text")
    sys.modules.pop("knowledge", None)
    return importlib.import_module("knowledge")


def test_ollama_embedder_posts_to_local_embed_endpoint(monkeypatch):
    knowledge = _knowledge(monkeypatch)
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeHTTPResponse({"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    monkeypatch.setattr(knowledge.urllib.request, "urlopen", fake_urlopen)

    # embedder cru, já aquecido (warm-up testado à parte) → posta o batch real
    knowledge._OllamaEmbedder._warmed = True
    vectors = knowledge._OllamaEmbedder().embed(["alpha", "beta"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["url"] == "http://127.0.0.1:11434/api/embed"
    assert captured["payload"] == {"model": "nomic-embed-text", "input": ["alpha", "beta"]}
    assert captured["timeout"] >= 1.0


def test_ollama_embedder_requires_external_adapters(monkeypatch):
    # O embedder CRU recusa sem o flag (garantia de gate no processo externo).
    knowledge = _knowledge(monkeypatch, external_adapters=False)

    with pytest.raises(RuntimeError, match="JAVIS_ENABLE_EXTERNAL_ADAPTERS"):
        knowledge._OllamaEmbedder().embed(["alpha"])


def test_selected_embedder_falls_back_to_local_when_ollama_down(monkeypatch):
    # Default (ollama) indisponível → cai para local (offline), NUNCA openai,
    # e nunca trava a busca.
    knowledge = _knowledge(monkeypatch)
    knowledge._OllamaEmbedder._warmed = False

    def boom(req, timeout):
        raise knowledge.urllib.error.URLError("connection refused")

    monkeypatch.setattr(knowledge.urllib.request, "urlopen", boom)
    # se openai for tocado, o teste falha de propósito
    monkeypatch.setattr(knowledge, "_embed_batch",
                        lambda texts: (_ for _ in ()).throw(AssertionError("openai não deve ser tocado")))

    vectors = knowledge._selected_embedder().embed(["alpha", "beta"])

    assert len(vectors) == 2
    assert all(isinstance(v, list) and v for v in vectors)
