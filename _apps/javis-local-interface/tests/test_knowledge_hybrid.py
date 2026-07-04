"""Testes do RAG híbrido (knowledge_hybrid): build no SQLite + semântico + BM25 + RRF.

Roda sem OpenAI (embeddings fake, determinísticos) e sem tocar o vault real
(DB temporário + _iter_files monkeypatchado). Estilo pytest.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import db                       # noqa: E402
import knowledge as k          # noqa: E402
import knowledge_hybrid as kh  # noqa: E402

# vocabulário fake → embeddings determinísticos por contagem de termos
_VOCAB = ["python", "javis", "rag", "voz", "memoria", "churrasco"]


def _fake_embed(texts):
    out = []
    for t in texts:
        tl = t.lower()
        out.append([float(tl.count(w)) for w in _VOCAB] + [0.5])
    return out


@pytest.fixture
def hybrid(tmp_path, monkeypatch):
    # DB isolado (schema real é recriado no tmp)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis_test.db")
    monkeypatch.setattr(db, "_initialized", False)
    # vault isolado + embeddings fake (a key só destrava o caminho de embed;
    # _embed_batch está monkeypatchado, então nada sai para a OpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(k, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(k, "_external_vaults", lambda: [])
    monkeypatch.setattr(k, "_embed_batch", _fake_embed)

    docs = {
        "a.md": "Javis roda RAG local em python. memoria persistente.",
        "b.md": "Receita de churrasco com carne e sal grosso.",
        "c.md": "Pipeline de voz do Javis usa whisper. python e voz.",
    }
    files = []
    for name, txt in docs.items():
        p = tmp_path / name
        p.write_text(txt, encoding="utf-8")
        files.append(p)
    monkeypatch.setattr(k, "_iter_files", lambda: iter(files))

    kh._invalidate()
    return kh


def test_build_populates_sqlite(hybrid):
    res = hybrid.build_index(force=True)
    assert res["status"] == "ok"
    assert res["chunks"] >= 3
    assert res["embedded"] >= 3          # sem JSON cache → embeda tudo (fake)
    assert hybrid.available()


def test_hybrid_search_ranks_relevant_first(hybrid):
    hybrid.build_index(force=True)
    hits = hybrid.search("python voz do javis", k=3)
    assert hits
    # o doc de churrasco não pode ser o mais relevante
    assert "b.md" not in hits[0]["path"]
    assert hits[0]["sem"] > 0            # veio com sinal semântico


def test_bm25_keyword_recall(hybrid):
    hybrid.build_index(force=True)
    kw = hybrid._keyword("churrasco", 5)
    assert kw                            # FTS5 achou pelo termo
    hits = hybrid.search("churrasco", k=3)
    assert any("b.md" in h["path"] for h in hits)


def test_answer_context_filters_irrelevant(hybrid):
    hybrid.build_index(force=True)
    ctx = hybrid.answer_context("python voz do javis", k=3)
    assert ctx
    assert "churrasco" not in ctx.lower()


def test_incremental_reuses_vectors(hybrid, tmp_path):
    hybrid.build_index(force=True)
    # segundo build incremental sem mudanças → nada re-embeda
    res2 = hybrid.build_index(force=False)
    assert res2["embedded"] == 0
    assert res2["arquivos"] == 0


def test_rrf_fusion_prioritizes_overlap():
    sem = [(1, 0.9), (2, 0.5)]
    kw = [(2, 0), (3, 0)]
    ordered = kh._rrf(sem, kw, 5)
    ids = [cid for cid, _ in ordered]
    assert set(ids) == {1, 2, 3}
    assert ids[0] == 2                   # id 2 casa nos dois rankings → topo


def test_blob_roundtrip():
    v = [0.1, 0.2, 0.3, -0.4]
    back = np.frombuffer(kh._vec_to_blob(v), dtype=np.float32)
    assert np.allclose(back, v, atol=1e-6)


def test_fts_match_sanitizes_punctuation():
    m = kh._fts_match('quero "python" AND voz!')
    assert m is not None
    assert '"python"' in m and '"voz"' in m
    assert kh._fts_match("!!! ??? .") is None
