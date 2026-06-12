"""Reminders — lembretes e timers do Jamba.

Guarda lembretes em JSON e roda um thread que verifica os vencidos.
Quando vence: coloca numa fila que a interface consome (fala por TTS) e,
se o Telegram estiver configurado, manda no celular também.
"""
from __future__ import annotations
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
FILE = JAVIS_ROOT / "_memoria" / "lembretes.json"

_lock = threading.Lock()
_due_queue: list[dict] = []   # vencidos aguardando a interface consumir
_started = False


def _load() -> list[dict]:
    if not FILE.exists():
        return []
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items: list[dict]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def add(text: str, minutos: float | None = None, iso: str | None = None) -> str:
    """Cria um lembrete. minutos = daqui a X min; iso = horário absoluto ISO."""
    text = (text or "").strip()
    if not text:
        return "Lembrete vazio, senhor."
    if minutos is not None:
        due = datetime.now() + timedelta(minutes=float(minutos))
    elif iso:
        try:
            due = datetime.fromisoformat(iso)
        except Exception:
            return "Não entendi o horário, senhor."
    else:
        return "Preciso saber quando, senhor (em quantos minutos ou que horas)."

    with _lock:
        items = _load()
        items.append({
            "id": int(time.time() * 1000),
            "text": text,
            "due": due.isoformat(timespec="seconds"),
            "done": False,
        })
        _save(items)

    quando = due.strftime("%H:%M")
    if minutos is not None:
        return f"Combinado, senhor. Te lembro às {quando} ({int(float(minutos))} min): {text}"
    return f"Combinado, senhor. Te lembro às {quando}: {text}"


def list_pending() -> list[dict]:
    now = datetime.now()
    out = []
    for it in _load():
        if it.get("done"):
            continue
        try:
            due = datetime.fromisoformat(it["due"])
        except Exception:
            continue
        out.append({"text": it["text"], "due": it["due"],
                    "falta_min": max(0, int((due - now).total_seconds() / 60))})
    return sorted(out, key=lambda x: x["due"])


def list_pending_text() -> str:
    p = list_pending()
    if not p:
        return "Nenhum lembrete pendente, senhor."
    linhas = [f"- {x['text']} (em {x['falta_min']} min)" for x in p]
    return "Seus lembretes, senhor:\n" + "\n".join(linhas)


def pop_due() -> list[dict]:
    """Retorna e limpa os lembretes que venceram (consumido pela interface)."""
    with _lock:
        due = list(_due_queue)
        _due_queue.clear()
    return due


def _check_loop() -> None:
    while True:
        try:
            now = datetime.now()
            with _lock:
                items = _load()
                changed = False
                for it in items:
                    if it.get("done"):
                        continue
                    try:
                        due = datetime.fromisoformat(it["due"])
                    except Exception:
                        continue
                    if due <= now:
                        it["done"] = True
                        changed = True
                        _due_queue.append({"text": it["text"]})
                        _notify_telegram(it["text"])
                if changed:
                    _save(items)
        except Exception:
            pass
        time.sleep(15)


def _notify_telegram(text: str) -> None:
    import os
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
    if not token or not chat:
        return
    try:
        import requests
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": f"⏰ Lembrete, senhor: {text}"}, timeout=10)
    except Exception:
        pass


def start_background() -> None:
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_check_loop, daemon=True).start()
