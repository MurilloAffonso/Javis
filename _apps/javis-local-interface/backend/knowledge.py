"""Knowledge — RAG sobre os arquivos do senhor (Obsidian + projeto).

Indexa os .md/.txt do vault com embeddings (OpenAI text-embedding-3-small),
e busca por similaridade semântica. Tudo local — nada sai do PC além do
texto enviado para gerar embeddings.
"""
from __future__ import annotations
import json
import math
import os
import threading
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
INDEX_FILE = JAVIS_ROOT / "_memoria" / "knowledge_index.json"

# SÓ as pastas de conhecimento do senhor entram no índice (notas, ideias, projetos…)
# _referencias/ fica de fora de propósito: é majoritariamente doc de libs de
# terceiros (ECC, silero-vad) que poluiria a busca semântica.
_KNOWLEDGE_DIRS = [
    "_memoria", "_ideias", "_projetos", "_logs", "_estado",
    "_prompts", "_skills", "_inbox", "_outbox", "_ferramentas",
    "_treinamento", "_docs", "_sessoes",
]
# subpastas a pular mesmo dentro das de conhecimento (caches, libs, lixo)
_SKIP_DIRS = {
    ".git", ".obsidian", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".idea", ".vscode", "open-webui-data", "cache", ".cache",
    "models", "snapshots", "blobs", "site-packages", "leanctx", "headroom",
}
_EXTS = {".md", ".txt"}
_CHUNK = 800        # tamanho alvo do trecho (chars)
_MODEL = "text-embedding-3-small"
_MAX_FILES = 800    # trava de segurança contra indexar demais

_lock = threading.Lock()
_building = False
_last_auto_check = 0.0
_AUTO_CHECK_COOLDOWN = 60   # segundos — não verifica mudanças mais de 1x/min


def _has_external_changes(since_mtime: float) -> bool:
    """True se algum arquivo dos vaults externos foi alterado depois de since_mtime."""
    for vault in _external_vaults():
        for f in vault.glob("*.md"):
            try:
                if f.stat().st_mtime > since_mtime:
                    return True
            except OSError:
                continue
        for top in ("docs", "skills", "_conhecimento"):
            base = vault / top
            if not base.is_dir():
                continue
            for root, _dirs, files in os.walk(base):
                for fn in files:
                    if Path(fn).suffix.lower() in _EXTS:
                        try:
                            if (Path(root) / fn).stat().st_mtime > since_mtime:
                                return True
                        except OSError:
                            continue
    return False


def maybe_auto_sync() -> bool:
    """Chamado a cada busca: se o índice está velho E há mudanças nos vaults externos,
    dispara rebuild incremental em background. Cooldown evita varrer o disco toda hora."""
    global _last_auto_check
    import time as _t
    now = _t.time()
    if now - _last_auto_check < _AUTO_CHECK_COOLDOWN:
        return False
    _last_auto_check = now
    try:
        idx_mtime = INDEX_FILE.stat().st_mtime if INDEX_FILE.exists() else 0
    except OSError:
        idx_mtime = 0
    if _has_external_changes(idx_mtime):
        start_background_index()
        return True
    return False


def _external_vaults() -> list[Path]:
    """Vaults de projetos externos plugados (read-only). Hoje: Cérebro Jampa.
    Lê do project_registry; ignora silenciosamente se algo falhar."""
    out = []
    try:
        import project_registry as pr
        for slug, cfg in getattr(pr, "REGISTRY", {}).items():
            p = cfg.get("path") if isinstance(cfg, dict) else None
            if p and Path(p).is_dir():
                out.append(Path(p))
    except Exception:
        pass
    return out


def _iter_files():
    count = 0
    # 1) arquivos .md soltos na raiz (CLAUDE.md, AGENTS.md, README.md…)
    for f in JAVIS_ROOT.glob("*.md"):
        yield f
        count += 1
    # 2) só as pastas de conhecimento DO Javis
    for top in _KNOWLEDGE_DIRS:
        base = JAVIS_ROOT / top
        if not base.is_dir():
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".")]
            for fn in files:
                if Path(fn).suffix.lower() in _EXTS:
                    if count >= _MAX_FILES:
                        return
                    yield Path(root) / fn
                    count += 1
    # 3) VAULTS EXTERNOS plugados (Cérebro Jampa etc.) — read-only.
    # Pega a raiz do vault (FONTE-DA-VERDADE.md, AGENTS.md, CLAUDE.md…) e as
    # pastas de conhecimento que existirem nele (docs/, skills/, _conhecimento/…).
    _EXT_DIRS = {"docs", "skills", "_conhecimento", "_memoria", "_aprendizados",
                 "planejamento", "templates", "google-business-profile"}
    for vault in _external_vaults():
        for f in vault.glob("*.md"):
            if count >= _MAX_FILES:
                return
            yield f
            count += 1
        for top in _EXT_DIRS:
            base = vault / top
            if not base.is_dir():
                continue
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".")]
                for fn in files:
                    if Path(fn).suffix.lower() in _EXTS:
                        if count >= _MAX_FILES:
                            return
                        yield Path(root) / fn
                        count += 1


