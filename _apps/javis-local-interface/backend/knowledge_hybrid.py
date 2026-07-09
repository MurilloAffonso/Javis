"""knowledge_hybrid.py — RAG híbrido (SQLite-nativo): semântico + BM25 + RRF.

ADITIVO: não substitui `knowledge.py`. Reaproveita a varredura de arquivos, os
vaults externos e o embedding da OpenAI daquele módulo, mas guarda os chunks e
vetores no SQLite (`javis.db`) e cruza:

  • busca vetorial  — cosine com numpy sobre os vetores guardados em BLOB;
  • busca por termo  — FTS5/BM25 embutido no SQLite;

fundindo os dois rankings por Reciprocal Rank Fusion (RRF).

Economia: a migração inicial reaproveita os vetores já existentes em
`_memoria/knowledge_index.json` (casando por path + texto do chunk). Enquanto o
chunking for o mesmo do legado, o primeiro build custa ZERO embeddings novos.

API espelha `knowledge.py` (search/answer_context/build_index/...) para poder
ser plugado como substituto transparente, com fallback pro legado.
"""
from __future__ import annotations

import os
import re
import threading

import numpy as np

import categoria as _cat
import db
import gate
import knowledge as _k   # reuso: _iter_files, _external_vaults, _embed_batch, _chunks, _load_index, JAVIS_ROOT

_RRF_K = 60                 # constante clássica do Reciprocal Rank Fusion
_SEM_MIN = 0.15            # piso legado (usado no modo degradado, sem embeddings)
# Portão de relevância do answer_context (com embeddings vivos). Medido no golden
# 2026-07-05: chunks RELEVANTES têm sem>=0.47 (mediana 0.62); o casamento kw-only
# com sem~0 é ruído (5/5 não-relevantes). Estes cortes mantêm retenção 100% e
# eliminam o ruído "match fraco só por palavra".
_SEM_KEEP = 0.35           # piso p/ um chunk entrar no contexto por conta própria
_SEM_KW_FLOOR = 0.25       # piso menor p/ um casamento BM25 ainda contar (guarda exato-termo)

_lock = threading.Lock()
_building = False

# Cache em memória da matriz de vetores normalizados (evita reconstruir a cada busca).
_cache: dict = {"ids": None, "mat": None}


# ---------------------------------------------------------------------------
# Serialização de vetores
# ---------------------------------------------------------------------------
def _vec_to_blob(vec) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes()


def _invalidate() -> None:
    _cache["ids"] = None
    _cache["mat"] = None


