"""Telegram Bridge — controlar o Jamba pelo celular via long polling.

Sobe um thread em segundo plano (só se TELEGRAM_BOT_TOKEN estiver no .env).
Não precisa de webhook nem URL pública — usa getUpdates (long polling).

Fluxo: mensagem do Telegram → command_router → ação local ou cérebro principal → resposta.
"""
from __future__ import annotations
import os
import time
import threading
import requests

_API = "https://api.telegram.org/bot{token}/{method}"
_TIMEOUT = 40
_started = False


def _call(token: str, method: str, **kwargs):
    return requests.post(_API.format(token=token, method=method), timeout=20, **kwargs)


def _send(token: str, chat_id: int, text: str) -> None:
    try:
        _call(token, "sendMessage", json={"chat_id": chat_id, "text": text[:4000]})
    except Exception:
        pass


def _handle(text: str) -> str:
    """Roteia a mensagem: ações de info executam; o resto vai pro cérebro principal."""
    import command_router
    import actions

    route = command_router.route(text)
    intent = route["intent"]

    # Ações que fazem sentido pelo celular (info, não abrir apps no PC)
    if intent in ("clima", "status_sistema", "analisar_site"):
        return actions.execute(intent, text).get("message", "Feito, senhor.")

    if intent == "acao_perigosa":
        return "Essa ação eu não executo por aqui, senhor."

    # Conversa → cérebro principal (Claude)
    from orchestrator import SYSTEM_MAIN_BRAIN
    from llm_providers import call_claude
    try:
        return call_claude([
            {"role": "system", "content": SYSTEM_MAIN_BRAIN},
            {"role": "user", "content": text},
        ])
    except Exception as e:
        return f"Tive um problema ao pensar, senhor: {e}"


def _run_polling(token: str) -> None:
    allowed = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
    offset = None
    print("  Telegram bridge: online (long polling)")

    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset
            r = requests.get(_API.format(token=token, method="getUpdates"),
                             params=params, timeout=_TIMEOUT)
            updates = r.json().get("result", [])
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message") or {}
                text = (msg.get("text") or "").strip()
                chat = msg.get("chat") or {}
                chat_id = chat.get("id")
                if not text or chat_id is None:
                    continue

                # Trava de segurança opcional
                if allowed and str(chat_id) != allowed:
                    _send(token, chat_id, "Não autorizado.")
                    continue

                if text.lower() in ("/start", "/help"):
                    _send(token, chat_id,
                          f"Jamba online, senhor. Pode falar normalmente.\n"
                          f"Seu chat ID é {chat_id} (use em TELEGRAM_ALLOWED_CHAT_ID para travar o bot).")
                    continue

                reply = _handle(text)
                _send(token, chat_id, reply or "Sem resposta, senhor.")
        except Exception:
            time.sleep(3)


def start_background() -> bool:
    """Inicia o polling num thread daemon se houver token. Retorna True se iniciou."""
    global _started
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or _started:
        return False
    _started = True
    threading.Thread(target=_run_polling, args=(token,), daemon=True).start()
    return True
