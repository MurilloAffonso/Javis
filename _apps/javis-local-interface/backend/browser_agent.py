"""browser_agent.py — capacidade de OPERAR o navegador (browser-use).

Game-changer: o Javis clica/preenche/navega como humano em sites reais
(Instagram, Meta Ads, WhatsApp Web, Google, reservas). Roda via OpenRouter.

Segurança: ação em site real = risco → deve passar SEMPRE por aprovação humana
(o chamador decide). Ativa só se OPENROUTER_API_KEY existir.

Import direto dos submódulos: o top-level do browser-use tenta importar todos os
providers (inclui Oracle 'oci', que não temos) e quebra — então NÃO usar
`import browser_use` / `from browser_use import Agent`.
"""
from __future__ import annotations
import os

import safe_config


def available() -> bool:
    if not safe_config.browser_enabled():
        return False
    if not os.environ.get("OPENROUTER_API_KEY"):
        return False
    try:
        from browser_use.agent.service import Agent  # noqa: F401
        from browser_use.llm.openai.chat import ChatOpenAI  # noqa: F401
        return True
    except Exception:
        return False


def _llm():
    from browser_use.llm.openai.chat import ChatOpenAI
    # browser-use usa VISÃO (screenshots) → o modelo PRECISA aceitar imagem.
    # Default: Gemini 2.0 Flash free (tem visão). Modelo pago (claude/gpt-4o) é
    # mais confiável p/ cliques; troque via BROWSER_USE_MODEL.
    model = os.environ.get("BROWSER_USE_MODEL", "google/gemma-4-31b-it:free")
    return ChatOpenAI(
        model=model,
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.2,
    )


async def run_task(task: str, max_steps: int = 12) -> dict:
    """Executa uma tarefa no navegador e devolve o resultado. Async."""
    if not (task or "").strip():
        return {"status": "error", "message": "Tarefa vazia."}
    if not safe_config.browser_enabled():
        return safe_config.disabled_response("browser", safe_config.JAVIS_ENABLE_BROWSER)
    if not available():
        return {"status": "error",
                "message": "Operação de navegador indisponível: precisa de OPENROUTER_API_KEY "
                           "e do browser-use instalado, senhor."}
    from browser_use.agent.service import Agent
    try:
        agent = Agent(task=task, llm=_llm())
        history = await agent.run(max_steps=max_steps)
        result = ""
        try:
            result = history.final_result() or ""
        except Exception:
            result = ""
        return {"status": "ok", "result": (result or "Tarefa concluída no navegador, senhor."),
                "task": task}
    except Exception as e:
        return {"status": "error", "message": f"Falha ao operar o navegador, senhor: {e}"}