# ---------------------------------------------------------------------------
# Chunking com overlap (usado só em rebuild force=True; o build incremental
# usa o chunking do legado para poder reaproveitar os vetores do JSON)
# ---------------------------------------------------------------------------
def _chunks_overlap(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    out: list[str] = []
    buf = ""
    for para in paras:
        if len(para) > size:                      # parágrafo gigante → fatia bruta
            if buf:
                out.append(buf)
                buf = ""
            for i in range(0, len(para), size - overlap):
                out.append(para[i:i + size])
            continue
        if len(buf) + len(para) + 2 <= size:
            buf = f"{buf}\n\n{para}" if buf else para
        else:
            if buf:
                out.append(buf)
            tail = buf[-overlap:] if buf else ""
            buf = f"{tail}\n\n{para}" if tail else para
    if buf:
        out.append(buf)
    return out


# ---------------------------------------------------------------------------
# Helpers de build
# ---------------------------------------------------------------------------
def _relpath(f, ext_roots) -> tuple[str | None, float]:
    """Mesma convenção de caminho do knowledge.py (rel ao Javis ou '[vault] rel')."""
    try:
        return str(f.relative_to(_k.JAVIS_ROOT)), f.stat().st_mtime
    except (ValueError, OSError):
        pass
    for root in ext_roots:
        try:
            return f"[{root.name}] " + str(f.relative_to(root)), f.stat().st_mtime
        except (ValueError, OSError):
            continue
    try:
        return str(f), f.stat().st_mtime
    except OSError:
        return None, 0.0


def _load_json_vec_cache() -> dict:
    """{(path, chunk_text): vec} a partir do índice JSON legado — p/ reaproveitar embeddings."""
    cache: dict = {}
    for it in _k._load_index():
        v = it.get("vec")
        if v:
            cache[(it.get("path"), it.get("chunk"))] = v
    return cache


def backfill_categoria() -> int:
    """Preenche `categoria` (determinística, por path) nos chunks que ainda estão
    NULL — DBs populados antes da coluna existir. Custo ZERO de embeddings: só um
    UPDATE por path. Idempotente. Retorna quantos paths foram rotulados."""
    rows = db.query("SELECT DISTINCT path FROM knowledge_chunks WHERE categoria IS NULL")
    if not rows:
        return 0
    conn = db.get_conn()
    try:
        for r in rows:
            conn.execute(
                "UPDATE knowledge_chunks SET categoria = ? WHERE path = ? AND categoria IS NULL",
                (_cat.de_path(r["path"]), r["path"]))
        conn.commit()
    finally:
        conn.close()
    return len(rows)


def build_index(force: bool = False) -> dict:
    """Indexa (incremental) os arquivos do vault no SQLite. Reaproveita vetores do
    JSON legado quando o chunk é idêntico; só embeda o que sobra."""
    global _building
    blocked = gate.require_external_adapters("knowledge_hybrid.build_index")
    if blocked:
        return blocked
    with _lock:
        if _building:
            return {"status": "busy"}
        _building = True
    try:
        db.init_db()
        backfill_categoria()
        json_cache = {} if force else _load_json_vec_cache()
        ext_roots = _k._external_vaults()

        conn = db.get_conn()
        try:
            stored = {r["path"]: r["m"] for r in
                      conn.execute("SELECT path, MAX(mtime) AS m FROM knowledge_chunks GROUP BY path")}
            seen: set[str] = set()
            changed_paths: set[str] = set()
            staged: list[list] = []      # [path, mtime, chunk_index, content, vec|None]
            pending_idx: list[int] = []  # posições em staged sem vetor (precisam embed)

            for f in _k._iter_files():
                rel, mtime = _relpath(f, ext_roots)
                if rel is None:
                    continue
                seen.add(rel)
                if not force and rel in stored and abs(stored[rel] - mtime) < 1:
                    continue                       # inalterado → mantém o que já está no banco
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                chunks = _chunks_overlap(text) if force else _k._chunks(text)
                changed_paths.add(rel)
                cat = _cat.de_path(rel)
                for ci, ch in enumerate(chunks):
                    vec = json_cache.get((rel, ch))
                    staged.append([rel, mtime, ci, ch, vec, cat])
                    if vec is None:
                        pending_idx.append(len(staged) - 1)

            # embeddings só do que faltou (sem key: fica NULL → indexado só no BM25)
            embedded = 0
            if pending_idx and os.environ.get("OPENAI_API_KEY", "").strip():
                texts = [staged[i][3] for i in pending_idx]
                vecs = _k._embed_batch(texts)
                for i, v in zip(pending_idx, vecs):
                    staged[i][4] = v
                    embedded += 1

            # remove do banco os paths alterados (reinseridos) e os sumidos do disco
            stale = set(stored) - seen
            for rel in (changed_paths | stale):
                conn.execute("DELETE FROM knowledge_chunks WHERE path = ?", (rel,))

            rows = [(r[0], r[1], r[2], r[3],
                     _vec_to_blob(r[4]) if r[4] is not None else None,
                     len(r[4]) if r[4] is not None else None,
                     r[5])
                    for r in staged]
            if rows:
                conn.executemany(
                    "INSERT INTO knowledge_chunks(path, mtime, chunk_index, content, vec, dim, categoria) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
            conn.commit()
            total = conn.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
        finally:
            conn.close()

        _invalidate()
        have_vec = sum(1 for r in staged if r[4] is not None)
        return {"status": "ok", "chunks": int(total), "arquivos": len(changed_paths),
                "reused_vecs": have_vec - embedded, "embedded": embedded,
                "removidos": len(set(stored) - seen)}
    finally:
        _building = False


# ---------------------------------------------------------------------------
# Busca
# ---------------------------------------------------------------------------
def _matrix() -> tuple[np.ndarray, np.ndarray]:
    """(ids, matriz normalizada linha-a-linha) de todos os chunks com vetor. Cacheado."""
    if _cache["ids"] is not None:
        return _cache["ids"], _cache["mat"]
    rows = db.query("SELECT id, vec FROM knowledge_chunks WHERE vec IS NOT NULL")
    if rows:
        ids = np.array([r["id"] for r in rows], dtype=np.int64)
        mat = np.vstack([np.frombuffer(r["vec"], dtype=np.float32) for r in rows])
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        mat = (mat / norms).astype(np.float32)
    else:
        ids = np.zeros((0,), dtype=np.int64)
        mat = np.zeros((0, 0), dtype=np.float32)
    _cache["ids"], _cache["mat"] = ids, mat
    return ids, mat


def _semantic(qvec, n: int) -> list[tuple[int, float]]:
    ids, mat = _matrix()
    if mat.shape[0] == 0:
        return []
    q = np.asarray(qvec, dtype=np.float32)
    nq = float(np.linalg.norm(q)) or 1.0
    sims = mat @ (q / nq)
    n = min(n, sims.shape[0])
    idx = np.argpartition(-sims, n - 1)[:n]
    idx = idx[np.argsort(-sims[idx])]
    return [(int(ids[i]), float(sims[i])) for i in idx]


def _fts_match(query: str) -> str | None:
    """Monta um MATCH FTS5 seguro: tokens alfanuméricos OR-eados e citados
    (evita erro de sintaxe com pontuação/operadores do usuário)."""
    toks = [t for t in re.findall(r"\w+", query.lower(), flags=re.UNICODE) if len(t) > 1]
    if not toks:
        return None
    return " OR ".join(f'"{t}"' for t in toks[:24])


def _keyword(query: str, n: int) -> list[tuple[int, int]]:
    m = _fts_match(query)
    if not m:
        return []
    try:
        rows = db.query(
            "SELECT rowid AS id FROM knowledge_fts WHERE knowledge_fts MATCH ? "
            "ORDER BY bm25(knowledge_fts) LIMIT ?", (m, n))
    except Exception:
        return []
    return [(int(r["id"]), rank) for rank, r in enumerate(rows)]


def _rrf(sem: list[tuple[int, float]], kw: list[tuple[int, int]], k: int):
    scores: dict[int, float] = {}
    for rank, (cid, _s) in enumerate(sem):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank)
    for rank, (cid, _r) in enumerate(kw):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank)
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return ordered


