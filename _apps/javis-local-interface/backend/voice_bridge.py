"""Voice Bridge — classifica e executa transcrições de voz.

Fase 2 ativa (aprovado por Murillo, 2026-06-13): intents seguros executam via _brain() no server.
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
    # wake words (variações do nome — Jamba e como o ASR costuma ouvir)
    "jamba", "jambo", "jambá", "jamb", "javis", "jarvis", "javes",
    "diabes", "diaves", "chaves",
    # saudações comuns antes do comando
    "olá", "ola", "oi", "ei", "hey", "e aí", "eai",
]
_PREFIX_RE = re.compile(
    r"^(?:(?:" + "|".join(re.escape(w) for w in _PREFIX_WORDS) + r")[,!?\s]+)+",
    re.IGNORECASE,
)
# Palavras que ABREM o portão do microfone sempre-ligado (has_wake_word).
# Nome oficial = "Javis" (decisão Murillo 18/06). Mantém só as variações que o
# Whisper de fato produz pra "Javis" (medido na gravação dele: "Javis" com o
# initial_prompt, "Javes" sem). "jarvis" entra porque é o erro mais comum e
# próximo. Os palpites antigos (jamba/diabes/chaves) saíram daqui pra não abrir
# o portão à toa — continuam só no _PREFIX_WORDS (corte de prefixo em comando).
WAKE_WORDS = ["javis", "javes", "jávis", "jáves", "jarvis"]

# Palavras-chave que surgem em hallucinations do prompt — natural speech raramente
# contém 5+ destas ao mesmo tempo
_HALLUCINATION_WORDS = {
    "jamba", "javis", "javes", "jarvis",    # wake words
    "youtube", "webui", "vscode",  # apps específicos
    "status", "sistema",           # contexto de sistema
    "terminal", "navegador",       # apps/contexto
}
_HALLUCINATION_THRESHOLD = 5


def _strip_wake_word(text: str) -> str:
    """Remove greeting/wake-word prefix from voice transcript before routing."""
    return _PREFIX_RE.sub("", text).strip()


# Portão de ativação p/ microfone sempre-ligado (sandbox de voz / VTuber). Só os
# nomes de ativação contam — saudações genéricas (oi/ei/hey) NÃO abrem o portão,
# senão qualquer fala de fundo destrava a escuta.
_WAKE_ONLY_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in WAKE_WORDS) + r")\b", re.IGNORECASE
)


def has_wake_word(text: str) -> bool:
    """True se a palavra de ativação (Jamba/Javis/...) aparece em qualquer ponto do texto."""
    return bool(_WAKE_ONLY_RE.search(text or ""))


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
    "status_sistema", "analisar_site", "clima", "conversa", "desconhecido",
    "hora_data", "listar_lembretes", "pesquisar_google", "ler_pagina",
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
        note = "seguro — executa via _brain() no server"
    else:
        would_execute = False
        note = "intent desconhecido — encaminhado ao LLM"

    result = {
        "source": "voice",
        "transcript": transcript,
        "intent": intent,
        "confidence": route["confidence"],
        "risk_level": route["risk_level"],
        "requires_approval": route["requires_approval"],
        "action": route["action"],
        "dry_run": False,
        "would_execute": would_execute,
        "reason": route["reason"],
        "note": note,
    }

    logger.log(
        source="voice",
        user_text=transcript,
        route=route,
        action_result={"status": "executed" if would_execute else "routed_to_llm", "message": note},
        approved=would_execute,
        duration_ms=duration,
        extra={"transcript": transcript, "clean_transcript": clean, "dry_run": False, "would_execute": would_execute, "note": note},
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