def _chunks(text: str) -> list[str]:
    out, buf = [], ""
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if len(buf) + len(para) + 2 <= _CHUNK:
            buf = f"{buf}\n\n{para}" if buf else para
        else:
            if buf:
                out.append(buf)
            buf = para if len(para) <= _CHUNK else para[:_CHUNK]
    if buf:
        out.append(buf)
    return out


def _embed_batch(texts: list[str]) -> list[list[float]]:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    vecs: list[list[float]] = []
    for i in range(0, len(texts), 96):
        batch = texts[i:i + 96]
        resp = client.embeddings.create(model=_MODEL, input=batch)
        vecs.extend(d.embedding for d in resp.data)
    return vecs


def _load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        return []
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_index(items: list[dict]) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def build_index(force: bool = False) -> dict:
    """Indexa (incremental) os arquivos do vault. Só re-embeda o que mudou."""
    global _building
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return {"status": "error", "message": "Sem OPENAI_API_KEY para gerar embeddings."}
    with _lock:
        if _building:
            return {"status": "busy"}
        _building = True
    try:
        index = [] if force else _load_index()
        by_path: dict[str, list[dict]] = {}
        for it in index:
            by_path.setdefault(it["path"], []).append(it)

        new_index: list[dict] = []
        pending_texts: list[str] = []
        pending_meta: list[dict] = []
        files_done = 0

        ext_roots = _external_vaults()
        for f in _iter_files():
            try:
                # caminho relativo ao Javis OU a um vault externo plugado
                try:
                    rel = str(f.relative_to(JAVIS_ROOT))
                except ValueError:
                    rel = None
                    for root in ext_roots:
                        try:
                            rel = f"[{root.name}] " + str(f.relative_to(root))
                            break
                        except ValueError:
                            continue
                    if rel is None:
                        rel = str(f)
                mtime = f.stat().st_mtime
            except OSError:
                continue   # arquivo quebrado / symlink inacessível → ignora
            cached = by_path.get(rel)
            if cached and all(abs(c.get("mtime", 0) - mtime) < 1 for c in cached):
                new_index.extend(cached)            # inalterado → reaproveita
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for ch in _chunks(text):
                pending_meta.append({"path": rel, "mtime": mtime, "chunk": ch})
                pending_texts.append(ch)
            files_done += 1

        if pending_texts:
            vecs = _embed_batch(pending_texts)
            for meta, vec in zip(pending_meta, vecs):
                meta["vec"] = vec
                new_index.append(meta)

        _save_index(new_index)
        return {"status": "ok", "chunks": len(new_index), "arquivos_reindexados": files_done}
    finally:
        _building = False


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def search(query: str, k: int = 5) -> list[dict]:
    """Busca semântica. Retorna [{path, chunk, score}] mais relevantes."""
    query = (query or "").strip()
    if not query:
        return []
    # Auto-sync lazy: se mudou algo nos vaults externos, dispara rebuild em
    # background (não bloqueia a busca atual, próximas já pegam o índice novo).
    try:
        maybe_auto_sync()
    except Exception:
        pass
    index = _load_index()
    if not index:
        build_index()
        index = _load_index()
    if not index:
        return []
    try:
        qvec = _embed_batch([query])[0]
    except Exception:
        return []
    scored = [{"path": it["path"], "chunk": it["chunk"], "score": _cosine(qvec, it["vec"])}
              for it in index if it.get("vec")]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def answer_context(query: str, k: int = 5) -> str:
    """Monta um bloco de contexto com os trechos relevantes (para o agente responder)."""
    hits = search(query, k)
    if not hits:
        return ""
    blocos = []
    for h in hits:
        if h["score"] < 0.25:
            continue
        blocos.append(f"[{h['path']}]\n{h['chunk']}")
    return "\n\n---\n\n".join(blocos)


def start_background_index() -> None:
    """Constrói o índice (incremental) em segundo plano no startup."""
    threading.Thread(target=lambda: build_index(force=False), daemon=True).start()
