"""openrouter_voice.py — cérebro de VOZ via OpenRouter free (rápido e grátis).

Descoberto no teste 2026-07-05: `openrouter/free` responde saudações em 0.7-2.0s
mantendo pt-BR limpo e a persona ("senhor"). O Claude assinatura levava ~20s
por chamada — a voz ficava lenta. Este módulo pluga como cérebro de voz opcional
(ativa com JAVIS_VOICE_BRAIN=openrouter no .env).

Interface espelha ollama_brain / claude_brain: `answer_stream(pergunta, contexto,
system=...)` retorna um generator de sentenças (compat com o loop de TTS incremental).
Streaming REAL via SSE do OpenRouter — o TTS começa a falar assim que a 1ª sentença fica pronta.
"""
from __future__ import annotations
import os
import json
import re

_URL = "https://openrouter.ai/api/v1/chat/completions"

# Ordem = fallback. openrouter/free ganhou no teste (0.7-2s, pt-BR limpo,
# tom certo). Nemotron 3 Ultra 550B é reserva (~4-15s mas resposta rica).
_DEFAULT = [
    "openrouter/free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]


def available() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _models() -> list[str]:
    env = os.environ.get("OPENROUTER_VOICE_MODELS", "")
    if env.strip():
        return [m.strip() for m in env.split(",") if m.strip()]
    return _DEFAULT


def answer_stream(pergunta: str, contexto: str = "",
                  system: str | None = None, timeout: int = 25):
    """Yields fragmentos de texto conforme chegam. Tenta cada modelo em ordem;
    se todos falharem, o generator termina sem yield (chamador cai no próximo brain)."""
    if not available() or not pergunta.strip():
        return
    try:
        import requests
    except Exception:
        return

    sys_msg = system or ("Você é o Javes, mordomo de IA do Murillo. Chame-o de 'senhor'. "
                         "Responda em português do Brasil, curto e direto (1-3 frases), "
                         "tom sereno e prático. Sem enumeração longa, sem markdown pesado.")
    user = (f"Contexto:\n{contexto}\n\nPergunta:\n{pergunta}" if contexto else pergunta)
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost/javis",
        "X-Title": "Javis",
    }

    for model in _models():
        try:
            body = {
                "model": model, "temperature": 0.6, "max_tokens": 350, "stream": True,
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user},
                ],
            }
            resp = requests.post(_URL, headers=headers, json=body, stream=True, timeout=timeout)
            if resp.status_code != 200:
                continue
            got_any = False
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                    delta = (obj.get("choices") or [{}])[0].get("delta") or {}
                    chunk = delta.get("content") or ""
                    if chunk:
                        got_any = True
                        yield chunk
                except Exception:
                    continue
            if got_any:
                return  # sucesso — não tenta próximo modelo
        except Exception:
            continue
    return


def answer(pergunta: str, contexto: str = "", system: str | None = None,
           timeout: int = 25) -> str:
    """Versão não-stream (junta o generator). Útil pra testes e chamadas simples."""
    return "".join(answer_stream(pergunta, contexto, system, timeout)).strip()
