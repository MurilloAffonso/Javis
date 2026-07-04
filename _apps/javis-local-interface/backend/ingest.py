"""ingest.py — ingestão em LOTE de material bruto → DNA → grafo.

Despeje arquivos de texto (.txt/.md) numa pasta (default `_inbox/ingestao/`) —
WhatsApp exports, transcrições, resumos de mentores, notas — e rode a ingestão:
cada arquivo passa pelo `dna_extractor` (detectando o tipo), o RAG é reindexado
uma vez no fim, e o grafo de conhecimento é reconstruído. Roda em thread; a UI
acompanha o progresso via `status()`.

É o "despejar material e ver o grafo crescer" — o salto de inteligência vem do
VOLUME de dossiês, não de mais código.
"""
from __future__ import annotations
import re
import threading
from datetime import datetime
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
INBOX_DIR = JAVIS_ROOT / "_inbox" / "ingestao"
_EXTS = (".txt", ".md")

_state = {
    "running": False, "total": 0, "processed": 0, "ok": 0, "erros": 0,
    "current": "", "done_ts": "", "graph": {}, "pasta": str(INBOX_DIR),
}
_lock = threading.Lock()


def _detect_tipo(text: str, name: str) -> str:
    """Heurística leve: WhatsApp (linhas com data + hora), transcrição, ou genérico."""
    low = name.lower()
    if "whats" in low or re.search(r"\d{1,2}/\d{1,2}/\d{2,4}[^\n]{0,8}\d{1,2}:\d{2}", text[:800]):
        return "whatsapp"
    if "transcri" in low or "transcript" in low:
        return "transcricao"
    return ""


_SKIP = {"leia-me", "leiame", "readme", "_leia-me"}


def _files(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.glob("*")
        if p.suffix.lower() in _EXTS and p.stem.lower() not in _SKIP
    )


def _run(folder: Path) -> None:
    import dna_extractor
    files = _files(folder)
    with _lock:
        _state.update({"running": True, "total": len(files), "processed": 0,
                       "ok": 0, "erros": 0, "current": "", "done_ts": "",
                       "pasta": str(folder)})
    for p in files:
        with _lock:
            _state["current"] = p.name
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            tipo = _detect_tipo(text, p.name)
            # reindex=False no loop; reindexamos uma vez no fim (mais rápido).
            r = dna_extractor.extract_and_index(text, fonte=p.name, tema=p.stem,
                                                fonte_tipo=tipo, reindex=False)
            with _lock:
                _state["ok" if r.get("status") == "ok" else "erros"] += 1
        except Exception:
            with _lock:
                _state["erros"] += 1
        with _lock:
            _state["processed"] += 1

    # Reindexa o RAG uma vez e reconstrói o grafo com todos os dossiês.
    try:
        import knowledge
        knowledge.build_index(force=False)
    except Exception:
        pass
    graph = {}
    try:
        import knowledge_graph
        graph = knowledge_graph.build_from_dna()
    except Exception:
        pass
    with _lock:
        _state.update({"running": False, "current": "", "graph": graph,
                       "done_ts": datetime.now().isoformat(timespec="seconds")})


def start(folder: str = "") -> dict:
    """Dispara a ingestão em lote (assíncrona). Retorna já com o total encontrado."""
    with _lock:
        if _state["running"]:
            return {"status": "ja_rodando", **_state}
    fdir = Path(folder) if folder else INBOX_DIR
    fdir.mkdir(parents=True, exist_ok=True)
    files = _files(fdir)
    if not files:
        return {"status": "vazio", "pasta": str(fdir),
                "dica": "Coloque arquivos .txt ou .md nessa pasta e rode de novo."}
    threading.Thread(target=_run, args=(fdir,), daemon=True).start()
    return {"status": "iniciado", "total": len(files), "pasta": str(fdir)}


def status() -> dict:
    with _lock:
        return dict(_state)
