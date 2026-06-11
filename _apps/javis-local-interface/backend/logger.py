"""Logger — grava eventos JSONL com rotação diária em logs/actions-YYYY-MM-DD.jsonl."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


def log(
    source: str,
    user_text: str,
    route: dict,
    action_result: dict,
    approved: bool | None = None,
    duration_ms: int = 0,
    extra: dict | None = None,
) -> None:
    """Grava um evento no JSONL com rotação diária. source: 'cli', 'frontend' ou 'voice'."""
    LOGS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"actions-{date_str}.jsonl"

    _extra = extra or {}
    record = {
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "source":           source,
        "user_text":        user_text,
        "normalized_text":  _extra.get("clean_transcript"),
        "intent":           route.get("intent"),
        "confidence":       route.get("confidence"),
        "risk_level":       route.get("risk_level"),
        "requires_approval": route.get("requires_approval"),
        "approved":         approved,
        "dry_run":          _extra.get("dry_run"),
        "would_execute":    _extra.get("would_execute"),
        "note":             _extra.get("note"),
        "action_result":    action_result.get("status"),
        "message":          action_result.get("message"),
        "error":            action_result.get("error"),
        "latency_ms":       duration_ms,
    }

    # Adiciona campos extras não mapeados explicitamente acima
    for k, v in _extra.items():
        if k not in record:
            record[k] = v

    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
