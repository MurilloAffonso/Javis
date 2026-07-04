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

import db
import knowledge as _k   # reuso: _iter_files, _external_vaults, _embed_batch, _chunks, _load_index, JAVIS_ROOT

_RRF_K = 60                 # constante clássica do Reciprocal Rank Fusion
_SEM_MIN = 0.15            # similaridade mínima p/ um hit puramente semântico virar contexto

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


def build_index(force: bool = False) -> dict:
    """Indexa (incremental) os arquivos do vault no SQLite. Reaproveita vetores do
    JSON legado quando o chunk é idêntico; só embeda o que sobra."""
    global _building
    with _lock:
        if _building:
            return {"status": "busy"}
        _building = True
    try:
        db.init_db()
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
                for ci, ch in enumerate(chunks):
                    vec = json_cache.get((rel, ch))
                    staged.append([rel, mtime, ci, ch, vec])
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
                     len(r[4]) if r[4] is not None else None)
                    for r in staged]
            if rows:
                conn.executemany(
                    "INSERT INTO knowledge_chunks(path, mtime, chunk_index, content, vec, dim) "
                    "VALUES (?, ?, ?, ?, ?, ?)", rows)
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


def search(query: str, k: int = 5) -> list[dict]:
    """Busca híbrida. Retorna [{path, chunk, score, sem, kw}] mais relevantes."""
    query = (query or "").strip()
    if not query:
        return []
    try:
        qvec = _k._embed_batch([query])[0]
    except Exception:
        qvec = None

    pool = max(k * 4, 20)
    sem = _semantic(qvec, pool) if qvec is not None else []
    kw = _keyword(query, pool)
    if not sem and not kw:
        return []

    sem_by_id = {cid: s for cid, s in sem}
    kw_ids = {cid for cid, _ in kw}
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


def answer_context(query: str, k: int = 5) -> str:
    """Monta o bloco de contexto (para o agente responder)."""
    hits = search(query, k)
    if not hits:
        return ""
    blocos = []
    for h in hits:
        # mantém se tem semelhança semântica decente OU casou por palavra-chave (BM25)
        if h["sem"] < _SEM_MIN and not h["kw"]:
            continue
        blocos.append(f"[{h['path']}]\n{h['chunk']}")
    return "\n\n---\n\n".join(blocos)


def available() -> bool:
    """True se o índice híbrido já tem chunks (senão o legado assume)."""
    try:
        return db.count("knowledge_chunks") > 0
    except Exception:
        return False


def start_background_index() -> None:
    threading.Thread(target=lambda: build_index(force=False), daemon=True).start()
