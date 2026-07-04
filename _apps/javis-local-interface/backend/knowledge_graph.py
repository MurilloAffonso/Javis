"""knowledge_graph.py — grafo de conhecimento sobre os dossiês de DNA (item 4).

Liga os conceitos extraídos pelo dna_extractor: cada "ideia" de uma dimensão vira
um NÓ; conceitos que aparecem no MESMO dossiê ganham uma ARESTA de co-ocorrência.
Conceitos que reaparecem em vários dossiês acumulam `mentions` e peso de aresta —
é assim que os temas centrais do Murillo emergem do grafo.

Determinístico e sem custo de LLM (opera sobre o JSON já estruturado dos dossiês).
SQLite-nativo (javis.db), aditivo. Reconstrução idempotente (limpa só as tabelas
kg_*). Reusa dna_extractor.DNA_DIR / DIMENSOES / _slug.
"""
from __future__ import annotations

import json
from pathlib import Path

import db
import dna_extractor


# ---------------------------------------------------------------------------
# Leitura dos dossiês → itens (key, label, type)
# ---------------------------------------------------------------------------
def _label_of(it) -> str:
    if isinstance(it, dict):
        for f in ("ideia", "nome", "objecao", "termo"):
            if it.get(f):
                return str(it[f])
        # primeiro valor string não vazio
        for v in it.values():
            if isinstance(v, str) and v.strip():
                return v
        return ""
    return str(it).strip()


def _items_of(data: dict) -> list[tuple[str, str, str]]:
    """[(key, label, type)] únicos de um dossiê DNA."""
    dna = (data or {}).get("dna") or {}
    seen: dict[str, tuple[str, str, str]] = {}
    for dim in dna_extractor.DIMENSOES:
        for it in dna.get(dim) or []:
            label = _label_of(it).strip()
            if not label:
                continue
            key = dna_extractor._slug(label)
            if key and key not in seen:
                seen[key] = (key, label, dim)
    return list(seen.values())


# ---------------------------------------------------------------------------
# Build (reconstrução completa)
# ---------------------------------------------------------------------------
def _upsert_node(conn, cache: dict, key: str, label: str, typ: str, path: str) -> int:
    if key in cache:
        nid = cache[key]
        row = conn.execute("SELECT sources FROM kg_nodes WHERE id=?", (nid,)).fetchone()
        srcs = json.loads(row[0]) if row and row[0] else []
        if path not in srcs and len(srcs) < 20:
            srcs.append(path)
        conn.execute("UPDATE kg_nodes SET mentions = mentions + 1, sources = ? WHERE id = ?",
                     (json.dumps(srcs, ensure_ascii=False), nid))
        return nid
    cur = conn.execute(
        "INSERT INTO kg_nodes(key, label, type, mentions, sources) VALUES (?, ?, ?, 1, ?)",
        (key, label, typ, json.dumps([path], ensure_ascii=False)))
    cache[key] = cur.lastrowid
    return cur.lastrowid


def build_from_dna(dossier_dir=None, cap_itens: int = 60) -> dict:
    """(Re)constrói o grafo a partir de _memoria/dna/*.json. Idempotente."""
    d = Path(dossier_dir) if dossier_dir else dna_extractor.DNA_DIR
    db.init_db()
    files = sorted(d.glob("*.json")) if d.is_dir() else []

    conn = db.get_conn()
    try:
        conn.execute("DELETE FROM kg_edges")
        conn.execute("DELETE FROM kg_nodes")
        cache: dict[str, int] = {}
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            items = _items_of(data)[:cap_itens]
            ids = sorted({_upsert_node(conn, cache, k, lb, tp, f.name) for k, lb, tp in items})
            # arestas de co-ocorrência (não-direcionadas: src<dst)
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    conn.execute(
                        "INSERT INTO kg_edges(src, dst, rel, weight) VALUES (?, ?, 'co_ocorre', 1) "
                        "ON CONFLICT(src, dst, rel) DO UPDATE SET weight = weight + 1",
                        (ids[i], ids[j]))
        conn.commit()
        n_nodes = conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        n_edges = conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
    finally:
        conn.close()
    return {"status": "ok", "nodes": int(n_nodes), "edges": int(n_edges), "dossies": len(files)}


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------
def _find_nodes(term: str, limit: int = 10) -> list[dict]:
    term = (term or "").strip()
    if not term:
        return []
    like = f"%{term.lower()}%"
    keyl = f"%{dna_extractor._slug(term)}%"
    return db.query(
        "SELECT id, key, label, type, mentions FROM kg_nodes "
        "WHERE lower(label) LIKE ? OR key LIKE ? ORDER BY mentions DESC, id LIMIT ?",
        (like, keyl, limit))


def neighbors(term: str, depth: int = 1, limit: int = 60) -> dict:
    """Vizinhança de um conceito: nós-semente + conceitos ligados (até `depth` saltos)."""
    db.init_db()
    seeds = _find_nodes(term)
    if not seeds:
        return {"status": "ok", "term": term, "seeds": [], "nodes": [], "edges": []}

    seen = {n["id"] for n in seeds}
    frontier = set(seen)
    edge_set: dict[tuple, dict] = {}
    for _ in range(max(1, depth)):
        if not frontier:
            break
        ph = ",".join("?" * len(frontier))
        rows = db.query(
            f"SELECT src, dst, rel, weight FROM kg_edges WHERE src IN ({ph}) OR dst IN ({ph})",
            tuple(frontier) * 2)
        new_frontier = set()
        for r in rows:
            edge_set[(r["src"], r["dst"], r["rel"])] = r
            for x in (r["src"], r["dst"]):
                if x not in seen:
                    seen.add(x)
                    new_frontier.add(x)
        frontier = new_frontier
        if len(seen) >= limit:
            break

    ids = list(seen)[:limit]
    ph = ",".join("?" * len(ids))
    nodes = db.query(
        f"SELECT id, key, label, type, mentions FROM kg_nodes WHERE id IN ({ph}) "
        "ORDER BY mentions DESC", tuple(ids))
    id_ok = {n["id"] for n in nodes}
    edges = [e for e in edge_set.values() if e["src"] in id_ok and e["dst"] in id_ok]
    edges.sort(key=lambda e: e["weight"], reverse=True)
    return {"status": "ok", "term": term,
            "seeds": [s["label"] for s in seeds], "nodes": nodes, "edges": edges}


def top_concepts(n: int = 15) -> list[dict]:
    return db.query(
        "SELECT n.id, n.key, n.label, n.type, n.mentions, "
        "  (SELECT COUNT(*) FROM kg_edges e WHERE e.src = n.id OR e.dst = n.id) AS grau "
        "FROM kg_nodes n ORDER BY grau DESC, n.mentions DESC LIMIT ?", (n,))


def stats() -> dict:
    try:
        return {"status": "ok", "nodes": db.count("kg_nodes"), "edges": db.count("kg_edges"),
                "top": top_concepts(10)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