# Peso da MAGNITUDE semântica no rerank (vs. posição BM25). O RRF puro ordena só
# por rank e joga fora quão forte é o casamento semântico; o rerank recupera isso.
_RERANK_ALPHA = 0.7


def _rerank(cand_ids: list[int], sem_by_id: dict[int, float],
            kw_rank_by_id: dict[int, int], rrf_by_id: dict[int, float],
            alpha: float = _RERANK_ALPHA) -> list[tuple[int, float]]:
    """Reordena o pool de candidatos por FUSÃO DE SCORES normalizados: mistura a
    magnitude do cosseno (min-max no pool) com o sinal BM25 (1/(1+rank)). O RRF
    entra só como desempate. Sem modelo, sem latência. Retorna [(id, score)] desc."""
    sems = [max(sem_by_id.get(c, 0.0), 0.0) for c in cand_ids]
    smax = max(sems) if sems else 0.0
    smin = min(sems) if sems else 0.0
    span = smax - smin

    def sn(c: int) -> float:                      # semântico normalizado [0,1]
        v = max(sem_by_id.get(c, 0.0), 0.0)
        if span > 1e-9:
            return (v - smin) / span
        return 1.0 if v > 0 else 0.0

    def kn(c: int) -> float:                       # keyword: melhor rank BM25 → mais perto de 1
        r = kw_rank_by_id.get(c)
        return 1.0 / (1.0 + r) if r is not None else 0.0

    scored = [(c, alpha * sn(c) + (1.0 - alpha) * kn(c)) for c in cand_ids]
    scored.sort(key=lambda x: (x[1], rrf_by_id.get(x[0], 0.0)), reverse=True)
    return scored


def _ids_no_escopo(escopo) -> set[int] | None:
    """Conjunto de ids de chunk permitidos pelo escopo (categoria).
    Sem escopo explicito, exclui VP/Jampa do contexto global do Javis core.
    `escopo` pode ser uma str ('vp') ou lista (['projeto','pessoal'])."""
    if not escopo:
        try:
            rows = db.query(
                "SELECT id FROM knowledge_chunks WHERE COALESCE(categoria, '') <> ?",
                ("vp",),
            )
            return {int(r["id"]) for r in rows}
        except Exception:
            return set()
    cats = [escopo] if isinstance(escopo, str) else list(escopo)
    cats = [c for c in cats if c]
    if not cats:
        return None
    ph = ",".join("?" * len(cats))
    rows = db.query(
        f"SELECT id FROM knowledge_chunks WHERE categoria IN ({ph})", tuple(cats))
    return {int(r["id"]) for r in rows}


