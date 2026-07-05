"""knowledge_eval.py — avaliação de retrieval do Javis (item 2 do roadmap mega-brain).

Mede a qualidade do RAG com um conjunto de **perguntas-douradas** (golden set) e
compara os dois retrievers lado a lado:

  • HÍBRIDO  → knowledge_hybrid (semântico + BM25 + RRF)
  • LEGADO   → knowledge (índice JSON, cosine puro)

Métricas por pergunta e agregadas: hit@k, recall@k, precision@k, MRR.

Golden set (lista):
    [{"q": "pergunta...", "relevant": ["trecho-de-path", ...]}, ...]
Um hit conta como acerto se algum trecho de `relevant` aparece no path do
resultado (case-insensitive). Curar em `_memoria/rag_eval_golden.json`.

Uso:
    python knowledge_eval.py [k]         # imprime JSON comparativo
    GET /knowledge/eval?k=5              # via API
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent
JAVIS_ROOT = _BACKEND.parents[2]
GOLDEN_FILE = JAVIS_ROOT / "_memoria" / "rag_eval_golden.json"


def _is_relevant(path: str, relevant: list[str]) -> bool:
    p = (path or "").lower()
    return any(r.lower() in p for r in relevant if r)


def _retrieve(mode: str, query: str, k: int) -> list[dict]:
    """Retorna os hits de um dos retrievers. 'hybrid'/'reranked' chamam o módulo
    híbrido (rerank off/on); 'legacy' força o índice JSON via flag JAVIS_RAG."""
    if mode in ("hybrid", "reranked"):
        import knowledge_hybrid as kh
        return kh.search(query, k, rerank=(mode == "reranked"))
    import knowledge
    old = os.environ.get("JAVIS_RAG")
    os.environ["JAVIS_RAG"] = "legacy"
    try:
        return knowledge.search(query, k)
    finally:
        if old is None:
            os.environ.pop("JAVIS_RAG", None)
        else:
            os.environ["JAVIS_RAG"] = old


def _score_one(hits: list[dict], relevant: list[str], k: int) -> dict:
    hits = hits[:k]
    flags = [_is_relevant(h.get("path", ""), relevant) for h in hits]
    matched = set()
    for h in hits:
        p = (h.get("path", "") or "").lower()
        for r in relevant:
            if r and r.lower() in p:
                matched.add(r.lower())
    denom = max(len([r for r in relevant if r]), 1)
    n_rel_hits = sum(flags)
    rr = 0.0
    for i, f in enumerate(flags):
        if f:
            rr = 1.0 / (i + 1)
            break
    return {
        "hit": bool(n_rel_hits),
        "recall": len(matched) / denom,
        "precision": n_rel_hits / max(len(hits), 1),
        "rr": rr,
        "topk_paths": [h.get("path") for h in hits],
    }


def load_golden(path: str | None = None) -> list[dict]:
    p = Path(path) if path else GOLDEN_FILE
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("golden", [])
    except Exception:
        return []


def evaluate(golden: list[dict] | None = None, k: int = 5,
             modes: tuple[str, ...] = ("hybrid", "legacy")) -> dict:
    """Roda o golden set em cada retriever e devolve métricas + delta hybrid−legacy."""
    golden = golden if golden is not None else load_golden()
    if not golden:
        return {"status": "no_golden",
                "message": f"Sem golden set. Crie {GOLDEN_FILE} — lista de {{q, relevant}}."}

    results: dict = {}
    for mode in modes:
        per, agg = [], {"hit": 0.0, "recall": 0.0, "precision": 0.0, "mrr": 0.0}
        for case in golden:
            q = case.get("q") or case.get("query") or ""
            rel = case.get("relevant") or case.get("paths") or []
            try:
                hits = _retrieve(mode, q, k)
            except Exception:
                hits = []
            s = _score_one(hits, rel, k)
            s["q"] = q
            per.append(s)
            agg["hit"] += 1 if s["hit"] else 0
            agg["recall"] += s["recall"]
            agg["precision"] += s["precision"]
            agg["mrr"] += s["rr"]
        n = len(golden)
        results[mode] = {
            "k": k, "n": n,
            "hit_rate": round(agg["hit"] / n, 4),
            "recall@k": round(agg["recall"] / n, 4),
            "precision@k": round(agg["precision"] / n, 4),
            "mrr": round(agg["mrr"] / n, 4),
            "per_question": per,
        }

    if "hybrid" in results and "legacy" in results:
        h, l = results["hybrid"], results["legacy"]
        results["delta"] = {m: round(h[m] - l[m], 4)
                            for m in ("hit_rate", "recall@k", "precision@k", "mrr")}
    return {"status": "ok", "modes": results}


if __name__ == "__main__":
    import sys
    kk = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(json.dumps(evaluate(k=kk), ensure_ascii=False, indent=2))
