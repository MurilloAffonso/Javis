"""Knowledge — RAG sobre os arquivos do senhor (Obsidian + projeto).

Indexa os .md/.txt do vault com embeddings e busca por similaridade semântica.
O provedor de embeddings é selecionado por `JAVIS_RAG_EMBEDDER`:

- `openai` — caminho atual, preservado por padrão.
- `local` — embedder puro-Python, offline e determinístico.
- `ollama` — embedder local real via Ollama, opt-in e atrás de external_adapters.
"""
from __future__ import annotations
import json
import math
import os
import hashlib
import re
import threading
import urllib.error
import urllib.request
from pathlib import Path

import gate

JAVIS_ROOT = Path(__file__).resolve().parents[3]
INDEX_FILE = JAVIS_ROOT / "_memoria" / "knowledge_index.json"

# SÓ as pastas de conhecimento do senhor entram no índice (notas, ideias, projetos…)
# _referencias/ fica de fora de propósito: é majoritariamente doc de libs de
# terceiros (ECC, silero-vad) que poluiria a busca semântica.
_KNOWLEDGE_DIRS = [
    "_memoria", "_ideias", "_projetos", "_logs", "_estado",
    "_prompts", "_skills", "_inbox", "_outbox", "_ferramentas",
    "_treinamento", "_docs", "docs", "_sessoes",
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
_LOCAL_EMBED_DIM = 256
_OLLAMA_DEFAULT_BASE_URL = "http://127.0.0.1:11434"
_OLLAMA_DEFAULT_MODEL = "nomic-embed-text"
_OLLAMA_EMBED_BATCH = 32
_OLLAMA_WARMUP_TIMEOUT = 90.0   # cold start medido ~28s; margem na 1a carga
_MAX_FILES = 800    # trava de segurança contra indexar demais

_lock = threading.Lock()
_building = False
_last_auto_check = 0.0
_AUTO_CHECK_COOLDOWN = 60   # segundos — não verifica mudanças mais de 1x/min


def _hybrid():
    """Módulo de RAG híbrido (SQLite: semântico + BM25 + RRF), se habilitado e já
    populado. Controlado por JAVIS_RAG (padrão 'hybrid'; qualquer outro valor usa
    só o índice JSON legado). Retorna None → segue no caminho legado."""
    if gate.require_external_adapters("knowledge.hybrid"):
        return None
    if os.environ.get("JAVIS_RAG", "hybrid").strip().lower() != "hybrid":
        return None
    try:
        import knowledge_hybrid as kh
        return kh if kh.available() else None
    except Exception:
        return None


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
    if gate.require_external_adapters("knowledge.auto_sync"):
        return False
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
    # R1: o RAG global do Javis core nao carrega projetos externos implicitamente.
    # Project-scoped RAG com project_id explicito fica para R2.
    return []


def scope_for_project(project_id: str | None) -> str | list[str]:
    """Mapeia project_id para o escopo de RAG permitido."""
    pid = (project_id or "").strip()
    if pid == gate.CEREBRO_JAMPA_SCOPE:
        return "vp"
    if pid == gate.CORE_SCOPE or not pid:
        return ["pessoal", "projeto"]
    return ["projeto"]


def _normalize_project_id(project_id: str | None) -> str:
    return (project_id or "").strip() or gate.CORE_SCOPE


def _scope_set(scope: str | list[str]) -> set[str]:
    return {scope} if isinstance(scope, str) else set(scope)


def _embedder_name() -> str:
    # Default = ollama (local, offline, custo zero). Bench 09/07: nomic-embed-text
    # recall@5 0.73 vs local 0.35 vs openai (não medido). JAVIS_RAG_EMBEDDER
    # sobrescreve para 'openai' ou 'local'.
    return (os.environ.get("JAVIS_RAG_EMBEDDER") or "ollama").strip().lower() or "ollama"


class _BaseEmbedder:
    name = "base"

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class _OllamaHTTPError(RuntimeError):
    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status


class _OpenAIEmbedder(_BaseEmbedder):
    name = "openai"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return _embed_batch(texts)


class _LocalEmbedder(_BaseEmbedder):
    name = "local"

    @staticmethod
    def _vector(text: str) -> list[float]:
        tokens = re.findall(r"[0-9A-Za-zÀ-ÿ]+", (text or "").lower())
        vec = [0.0] * _LOCAL_EMBED_DIM
        if not tokens:
            return vec

        def add(feature: str, weight: float) -> None:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(digest, "big") % _LOCAL_EMBED_DIM
            vec[idx] += weight

        for token in tokens:
            add(f"w:{token}", 1.0)

        normalized = " ".join(tokens)
        padded = f" {normalized} "
        if len(padded) >= 3:
            for i in range(len(padded) - 2):
                add(f"c3:{padded[i:i + 3]}", 0.45)

        norm = math.sqrt(sum(v * v for v in vec))
        if not norm:
            return vec
        return [v / norm for v in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]


class _OllamaEmbedder(_BaseEmbedder):
    name = "ollama"
    _warmed = False

    def _warm(self) -> None:
        # Cold start do modelo mede ~28s (1a carga na RAM); quente fica ~0.15s.
        # A 1a chamada do processo usa timeout longo, UMA vez. Se falhar aqui,
        # a exceção sobe e o _FallbackEmbedder cai para o local (offline).
        if type(self)._warmed:
            return
        prev = self.timeout
        self.timeout = max(self.timeout, _OLLAMA_WARMUP_TIMEOUT)
        try:
            self._embed_batch_api(["warmup"])
            type(self)._warmed = True
        finally:
            self.timeout = prev

    def __init__(self):
        self.model = (os.environ.get("JAVIS_OLLAMA_EMBED_MODEL") or _OLLAMA_DEFAULT_MODEL).strip()
        self.base_url = (
            os.environ.get("JAVIS_OLLAMA_BASE_URL") or _OLLAMA_DEFAULT_BASE_URL
        ).strip().rstrip("/")
        raw_timeout = (os.environ.get("JAVIS_OLLAMA_TIMEOUT") or "20").strip()
        try:
            self.timeout = max(float(raw_timeout), 1.0)
        except ValueError:
            self.timeout = 20.0

    def _require_enabled(self) -> None:
        blocked = gate.require_external_adapters("knowledge.ollama_embed")
        if blocked:
            flag = blocked.get("flag", "JAVIS_ENABLE_EXTERNAL_ADAPTERS")
            raise RuntimeError(
                f"Ollama embedder desabilitado: habilite {flag} para usar processo externo local."
            )

    def _post_json(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            message = f"Ollama embeddings falhou ({exc.code}) em {url}: {detail}"
            raise _OllamaHTTPError(message, exc.code) from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise RuntimeError(
                f"Ollama embeddings indisponivel em {self.base_url}: {reason}"
            ) from exc
        except TimeoutError as exc:
            raise RuntimeError(
                f"Ollama embeddings excedeu timeout de {self.timeout:.1f}s em {self.base_url}"
            ) from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Ollama embeddings retornou JSON invalido em {url}") from exc

    @staticmethod
    def _coerce_embeddings(value, expected: int) -> list[list[float]]:
        if not isinstance(value, list) or len(value) != expected:
            raise RuntimeError(
                f"Ollama embeddings retornou {len(value) if isinstance(value, list) else 0} vetores; esperado {expected}."
            )
        try:
            return [[float(x) for x in vec] for vec in value]
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Ollama embeddings retornou vetor invalido.") from exc

    def _embed_batch_api(self, texts: list[str]) -> list[list[float]]:
        data = self._post_json("/api/embed", {"model": self.model, "input": texts})
        return self._coerce_embeddings(data.get("embeddings"), len(texts))

    def _embed_legacy_api(self, text: str) -> list[float]:
        data = self._post_json("/api/embeddings", {"model": self.model, "prompt": text})
        vectors = self._coerce_embeddings([data.get("embedding")], 1)
        return vectors[0]

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._require_enabled()
        if not texts:
            return []
        self._warm()
        out: list[list[float]] = []
        for i in range(0, len(texts), _OLLAMA_EMBED_BATCH):
            batch = texts[i:i + _OLLAMA_EMBED_BATCH]
            try:
                out.extend(self._embed_batch_api(batch))
            except _OllamaHTTPError as exc:
                if exc.status != 404:
                    raise
                out.extend(self._embed_legacy_api(text) for text in batch)
        return out


class _FallbackEmbedder(_BaseEmbedder):
    """Tenta o provider primário; se falhar, cai para o fallback offline.
    NUNCA cai silenciosamente para OpenAI — o fallback é sempre o local."""

    def __init__(self, primary: _BaseEmbedder, fallback: _BaseEmbedder):
        self.primary = primary
        self.fallback = fallback
        self.name = primary.name

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            return self.primary.embed(texts)
        except Exception as exc:
            print(
                f"[knowledge] embedder '{self.primary.name}' indisponível ({exc}); "
                f"fallback -> '{self.fallback.name}' (offline)",
                flush=True,
            )
            return self.fallback.embed(texts)


def _selected_embedder() -> _BaseEmbedder:
    name = _embedder_name()
    if name == "local":
        return _LocalEmbedder()
    if name == "ollama":
        # default: ollama com rede de segurança offline (local), nunca openai.
        return _FallbackEmbedder(_OllamaEmbedder(), _LocalEmbedder())
    return _OpenAIEmbedder()


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


def _iso_from_mtime(mtime: float | int | None) -> str:
    if not mtime:
        return ""
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(float(mtime), tz=timezone.utc).isoformat(timespec="seconds")
    except Exception:
        return ""


def _metadata_for(rel: str, mtime: float | int | None) -> dict:
    import categoria as _cat
    return {
        "project_id": gate.CORE_SCOPE,
        "categoria": _cat.de_path(rel),
        "modified_at": _iso_from_mtime(mtime),
    }


def _query_terms(query: str) -> set[str]:
    stop = {
        "qual", "quais", "como", "esta", "está", "sao", "são", "de", "do",
        "da", "dos", "das", "e", "o", "a", "os", "as", "um", "uma", "me",
        "diga", "javes", "javis", "sistema", "projeto",
    }
    return {
        t for t in re.findall(r"[0-9A-Za-zÀ-ÿ_.-]+", (query or "").lower())
        if len(t) > 1 and t not in stop
    }


def _ranking_bonus(item: dict, query: str, max_mtime: float) -> float:
    path = (item.get("path") or "").replace("\\", "/")
    text = f"{path}\n{item.get('chunk') or ''}".lower()
    exact = sum(1 for term in _query_terms(query) if term in text)
    try:
        mtime = float(item.get("mtime") or 0)
        recency = (mtime / max_mtime) if max_mtime and mtime else 0.0
    except (TypeError, ValueError):
        recency = 0.0
    priority = 0.0
    low_path = path.lower()
    if low_path.startswith("docs/"):
        priority += 0.08
    if any(name in low_path for name in (
        "safe_startup", "audit_r0", "audit_r1", "audit_r2", "audit_r3",
        "audit_r4", "audit_r5", "release",
    )):
        priority += 0.12
    return min(exact * 0.05, 0.25) + min(recency * 0.12, 0.12) + priority


def build_index(force: bool = False) -> dict:
    """Indexa (incremental) os arquivos do vault. Só re-embeda o que mudou."""
    global _building
    blocked = gate.require_external_adapters("knowledge.build_index")
    if blocked:
        return blocked
    embedder = _selected_embedder()
    if embedder.name == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
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
                meta = _metadata_for(rel, mtime)
                for c in cached:
                    c.setdefault("mtime", mtime)
                    for key, value in meta.items():
                        c.setdefault(key, value)
                new_index.extend(cached)            # inalterado → reaproveita
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for ch in _chunks(text):
                pending_meta.append({
                    "path": rel,
                    "mtime": mtime,
                    "chunk": ch,
                    **_metadata_for(rel, mtime),
                })
                pending_texts.append(ch)
            files_done += 1

        if pending_texts:
            try:
                vecs = embedder.embed(pending_texts)
            except Exception as exc:
                return {
                    "status": "error",
                    "message": f"Falha no embedder {embedder.name}: {exc}",
                    "embedder": embedder.name,
                }
            for meta, vec in zip(pending_meta, vecs):
                meta["vec"] = vec
                new_index.append(meta)

        _save_index(new_index)
        # Alimenta também o índice híbrido (SQLite). Reaproveita os vetores
        # recém-gravados no JSON → não gera embedding novo na migração.
        try:
            if os.environ.get("JAVIS_RAG", "hybrid").strip().lower() == "hybrid":
                import knowledge_hybrid as kh
                kh.build_index(force=force)
        except Exception:
            pass
        return {"status": "ok", "chunks": len(new_index), "arquivos_reindexados": files_done}
    finally:
        _building = False


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def search(query: str, k: int = 5, project_id: str | None = None) -> list[dict]:
    """Busca semântica. Retorna [{path, chunk, score}] mais relevantes."""
    if gate.require_external_adapters("knowledge.search"):
        return []
    query = (query or "").strip()
    if not query:
        return []
    kh = _hybrid()
    if kh is not None:
        try:
            return kh.search(query, k, escopo=scope_for_project(_normalize_project_id(project_id)))
        except Exception:
            pass   # qualquer falha no híbrido → cai no índice JSON legado
    # Auto-sync lazy: se mudou algo nos vaults externos, dispara rebuild em
    # background (não bloqueia a busca atual, próximas já pegam o índice novo).
    try:
        maybe_auto_sync()
    except Exception:
        pass
    embedder = _selected_embedder()
    index = _load_index()
    if not index:
        build_index()
        index = _load_index()
    if not index:
        return []
    try:
        qvec = embedder.embed([query])[0]
    except Exception as exc:
        if embedder.name == "ollama":
            raise RuntimeError(f"Falha no embedder ollama: {exc}") from exc
        return []
    cats = _scope_set(scope_for_project(_normalize_project_id(project_id)))
    max_mtime = max((float(it.get("mtime") or 0) for it in index), default=0.0)
    scored = []
    for it in index:
        if not it.get("vec"):
            continue
        categoria = it.get("categoria")
        if not categoria:
            import categoria as _cat
            categoria = _cat.de_path(it.get("path", ""))
        if categoria not in cats:
            continue
        base_score = _cosine(qvec, it["vec"])
        scored.append({
            "path": it["path"],
            "chunk": it["chunk"],
            "score": base_score + _ranking_bonus(it, query, max_mtime),
            "base_score": base_score,
            "mtime": it.get("mtime", 0),
            "modified_at": it.get("modified_at", ""),
            "categoria": categoria,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def answer_context(query: str, k: int = 5, escopo=None) -> str:
    """Monta um bloco de contexto com os trechos relevantes (para o agente responder).
    `escopo` (str|list) restringe a categoria: 'pessoal' | 'projeto' | 'vp'."""
    kh = _hybrid()
    if kh is not None:
        try:
            return kh.answer_context(query, k, escopo=escopo)
        except Exception:
            pass   # falha no híbrido → contexto pelo caminho legado
    search_project_id = gate.CORE_SCOPE
    if escopo:
        cats_for_search = {escopo} if isinstance(escopo, str) else set(escopo)
        if "vp" in cats_for_search:
            search_project_id = gate.CEREBRO_JAMPA_SCOPE
    try:
        hits = search(query, k, project_id=search_project_id)
    except TypeError:
        hits = search(query, k)
    if not hits:
        return ""
    # Fallback legado (índice JSON, sem coluna de categoria): filtra por escopo
    # via path — best-effort, mas mantém a fronteira mesmo sem o híbrido.
    cats = None
    if escopo:
        cats = {escopo} if isinstance(escopo, str) else set(escopo)
    blocos = []
    for h in hits:
        if h["score"] < 0.25:
            continue
        if cats is not None:
            import categoria as _cat
            if _cat.de_path(h["path"]) not in cats:
                continue
        blocos.append(f"[{h['path']}]\n{h['chunk']}")
    return "\n\n---\n\n".join(blocos)


def start_background_index() -> bool:
    """Constrói o índice (incremental) em segundo plano no startup."""
    if gate.require_external_adapters("knowledge.start_background_index"):
        return False
    threading.Thread(target=lambda: build_index(force=False), daemon=True).start()
    return True
