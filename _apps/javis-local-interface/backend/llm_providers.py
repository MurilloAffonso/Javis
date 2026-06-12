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
TIMEOUT      = 30

CLAUDE_MODEL = os.environ.get("JAVIS_CLAUDE_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.environ.get("JAVIS_OPENAI_MODEL", "gpt-4o-mini")


def call_claude(messages: list[dict], temperature: float = 0.7) -> str:
    """Cérebro orquestrador — Claude Anthropic."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _call_ollama(messages)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
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
    except Exception:
        return _call_ollama(messages)


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


def stream_claude(messages: list[dict], temperature: float = 0.7):
    """Gerador síncrono de tokens do Claude — para streaming SSE."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        try:
            yield _call_ollama(messages)
        except Exception as e:
            yield (
                "⚠️ Nenhuma API configurada e Ollama está offline.\n"
                "Configure ANTHROPIC_API_KEY ou OPENAI_API_KEY no arquivo .env "
                "ou inicie o Ollama."
            )
        return
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
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
    except Exception:
        try:
            yield _call_ollama(messages)
        except Exception as e:
            yield f"⚠️ Claude e Ollama indisponíveis: {e}"


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
