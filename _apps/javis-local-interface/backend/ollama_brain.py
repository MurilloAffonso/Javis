"""ollama_brain.py — Cérebro LOCAL rápido (Ollama) para comando de voz.

Zero nuvem, zero chave, zero quota: roda no PC do Murillo. Interface espelha
claude_brain (available/answer) pra plugar no pipeline de voz. Modelo default
llama3.2:3b (leve, baixa latência). Self-contained: só urllib.

Ligar (quando a fiação da voz existir):
    JAVIS_VOICE_BRAIN=ollama        # roteia a voz conversacional pro Ollama
    OLLAMA_VOICE_MODEL=llama3.2:3b  # opcional
    OLLAMA_HOST=http://localhost:11434  # opcional
"""
from __future__ import annotations
import os
import json
import urllib.request


def _host() -> str:
    """Base URL do Ollama, robusta ao OLLAMA_HOST do ambiente.

    OLLAMA_HOST costuma ser o endereço de BIND do servidor (ex.: '0.0.0.0:11434'
    ou '0.0.0.0'), que não serve como alvo de cliente e às vezes vem sem esquema.
    Normaliza: adiciona http://, troca 0.0.0.0 por loopback, completa a porta.
    """
    h = (os.environ.get("OLLAMA_HOST") or "").strip()
    if not h:
        return "http://localhost:11434"
    if "://" not in h:
        h = "http://" + h
    h = h.replace("0.0.0.0", "127.0.0.1").rstrip("/")
    # sem porta explícita → assume a padrão do Ollama
    tail = h.split("://", 1)[1]
    if ":" not in tail:
        h = h + ":11434"
    return h


def _model() -> str:
    return (os.environ.get("OLLAMA_VOICE_MODEL") or "llama3.2:3b").strip()


def available(timeout: int = 2) -> bool:
    """True se o Ollama responde E o modelo de voz está baixado (sem gerar nada)."""
    try:
        with urllib.request.urlopen(_host() + "/api/tags", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        base = _model().split(":")[0]
        return any(base in (m.get("name") or "") for m in data.get("models", []))
    except Exception:
        return False


def answer(question: str, context: str = "", system: str | None = None,
           timeout: int | None = None, model: str | None = None) -> str:
    """Responde via Ollama local. Nunca lança — devolve texto ou erro amigável."""
    q = (question or "").strip()
    if not q:
        return ""
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": (f"{context}\n\n{q}" if context else q)})
    body = {
        "model": model or _model(),
        "messages": msgs,
        "stream": False,
        # mantém o modelo carregado na RAM entre comandos de voz (senão recarrega
        # do zero a cada fala — a carga fria é o que dói na latência).
        "keep_alive": os.environ.get("OLLAMA_KEEP_ALIVE", "15m"),
        "options": {"temperature": 0.5, "num_predict": 400},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(_host() + "/api/chat", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout or 60) as r:
            payload = json.loads(r.read().decode("utf-8"))
        text = ((payload.get("message") or {}).get("content") or "").strip()
        return text or "Não consegui formular agora, senhor."
    except Exception as e:
        return f"Ollama indisponível, senhor: {e}"


def answer_stream(question: str, context: str = "", system: str | None = None,
                  model: str | None = None):
    """Gera a resposta em pedaços (para TTS frase-a-frase na voz). Espelha
    claude_brain.answer_stream: yield de trechos de texto conforme o modelo produz."""
    q = (question or "").strip()
    if not q:
        return
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": (f"{context}\n\n{q}" if context else q)})
    body = {
        "model": model or _model(),
        "messages": msgs,
        "stream": True,
        "keep_alive": os.environ.get("OLLAMA_KEEP_ALIVE", "15m"),
        "options": {"temperature": 0.5, "num_predict": 400},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(_host() + "/api/chat", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            for raw in r:
                raw = raw.decode("utf-8").strip()
                if not raw:
                    continue
                obj = json.loads(raw)
                chunk = (obj.get("message") or {}).get("content", "")
                if chunk:
                    yield chunk
                if obj.get("done"):
                    break
    except Exception:
        return


def ping() -> dict:
    """Teste de fumaça (usado por script, não pelo app)."""
    if not available():
        return {"ok": False, "reason": "Ollama desligado ou modelo ausente"}
    out = answer("Responda apenas com a palavra: ok", timeout=30)
    return {"ok": "ok" in out.strip().lower()[:10], "model": _model(), "sample": out[:80]}
