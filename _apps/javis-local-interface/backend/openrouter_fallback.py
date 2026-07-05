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

# IDs free conhecidos (ordem = prioridade). Modelo free do OpenRouter expira em
# dias/semanas — reconfira via OPENROUTER_FREE_MODELS se todos falharem.
# Atualizado 2026-07-05 após bateria de teste real (extração JSON estruturada):
# - openrouter/free: auto-roteia, NÃO expira, best cobertura (5 itens no teste).
# - nemotron 3 Ultra 550B (1M ctx) / Super 120B: sólidos, respondem sem 429.
# - qwen3-coder, gemma-4, gpt-oss caíram em 429 na hora do teste → não usar
#   como fallback primário (podem voltar; ficam de reserva se editar via env).
_DEFAULT_FREE = [
    "openrouter/free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
]

_URL = "https://openrouter.ai/api/v1/chat/completions"


def available() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _models() -> list[str]:
    env = os.environ.get("OPENROUTER_FREE_MODELS", "")
    if env.strip():
        return [m.strip() for m in env.split(",") if m.strip()]
    return _DEFAULT_FREE


def call(messages: list[dict], temperature: float = 0.7,
         max_tokens: int | None = None, timeout: int = 45) -> str | None:
    """Tenta os modelos free em ordem; devolve o 1º texto válido, ou None.

    `max_tokens` opcional — extração de DNA pede saída grande; o chat deixa None."""
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
            body = {"model": model, "messages": messages, "temperature": temperature}
            if max_tokens:
                body["max_tokens"] = max_tokens
            r = requests.post(_URL, headers=headers, timeout=timeout, json=body)
            if r.status_code != 200:
                continue
            data = r.json()
            txt = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            if txt and txt.strip():
                return txt.strip()
        except Exception:
            continue
    return None
