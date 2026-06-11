"""Command Router — classifica intenção por palavras-chave, sem LLM."""
from __future__ import annotations
import re


RULES: list[tuple[str, list[str]]] = [
    ("acao_perigosa",  ["apaga", "apagar", "deleta", "deletar", "formata", "formatar",
                        "instala", "instalar", "remove", "remover", "destroi", "destruir",
                        "git push", "git reset", "git force", "drop", "truncate",
                        "rm -rf", "del /f", "format c"]),
    ("abrir_youtube",  ["youtube"]),
    ("tocar_musica",   ["toca ", "tocar ", "música", "musica", "playlist", "som relaxante",
                        "coloca uma música", "coloca musica", "play "]),
    ("abrir_openwebui",["open webui", "openwebui", "webui", "localhost:3000",
                        "abre o javis no navegador"]),
    ("abrir_vscode",   ["vscode", "vs code", "visual studio code", "editor de código",
                        "editor de codigo", "code ."]),
    ("abrir_terminal", ["terminal", "powershell", "cmd", "prompt de comando",
                        "linha de comando"]),
    ("abrir_navegador",["navegador", "chrome", "firefox", "edge", "browser", "internet"]),
    ("abrir_projeto",  ["abre o projeto", "abrir projeto", "projeto "]),
    ("abrir_javis",    ["pasta do javis", "pasta javis", "diretório javis",
                        "abre o javis", "abrir javis"]),
    ("registrar_ideia",["anota", "anotar", "captura ideia", "registra ideia",
                        "salva ideia", "ideia:", "tive uma ideia"]),
    ("status_sistema", ["status", "tá funcionando", "ta funcionando",
                        "tudo ok", "tudo funcionando", "tá tudo", "ta tudo", "está tudo", "esta tudo",
                        "check sistema", "verifica sistema",
                        "sistema ok", "como estão os serviços",
                        "o sistema", "tá o sistema", "ta o sistema",
                        "está o sistema", "esta o sistema"]),
]

CONVERSATION_HINTS = [
    "como", "o que", "me explica", "explica", "quem", "quando", "onde",
    "por que", "porque", "qual", "você", "voce", "me ajuda", "ajuda",
    "preciso", "quero saber",
]

RISK_MAP = {
    "acao_perigosa":  ("critical", True),
    "abrir_terminal": ("medium",   True),
    "abrir_projeto":  ("low",      False),
    "abrir_javis":    ("low",      False),
    "abrir_navegador":("low",      False),
    "abrir_youtube":  ("low",      False),
    "tocar_musica":   ("low",      False),
    "abrir_openwebui":("low",      False),
    "abrir_vscode":   ("low",      False),
    "registrar_ideia":("low",      False),
    "status_sistema": ("low",      False),
    "conversa":       ("none",     False),
    "desconhecido":   ("none",     False),
}

ACTION_MAP = {
    "abrir_navegador": "open_browser",
    "abrir_youtube":   "open_url",
    "tocar_musica":    "open_url",
    "abrir_openwebui": "open_url",
    "abrir_javis":     "open_folder",
    "abrir_vscode":    "open_vscode",
    "abrir_terminal":  "open_terminal",
    "abrir_projeto":   "open_folder",
    "registrar_ideia": "write_file",
    "status_sistema":  "check_status",
    "acao_perigosa":   "blocked",
    "conversa":        "llm_chat",
    "desconhecido":    "llm_chat",
}


def route(text: str) -> dict:
    """Classifica o texto e retorna um dicionário de roteamento."""
    normalized = text.lower().strip()
    normalized = re.sub(r"[^\w\sáéíóúàâêôãõüç:./\\-]", " ", normalized)

    intent = _classify(normalized)
    risk_level, requires_approval = RISK_MAP.get(intent, ("none", False))
    action = ACTION_MAP.get(intent, "llm_chat")

    return {
        "intent": intent,
        "confidence": _confidence(intent, normalized),
        "risk_level": risk_level,
        "requires_approval": requires_approval,
        "action": action,
        "reason": _reason(intent, normalized),
        "original_text": text,
    }


def _classify(text: str) -> str:
    for intent, keywords in RULES:
        for kw in keywords:
            if kw in text:
                return intent

    for hint in CONVERSATION_HINTS:
        if hint in text:
            return "conversa"

    if len(text.split()) <= 3:
        return "desconhecido"

    return "conversa"


def _confidence(intent: str, text: str) -> str:
    if intent in ("acao_perigosa", "abrir_youtube", "status_sistema"):
        return "high"
    if intent == "desconhecido":
        return "low"
    return "medium"


def _reason(intent: str, text: str) -> str:
    reasons = {
        "acao_perigosa":  "palavra-chave de ação destrutiva detectada",
        "abrir_youtube":  "palavra-chave 'youtube' detectada",
        "tocar_musica":   "palavra-chave de música detectada",
        "abrir_openwebui":"referência ao Open WebUI detectada",
        "abrir_vscode":   "referência ao VS Code detectada",
        "abrir_terminal": "referência ao terminal detectada",
        "abrir_navegador":"referência ao navegador detectada",
        "abrir_projeto":  "referência a projeto detectada",
        "abrir_javis":    "referência à pasta do Javis detectada",
        "registrar_ideia":"intenção de anotação detectada",
        "status_sistema": "palavra-chave de status detectada",
        "conversa":       "sem ação identificada — encaminhar ao LLM",
        "desconhecido":   "texto curto ou sem padrão reconhecido",
    }
    return reasons.get(intent, "sem regra correspondente")
