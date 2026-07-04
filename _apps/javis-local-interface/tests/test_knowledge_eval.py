"""Testes da avaliação de retrieval (knowledge_eval): métricas + A/B híbrido×legado.

Métricas testadas de forma determinística com um retriever controlado; e um teste
de integração real que prova o híbrido recuperando por palavra-chave onde o legado
(só semântico) erra. Sem OpenAI (embeddings fake) e sem tocar o vault real.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import db                       # noqa: E402
import knowledge as k          # noqa: E402
import knowledge_hybrid as kh  # noqa: E402
import knowledge_eval as ke    # noqa: E402

_VOCAB = ["python", "javis", "rag", "voz", "memoria", "churrasco"]


def _fake_embed(texts):
    return [[float(t.lower().count(w)) for w in _VOCAB] for t in texts]


# --- métricas (retriever controlado) ---------------------------------------
def test_metrics_hybrid_vs_legacy(monkeypatch):
    def fake_retrieve(mode, q, kk):
        if mode == "hybrid":
            hits = [{"path": "docs/target.md"}, {"path": "x.md"}, {"path": "y.md"}]
        else:  # legado erra: target só na 2ª posição
            hits = [{"path": "x.md"}, {"path": "docs/target.md"}, {"path": "y.md"}]
        return hits[:kk]

    monkeypatch.setattr(ke, "_retrieve", fake_retrieve)
    golden = [{"q": "achar target", "relevant": ["target.md"]}]
    r = ke.evaluate(golden, k=3)

    assert r["status"] == "ok"
    h, l = r["modes"]["hybrid"], r["modes"]["legacy"]
    assert h["hit_rate"] == 1.0 and l["hit_rate"] == 1.0
    assert h["mrr"] == 1.0        # target no topo
    assert l["mrr"] == 0.5        # target na posição 2
    assert r["modes"]["delta"]["mrr"] == 0.5


def test_no_golden(monkeypatch):
    monkeypatch.setattr(ke, "load_golden", lambda: [])
    r = ke.evaluate()
    assert r["status"] == "no_golden"


def test_recall_precision_math(monkeypatch):
    def fake_retrieve(mode, q, kk):
        return [{"path": "a/alpha.md"}, {"path": "b/beta.md"}, {"path": "c/gamma.md"}][:kk]
    monkeypatch.setattr(ke, "_retrieve", fake_retrieve)
    # 2 fontes relevantes, ambas no top-3 → recall 1.0; 2 de 3 hits relevantes → precision 0.667
    golden = [{"q": "x", "relevant": ["alpha.md", "beta.md"]}]
    r = ke.evaluate(golden, k=3, modes=("hybrid",))
    m = r["modes"]["hybrid"]
    assert m["recall@k"] == 1.0
    assert m["precision@k"] == round(2 / 3, 4)
    assert m["mrr"] == 1.0


# --- integração real: híbrido acha por BM25 onde o legado (semântico) falha --
def test_hybrid_beats_legacy_on_keyword(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "eval.db")
    monkeypatch.setattr(db, "_initialized", False)
    monkeypatch.setattr(k, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(k, "INDEX_FILE", tmp_path / "idx.json")   # não toca o JSON real
    monkeypatch.setattr(k, "_external_vaults", lambda: [])
    monkeypatch.setattr(k, "_embed_batch", _fake_embed)

    docs = {
        "a.md": "python rag javis",
        "c.md": "python voz memoria",
        "d.md": "python rag voz",
        "e.md": "python javis memoria",
        "b.md": "xptoproject metas trimestre relatorio anual",  # termo raro, zero vocab
    }
    files = []
    for name, txt in docs.items():
        p = tmp_path / name
        p.write_text(txt, encoding="utf-8")
        files.append(p)
    monkeypatch.setattr(k, "_iter_files", lambda: iter(files))

    kh._invalidate()
    k.build_index(force=True)     # popula JSON legado E o SQLite híbrido

    # query: termo raro (só em b.md) + termo comum. Legado (semântico) põe b.md
    # por último (vetor zero); híbrido acha via BM25.
    golden = [{"q": "xptoproject python", "relevant": ["b.md"]}]
    r = ke.evaluate(golden, k=3, modes=("hybrid", "legacy"))

    assert r["modes"]["hybrid"]["hit_rate"] == 1.0
    assert r["modes"]["legacy"]["hit_rate"] == 0.0
    assert r["modes"]["delta"]["recall@k"] > 0
