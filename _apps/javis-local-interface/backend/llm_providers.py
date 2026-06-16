"""LLM Providers — Claude (Anthropic) · OpenAI · Ollama (fallback).

Prioridade:
  Cérebro orquestrador / main brain  → Claude  (ANTHROPIC_API_KEY)
  Conclave / agentes especializados  → OpenAI  (OPENAI_API_KEY)
  Fallback (sem chave)               → Ollama local
"""
from __future__ import annotations
import os
import requests

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = os.environ.get("JAVIS_OLLAMA_MODEL", "llama3.2:3b")
TIMEOUT      = int(os.environ.get("JAVIS_OLLAMA_TIMEOUT", "8"))

CLAUDE_MODEL = os.environ.get("JAVIS_CLAUDE_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.environ.get("JAVIS_OPENAI_MODEL", "gpt-4o-mini")


def _anthropic_enabled() -> bool:
    """Anthropic só é usada se houver chave E o senhor ligar explicitamente.

    Default = 100% OpenAI (a chave Anthropic está sem crédito). Para religar:
    JAVIS_USE_ANTHROPIC=1 no .env.
    """
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return False
    return os.environ.get("JAVIS_USE_ANTHROPIC", "0").strip().lower() in ("1", "true", "yes", "on")


def call_claude(messages: list[dict], temperature: float = 0.7) -> str:
    """Cérebro orquestrador. Default 100% OpenAI; Anthropic só se habilitada."""
    if not _anthropic_enabled():
        return call_openai(messages, temperature)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        system_text = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        user_msgs   = [m for m in messages if m["role"] != "system"]
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=system_text or "Você é o Javis.",
            messages=user_msgs,
            temperature=temperature,
        )
        return resp.content[0].text.strip()
    except Exception as e:
        # Anthropic indisponível (ex.: sem crédito) → OpenAI, que é o cérebro
        # configurado e tem saldo. Só cai no Ollama se a OpenAI também falhar.
        print(f"[llm] Claude falhou ({e}); usando OpenAI.", flush=True)
        return call_openai(messages, temperature)


def call_openai(messages: list[dict], temperature: float = 0.7) -> str:
    """Agentes especializados — OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return _call_ollama(messages)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return _call_ollama(messages)


def _stream_openai(messages: list[dict], temperature: float = 0.7):
    """Streaming real de tokens via OpenAI (cérebro padrão)."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        yield _call_ollama(messages)
        return
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    stream = client.chat.completions.create(
        model=OPENAI_MODEL, messages=messages, temperature=temperature, stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def stream_claude(messages: list[dict], temperature: float = 0.7):
    """Gerador síncrono de tokens — Anthropic se habilitada, senão OpenAI (padrão)."""
    if not _anthropic_enabled():
        try:
            yield from _stream_openai(messages, temperature)
        except Exception as e:
            yield f"⚠️ OpenAI indisponível, senhor: {e}"
        return
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        system_text = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        user_msgs   = [m for m in messages if m["role"] != "system"]
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=system_text or "Você é o Javis.",
            messages=user_msgs,
            temperature=temperature,
        ) as stream:
            for token in stream.text_stream:
                yield token
    except Exception as e:
        # Claude indisponível (ex.: sem crédito) → OpenAI (não-stream, bloco único),
        # depois Ollama como último recurso.
        print(f"[llm] stream Claude falhou ({e}); usando OpenAI.", flush=True)
        try:
            yield call_openai(messages, temperature)
        except Exception as e2:
            yield f"⚠️ Claude e OpenAI indisponíveis, senhor: {e2}"


def embed(text: str) -> list[float] | None:
    """Embedding semântico via OpenAI text-embedding-3-small."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:2000],
        )
        return resp.data[0].embedding
    except Exception:
        return None


def _call_ollama(messages: list[dict], model: str | None = None) -> str:
    """Fallback local — Ollama."""
    resp = requests.post(
        OLLAMA_URL,
        json={"model": model or OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()
