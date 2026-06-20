"""LLM Providers — Claude pela ASSINATURA (claude_brain), cérebro ÚNICO.

Decisão Murillo 18/06: nada de API paga. Decisão 19/06: nada de Ollama também —
o Claude (assinatura) é a base de TUDO. Sem fallback local: se a assinatura
estiver indisponível (Claude Code não logado) ou sem cota, o Javis diz isso na
cara, em vez de cair num Ollama offline que dava erro técnico confuso.

`call_claude` e `call_openai` são o MESMO cérebro — o segundo nome ficou como
alias só porque dezenas de chamadores (Conclave, squads, analyzers, orchestrator)
ainda importam um ou outro; não há mais dois provedores reais.
"""
from __future__ import annotations
import os

import claude_brain

_SEM_CEREBRO = (
    "Estou sem cérebro disponível agora, senhor: o Claude pela assinatura não "
    "respondeu (pode ser cota semanal esgotada ou o Claude Code deslogado). "
    "Quando a cota voltar eu retomo."
)


def _split_messages(messages: list[dict]) -> tuple[str, str, str]:
    """Converte uma lista de mensagens chat (system/user/assistant) no formato
    que o claude_brain entende: (system_text, context, question)."""
    system_text = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    convo = [m for m in messages if m["role"] != "system"]
    question = convo[-1]["content"] if convo else ""
    context = "\n".join(f"{m['role']}: {m['content']}" for m in convo[:-1])
    return system_text, context, question


def call_claude(messages: list[dict], temperature: float = 0.7) -> str:
    """Cérebro único — Claude pela assinatura. Sem fallback: mensagem clara se faltar."""
    if claude_brain.available():
        system_text, context, question = _split_messages(messages)
        out = claude_brain.answer(question, context, system=system_text or None)
        if out:
            return out
    return _SEM_CEREBRO


# Mesmo cérebro — alias para os chamadores que ainda pedem "openai".
call_openai = call_claude


def stream_claude(messages: list[dict], temperature: float = 0.7):
    """Gerador síncrono de tokens — Claude pela assinatura. Sem fallback local."""
    if claude_brain.available():
        system_text, context, question = _split_messages(messages)
        got = False
        for chunk in claude_brain.answer_stream(question, context, system=system_text or None):
            got = True
            yield chunk
        if got:
            return
    yield _SEM_CEREBRO


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
