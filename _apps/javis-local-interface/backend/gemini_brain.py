"""gemini_brain.py — Cérebro rápido/grátis (Gemini Flash) via API REST.

Motivo: comando de voz quer LLM de baixa latência sem gastar a assinatura Claude.
Interface espelha claude_brain (available/answer) pra plugar no pipeline de voz sem
mudar quem chama. Self-contained: só urllib (sem SDK), lê GEMINI_API_KEY do ambiente.

Ativação (quando a chave existir no .env):
    GEMINI_API_KEY=...            # grátis em https://aistudio.google.com/apikey
    GEMINI_MODEL=gemini-2.0-flash # opcional (default flash)
    JAVIS_VOICE_BRAIN=gemini      # liga o roteamento da voz (fiação posterior)

NÃO é ligado em lugar nenhum ainda — só o cliente. A fiação no /voice vem depois,
testada ao vivo com a chave.
"""
from __future__ import annotations
import os
import json
import urllib.request
import urllib.error

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or "").strip()


def _model() -> str:
    return (os.environ.get("GEMINI_MODEL") or "gemini-2.0-flash").strip()


def available() -> bool:
    """True se há chave configurada (não faz chamada de rede)."""
    return bool(_key())


def answer(question: str, context: str = "", system: str | None = None,
           timeout: int | None = None, model: str | None = None,
           max_tokens: int = 800, temperature: float = 0.6) -> str:
    """Responde via Gemini Flash. Retorna texto (ou string de erro amigável, nunca lança).

    `max_tokens`/`temperature` são ajustáveis (extração de DNA precisa de saída
    grande e temperatura baixa; o chat de voz usa o default curto)."""
    key = _key()
    if not key:
        return "Gemini não configurado (falta GEMINI_API_KEY), senhor."
    q = (question or "").strip()
    if not q:
        return ""
    user = (f"{context}\n\n{q}" if context else q)
    body = {
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    url = _ENDPOINT.format(model=(model or _model())) + f"?key={key}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout or 30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        cands = payload.get("candidates") or []
        if not cands:
            # bloqueio de safety ou vazio
            fb = payload.get("promptFeedback", {})
            return f"Gemini não devolveu resposta{(' (' + str(fb) + ')') if fb else ''}, senhor."
        parts = (cands[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        return text or "Gemini respondeu vazio, senhor."
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8")[:200]
        except Exception:
            pass
        return f"Gemini falhou ({e.code}){(': ' + detail) if detail else ''}, senhor."
    except Exception as e:
        return f"Gemini indisponível agora, senhor: {e}"


def ping() -> dict:
    """Teste rápido de conectividade/chave — usado por um script, não pelo app."""
    if not available():
        return {"ok": False, "reason": "sem GEMINI_API_KEY"}
    out = answer("responda apenas: ok", timeout=15)
    return {"ok": out.strip().lower().startswith("ok"), "model": _model(), "sample": out[:80]}
