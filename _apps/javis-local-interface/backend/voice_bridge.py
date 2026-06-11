"""Voice Bridge — classifica transcrição de voz sem executar nada.

Modo: dry_run = True (sempre). Nesta fase, nenhuma ação é executada.
Uso:  python backend/voice_bridge.py "abre o youtube"
"""
from __future__ import annotations
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import command_router
import logger

_PREFIX_WORDS = [
    # wake words (variações do nome)
    "javis", "jarvis", "javes", "diabes", "diaves", "chaves",
    # saudações comuns antes do comando
    "olá", "ola", "oi", "ei", "hey", "e aí", "eai",
]
_PREFIX_RE = re.compile(
    r"^(?:(?:" + "|".join(re.escape(w) for w in _PREFIX_WORDS) + r")[,!?\s]+)+",
    re.IGNORECASE,
)
# mantém compatibilidade com código que importa WAKE_WORDS diretamente
WAKE_WORDS = ["javis", "jarvis", "javes", "diabes", "diaves", "chaves"]

# Palavras-chave que surgem em hallucinations do prompt — natural speech raramente
# contém 5+ destas ao mesmo tempo
_HALLUCINATION_WORDS = {
    "javis", "javes", "jarvis",    # wake words
    "youtube", "webui", "vscode",  # apps específicos
    "status", "sistema",           # contexto de sistema
    "terminal", "navegador",       # apps/contexto
}
_HALLUCINATION_THRESHOLD = 5


def _strip_wake_word(text: str) -> str:
    """Remove greeting/wake-word prefix from voice transcript before routing."""
    return _PREFIX_RE.sub("", text).strip()


def _is_hallucination(text: str) -> bool:
    """Return True if transcript looks like ASR hallucination of the initial_prompt.

    Fala natural raramente contém 5+ termos de comando distintos ao mesmo tempo.
    """
    lower = text.lower()
    found = sum(1 for w in _HALLUCINATION_WORDS if w in lower)
    return found >= _HALLUCINATION_THRESHOLD


SAFE_INTENTS = {
    "abrir_navegador", "abrir_youtube", "tocar_musica", "abrir_openwebui",
    "abrir_javis", "abrir_vscode", "abrir_projeto", "registrar_ideia",
    "status_sistema", "conversa", "desconhecido",
}

APPROVAL_INTENTS = {"abrir_terminal"}

BLOCKED_INTENTS = {"acao_perigosa"}


def classify_voice(transcript: str) -> dict:
    start = time.monotonic()
    clean = _strip_wake_word(transcript)

    if _is_hallucination(clean):
        duration = int((time.monotonic() - start) * 1000)
        _fake_route = {
            "intent": "desconhecido", "confidence": 0.0, "risk_level": "none",
            "requires_approval": False, "action": "noop",
            "reason": "hallucination", "original_text": transcript,
        }
        result = {
            "source": "voice", "transcript": transcript,
            "intent": "desconhecido", "confidence": 0.0,
            "risk_level": "none", "requires_approval": False,
            "action": "noop", "dry_run": True, "would_execute": False,
            "reason": "transcrição suspeita — possível hallucination do ASR",
            "note": "blocked_hallucination",
        }
        logger.log(
            source="voice", user_text=transcript, route=_fake_route,
            action_result={"status": "blocked_hallucination", "message": "transcrição suspeita"},
            approved=False, duration_ms=duration,
            extra={"transcript": transcript, "clean_transcript": clean,
                   "dry_run": True, "would_execute": False, "note": "blocked_hallucination"},
        )
        return result

    route = command_router.route(clean)
    duration = int((time.monotonic() - start) * 1000)

    intent = route["intent"]

    if intent in BLOCKED_INTENTS:
        would_execute = False
        note = "BLOQUEADO — acao_perigosa nunca executa por voz"
    elif intent in APPROVAL_INTENTS:
        would_execute = False
        note = "requer aprovacao explicita — nao executaria por voz nesta fase"
    elif intent in SAFE_INTENTS:
        would_execute = True
        note = "seguro — executaria via actions.execute() quando liberado"
    else:
        would_execute = False
        note = "intent desconhecido — encaminharia ao LLM"

    result = {
        "source": "voice",
        "transcript": transcript,
        "intent": intent,
        "confidence": route["confidence"],
        "risk_level": route["risk_level"],
        "requires_approval": route["requires_approval"],
        "action": route["action"],
        "dry_run": True,
        "would_execute": would_execute,
        "reason": route["reason"],
        "note": note,
    }

    logger.log(
        source="voice",
        user_text=transcript,
        route=route,
        action_result={"status": "dry_run_only", "message": note},
        approved=False,
        duration_ms=duration,
        extra={"transcript": transcript, "clean_transcript": clean, "dry_run": True, "would_execute": would_execute, "note": note},
    )

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python backend/voice_bridge.py \"texto transcrito\"")
        sys.exit(1)

    transcript = " ".join(sys.argv[1:])
    result = classify_voice(transcript)

    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
