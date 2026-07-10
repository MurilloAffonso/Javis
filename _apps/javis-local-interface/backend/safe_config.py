"""Safe startup flags for the legacy Javis backend."""
from __future__ import annotations

import os

_TRUE_VALUES = {"1", "true", "yes", "y", "on", "sim"}


def flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES


JAVIS_ENABLE_EXTERNAL_ADAPTERS = "JAVIS_ENABLE_EXTERNAL_ADAPTERS"
JAVIS_ENABLE_CODEX_EXEC = "JAVIS_ENABLE_CODEX_EXEC"
JAVIS_ENABLE_CLAUDE_EXEC = "JAVIS_ENABLE_CLAUDE_EXEC"
JAVIS_ENABLE_BROWSER = "JAVIS_ENABLE_BROWSER"
JAVIS_ENABLE_TELEGRAM = "JAVIS_ENABLE_TELEGRAM"
JAVIS_ENABLE_MCP = "JAVIS_ENABLE_MCP"
JAVIS_ENABLE_LOCAL_ACTIONS = "JAVIS_ENABLE_LOCAL_ACTIONS"
JAVIS_ENABLE_SUPERVISED_EXEC = "JAVIS_ENABLE_SUPERVISED_EXEC"
JAVIS_ENABLE_VP_EFFECTS = "JAVIS_ENABLE_VP_EFFECTS"
JAVIS_DEV_ALLOW_CORS = "JAVIS_DEV_ALLOW_CORS"


def external_adapters_enabled() -> bool:
    return flag(JAVIS_ENABLE_EXTERNAL_ADAPTERS, False)


JAVES_PROVIDER_MODE = "JAVES_PROVIDER_MODE"


def provider_mode() -> str:
    """Modo de provider do chat (R2.1). Valores: 'local' | 'cloud' | 'auto'.

    - local: SÓ Ollama; nunca cai silenciosamente na nuvem. Se o Ollama estiver
      indisponível, o chamador devolve provider_unavailable.
    - cloud: cadeia externa (Gemini/OpenAI/Claude/OpenRouter), como antes.
    - auto (default): tenta Ollama primeiro; a nuvem só entra se o Ollama não
      responder E os adaptadores externos estiverem habilitados.
    """
    raw = (os.environ.get(JAVES_PROVIDER_MODE) or "auto").strip().lower()
    return raw if raw in {"local", "cloud", "auto"} else "auto"


def codex_exec_enabled() -> bool:
    return external_adapters_enabled() and flag(JAVIS_ENABLE_CODEX_EXEC, False)


def claude_exec_enabled() -> bool:
    return external_adapters_enabled() and flag(JAVIS_ENABLE_CLAUDE_EXEC, False)


def browser_enabled() -> bool:
    return external_adapters_enabled() and flag(JAVIS_ENABLE_BROWSER, False)


def telegram_enabled() -> bool:
    return external_adapters_enabled() and flag(JAVIS_ENABLE_TELEGRAM, False)


def mcp_enabled() -> bool:
    return external_adapters_enabled() and flag(JAVIS_ENABLE_MCP, False)


def local_actions_enabled() -> bool:
    return flag(JAVIS_ENABLE_LOCAL_ACTIONS, False)


def supervised_execution_enabled() -> bool:
    """Executor supervisionado em worktree (R4). Desligado por padrão; a R4.1 é
    só fundação (nenhum agente roda mesmo com a flag ligada)."""
    return flag(JAVIS_ENABLE_SUPERVISED_EXEC, False)


def vp_effects_enabled() -> bool:
    return flag(JAVIS_ENABLE_VP_EFFECTS, False)


def dev_allow_cors() -> bool:
    return flag(JAVIS_DEV_ALLOW_CORS, False)


def cors_origins() -> list[str]:
    if dev_allow_cors():
        return ["*"]
    raw = os.environ.get("JAVIS_CORS_ORIGINS", "").strip()
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    return [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
    ]


def disabled_response(capability: str, flag_hint: str = "") -> dict:
    return {
        "status": "disabled_by_default",
        "reason": "requires_explicit_enable",
        "capability": capability,
        "flag": flag_hint,
        "message": disabled_message(capability, flag_hint),
    }


def disabled_message(capability: str, flag_hint: str = "") -> str:
    suffix = f" ({flag_hint})" if flag_hint else ""
    return f"disabled_by_default: {capability} requires_explicit_enable{suffix}"


EXPECTED_FLAGS = [
    JAVIS_ENABLE_EXTERNAL_ADAPTERS,
    JAVIS_ENABLE_CODEX_EXEC,
    JAVIS_ENABLE_CLAUDE_EXEC,
    JAVIS_ENABLE_BROWSER,
    JAVIS_ENABLE_TELEGRAM,
    JAVIS_ENABLE_MCP,
    JAVIS_ENABLE_LOCAL_ACTIONS,
    JAVIS_ENABLE_SUPERVISED_EXEC,
    JAVIS_ENABLE_VP_EFFECTS,
    JAVIS_DEV_ALLOW_CORS,
]