def search(query: str, k: int = 5, escopo=None, rerank: bool = False) -> list[dict]:
    """Busca híbrida. Retorna [{path, chunk, score, sem, kw}] mais relevantes.
    `escopo` (str|list) filtra por categoria: 'pessoal' | 'projeto' | 'vp'.
    `rerank`: reordena o pool fundido por magnitude de score. Default OFF —
    medido no golden set COM embeddings (2026-07-05): PIORA o RRF (mrr 0.958→0.83,
    −0.13), pois desarruma um ranking já quase perfeito. Mantido só como estágio
    togglável p/ medir rerankers futuros; ganho real exigiria cross-encoder."""
    query = (query or "").strip()
    if not query:
        return []
    if gate.require_external_adapters("knowledge_hybrid.search"):
        return []
    try:
        qvec = _k._embed_batch([query])[0]
    except Exception:
        qvec = None

    allowed = _ids_no_escopo(escopo)
    # Com escopo, puxa um pool maior porque o filtro pós-retrieval descarta chunks.
    pool = max(k * 8, 40) if allowed is not None else max(k * 4, 20)
    sem = _semantic(qvec, pool) if qvec is not None else []
    kw = _keyword(query, pool)
    if allowed is not None:
        sem = [(cid, s) for cid, s in sem if cid in allowed]
        kw = [(cid, r) for cid, r in kw if cid in allowed]
    if not sem and not kw:
        return []

    sem_by_id = {cid: s for cid, s in sem}
    kw_ids = {cid for cid, _ in kw}
    if rerank:
        kw_rank_by_id = {cid: r for cid, r in kw}
        cand = list(dict.fromkeys([c for c, _ in sem] + [c for c, _ in kw]))  # união, dedup ordem-preservada
        rrf_by_id = dict(_rrf(sem, kw, len(cand)))                            # desempate
        ordered = _rerank(cand, sem_by_id, kw_rank_by_id, rrf_by_id)[:k]
    else:
        ordered = _rrf(sem, kw, k)
    ids = [cid for cid, _ in ordered]
    if not ids:
        return []

    ph = ",".join("?" * len(ids))
    rows = db.query(f"SELECT id, path, content FROM knowledge_chunks WHERE id IN ({ph})", tuple(ids))
    by_id = {r["id"]: r for r in rows}

    out = []
    for cid, sc in ordered:
        r = by_id.get(cid)
        if not r:
            continue
        out.append({
            "path": r["path"], "chunk": r["content"],
            "score": round(float(sc), 6),
            "sem": round(float(sem_by_id.get(cid, 0.0)), 4),
            "kw": cid in kw_ids,
        })
    return out


def answer_context(query: str, k: int = 5, escopo=None, rerank: bool = False) -> str:
    """Monta o bloco de contexto (para o agente responder). `escopo` (str|list)
    restringe a categoria: 'pessoal' | 'projeto' | 'vp'. `rerank`: default OFF
    (sem ganho medido sobre o RRF; ver search())."""
    hits = search(query, k, escopo=escopo, rerank=rerank)
    if not hits:
        return ""
    # Guard: se o embedding estiver morto (sem OPENAI_API_KEY em runtime), TODO sem
    # vem 0 → cai no gate legado (kw OU sem>=_SEM_MIN) pra NÃO zerar o grounding.
    sem_vivo = any(h["sem"] > 0 for h in hits)
    blocos = []
    for h in hits:
        if sem_vivo:
            # embedding vivo: piso semântico firme; kw só conta se ainda houver
            # alguma afinidade semântica (mata "match fraco só por palavra").
            keep = h["sem"] >= _SEM_KEEP or (h["kw"] and h["sem"] >= _SEM_KW_FLOOR)
        else:
            keep = h["kw"] or h["sem"] >= _SEM_MIN     # modo degradado (legado)
        if not keep:
            continue
        blocos.append(f"[{h['path']}]\n{h['chunk']}")
    return "\n\n---\n\n".join(blocos)


def available() -> bool:
    """True se o índice híbrido já tem chunks (senão o legado assume)."""
    try:
        return db.count("knowledge_chunks") > 0
    except Exception:
        return False


def start_background_index() -> bool:
    if gate.require_external_adapters("knowledge_hybrid.start_background_index"):
        return False
    threading.Thread(target=lambda: build_index(force=False), daemon=True).start()
    return True
