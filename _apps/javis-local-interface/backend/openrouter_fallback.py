"""OpenRouter fallback — plano B free-first quando o Claude (assinatura) falha.

Minerado do padrão de providers do Hermes Agent (NousResearch, MIT). NÃO muda o
caminho feliz: só ativa se OPENROUTER_API_KEY existir no .env e SOMENTE quando o
Claude pela assinatura não responder. Multi-ID porque modelo free do OpenRouter
expira em dias (memória: 'OpenRouter free é volátil') — tenta vários em ordem.

Configurável por env:
  OPENROUTER_API_KEY     — obrigatório para ativar
  OPENROUTER_FREE_MODELS — lista CSV de ids (sobrescreve os defaults)
"""
from __future__ import annotations
import os

# IDs free conhecidos (ordem = prioridade). gpt-oss-120b:free foi aprovado 3/3
# no teste de 23/06 (memória). Ajuste via OPENROUTER_FREE_MODELS se expirarem.
_DEFAULT_FREE = [
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-72b-instruct:free",
]

_URL = "https://openrouter.ai/api/v1/chat/completions"


def available() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _models() -> list[str]:
    env = os.environ.get("OPENROUTER_FREE_MODELS", "")
    if env.strip():
        return [m.strip() for m in env.split(",") if m.strip()]
    return _DEFAULT_FREE


def call(messages: list[dict], temperature: float = 0.7) -> str | None:
    """Tenta os modelos free em ordem; devolve o 1º texto válido, ou None."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return None
    try:
        import requests
    except Exception:
        return None
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost/javis",
        "X-Title": "Javis",
    }
    for model in _models():
        try:
            r = requests.post(_URL, headers=headers, timeout=45, json={
                "model": model, "messages": messages, "temperature": temperature,
            })
            if r.status_code != 200:
                continue
            data = r.json()
            txt = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            if txt and txt.strip():
                return txt.strip()
        except Exception:
            continue
    return None
