"""telemetry_adapter.py — telemetria READ-ONLY a partir do log de eventos.

Le os JSONL gravados por logger.py (logs/actions-YYYY-MM-DD.jsonl) e agrega:
status do sistema, metricas (contagem/tokens estimados/latencia) e eventos
recentes — para o Command Center. NUNCA escreve, NUNCA executa nada.

Tokens sao ESTIMADOS (~4 chars/token); nao sao cobranca real.
"""
from __future__ import annotations
import json
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


def _read_recent(limit: int = 500) -> list[dict]:
    """Registros mais recentes primeiro, varrendo os JSONL do mais novo p/ o mais antigo."""
    if not LOGS_DIR.exists():
        return []
    files = sorted(LOGS_DIR.glob("actions-*.jsonl"), reverse=True)
    out: list[dict] = []
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
            if len(out) >= limit:
                return out
    return out


def _est_tokens(text: str | None) -> int:
    return max(0, len(text or "") // 4)


def recent_events(limit: int = 12) -> list[dict]:
    out = []
    for r in _read_recent(limit):
        ts = r.get("timestamp", "") or ""
        out.append({
            "t": ts[11:16] if len(ts) >= 16 else "",
            "source": r.get("source"),
            "intent": r.get("intent"),
            "status": r.get("action_result"),
            "message": (r.get("message") or "")[:140],
        })
    return out


def _last_brain() -> str | None:
    """brain da última resposta do assistente (vem do SQLite messages, não do JSONL)."""
    try:
        import repositories as repo
        for m in repo.messages.recent(8):
            if m.get("role") == "assistant" and m.get("brain"):
                return m.get("brain")
    except Exception:
        pass
    return None


def last_execution() -> dict:
    recs = _read_recent(1)
    base = {} if not recs else {
        "intent": recs[0].get("intent"),
        "risk_level": recs[0].get("risk_level"),
        "requires_approval": recs[0].get("requires_approval"),
        "status": recs[0].get("action_result"),
        "source": recs[0].get("source"),
        "latency_ms": recs[0].get("latency_ms"),
    }
    base["brain"] = _last_brain()
    return base


def metrics() -> dict:
    recs = _read_recent(500)
    lat = [r.get("latency_ms") or 0 for r in recs if r.get("latency_ms")]
    tokens_in = sum(_est_tokens(r.get("user_text")) for r in recs)
    tokens_out = sum(_est_tokens(r.get("message")) for r in recs)
    return {
        "calls": len(recs),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_total": tokens_in + tokens_out,
        "avg_latency_ms": round(sum(lat) / len(lat)) if lat else 0,
        "last": last_execution(),
    }


def status() -> list[dict]:
    items = [{"label": "Backend (server.py)", "val": "online", "cls": "ok"}]
    try:
        import claude_exec
        ok = claude_exec.available()
        items.append({"label": "Claude Code (exec)", "val": "pronto" if ok else "indisponível",
                      "cls": "ok" if ok else "err"})
    except Exception:
        items.append({"label": "Claude Code (exec)", "val": "?", "cls": "wait"})
    try:
        import knowledge  # noqa: F401
        items.append({"label": "RAG (Obsidian)", "val": "ativo", "cls": "ok"})
    except Exception:
        items.append({"label": "RAG (Obsidian)", "val": "off", "cls": "wait"})
    return items


def full() -> dict:
    return {"status": status(), "metrics": metrics(), "events": recent_events()}
