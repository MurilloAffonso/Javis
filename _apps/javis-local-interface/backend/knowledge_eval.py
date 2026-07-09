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
    python knowledge_eval.py [k] --embedders
    GET /knowledge/eval?k=5              # via API
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent
JAVIS_ROOT = _BACKEND.parents[2]
GOLDEN_FILE = JAVIS_ROOT / "_memoria" / "rag_eval_golden.json"
EMBEDDER_PROVIDERS = ("openai", "local", "ollama")


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


def _provider_skip_note(provider: str) -> str:
    if provider in ("openai", "ollama"):
        import gate
        blocked = gate.require_external_adapters(f"knowledge_eval.{provider}_embed")
        if blocked:
            flag = blocked.get("flag", "JAVIS_ENABLE_EXTERNAL_ADAPTERS")
            return f"external_adapters desabilitado ({flag}); provider {provider} pulado."
    if provider == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
        return "OPENAI_API_KEY ausente; provider openai pulado."
    return ""


def _selected_provider(provider: str):
    import knowledge
    old = os.environ.get("JAVIS_RAG_EMBEDDER")
    os.environ["JAVIS_RAG_EMBEDDER"] = provider
    try:
        return knowledge._selected_embedder()
    finally:
        if old is None:
            os.environ.pop("JAVIS_RAG_EMBEDDER", None)
        else:
            os.environ["JAVIS_RAG_EMBEDDER"] = old


def _eval_path(path: Path, ext_roots: list[Path]) -> str:
    import knowledge
    try:
        return str(path.relative_to(knowledge.JAVIS_ROOT))
    except ValueError:
        for root in ext_roots:
            try:
                return f"[{root.name}] " + str(path.relative_to(root))
            except ValueError:
                continue
    return str(path)


def _load_eval_corpus() -> list[dict]:
    import knowledge
    corpus: list[dict] = []
    ext_roots = knowledge._external_vaults()
    for raw_path in knowledge._iter_files():
        path = Path(raw_path)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = _eval_path(path, ext_roots)
        for chunk in knowledge._chunks(text):
            corpus.append({"path": rel, "chunk": chunk})
    return corpus


def _rank_by_vectors(query_vec: list[float], corpus: list[dict],
                     corpus_vecs: list[list[float]], k: int) -> list[dict]:
    import knowledge
    scored = [
        {
            "path": item["path"],
            "chunk": item["chunk"],
            "score": knowledge._cosine(query_vec, vec),
        }
        for item, vec in zip(corpus, corpus_vecs)
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def _metrics_from_cases(per: list[dict], k: int) -> dict:
    n = len(per)
    return {
        "k": k,
        "n": n,
        "hit_rate": round(sum(1 if p["hit"] else 0 for p in per) / n, 4),
        "recall@k": round(sum(p["recall"] for p in per) / n, 4),
        "precision@k": round(sum(p["precision"] for p in per) / n, 4),
        "mrr": round(sum(p["rr"] for p in per) / n, 4),
        "per_question": per,
    }


def _evaluate_embedder(provider: str, golden: list[dict], k: int) -> dict:
    note = _provider_skip_note(provider)
    if note:
        return {"status": "skipped", "note": note}

    corpus = _load_eval_corpus()
    if not corpus:
        return {"status": "skipped", "note": "Corpus de avaliação vazio."}

    try:
        embedder = _selected_provider(provider)
        corpus_vecs = embedder.embed([item["chunk"] for item in corpus])
        query_vecs = embedder.embed([
            case.get("q") or case.get("query") or "" for case in golden
        ])
    except Exception as exc:
        return {"status": "skipped", "note": f"Provider {provider} indisponivel: {exc}"}

    if len(corpus_vecs) != len(corpus) or len(query_vecs) != len(golden):
        return {"status": "skipped", "note": f"Provider {provider} retornou vetores incompletos."}

    per = []
    for case, qvec in zip(golden, query_vecs):
        q = case.get("q") or case.get("query") or ""
        rel = case.get("relevant") or case.get("paths") or []
        hits = _rank_by_vectors(qvec, corpus, corpus_vecs, k)
        score = _score_one(hits, rel, k)
        score["q"] = q
        per.append(score)
    out = _metrics_from_cases(per, k)
    out["status"] = "ok"
    return out


def _recommend_default(embedders: dict) -> str:
    ok = {name: data for name, data in embedders.items() if data.get("status") == "ok"}
    local = ok.get("local")
    openai = ok.get("openai")
    ollama = ok.get("ollama")

    if not local:
        return "Manter openai: o provider local nao produziu baseline offline valido."

    def quality(data: dict) -> tuple[float, float, float, float]:
        return (data["recall@k"], data["mrr"], data["hit_rate"], data["precision@k"])

    if openai:
        alternatives = {name: ok[name] for name in ("local", "ollama") if name in ok}
        best_name, best = max(alternatives.items(), key=lambda item: quality(item[1]))
        if quality(best) >= quality(openai):
            return f"{best_name} e candidato a default: empatou ou superou openai em recall@k/MRR."
        return "Manter openai: nenhum provider local superou o baseline openai nas metricas medidas."

    if ollama and quality(ollama) > quality(local):
        return "Ollama e candidato a default local: superou local em recall@k/MRR, sujeito a latencia e gate."
    return "Nao mudar default ainda: so o provider local rodou; falta baseline openai/ollama acessivel."


def evaluate_embedders(golden: list[dict] | None = None, k: int = 5,
                       providers: tuple[str, ...] = EMBEDDER_PROVIDERS) -> dict:
    """Compara providers de embedding no mesmo corpus, sem sobrescrever o índice real."""
    golden = golden if golden is not None else load_golden()
    if not golden:
        return {"status": "no_golden",
                "message": f"Sem golden set. Crie {GOLDEN_FILE} — lista de {{q, relevant}}."}

    results = {provider: _evaluate_embedder(provider, golden, k) for provider in providers}
    return {
        "status": "ok",
        "k": k,
        "embedders": results,
        "recommendation": _recommend_default(results),
    }


def _cli_k(args: list[str]) -> int:
    for arg in args:
        if arg.isdigit():
            return int(arg)
    return 5


if __name__ == "__main__":
    import sys
    cli_args = sys.argv[1:]
    kk = _cli_k(cli_args)
    if "--embedders" in cli_args:
        print(json.dumps(evaluate_embedders(k=kk), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(evaluate(k=kk), ensure_ascii=False, indent=2))
