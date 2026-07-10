"""Central registry for Javes model providers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import os
import socket
import urllib.parse

import safe_config
import provider_health


LOCAL = "local"
CLOUD = "cloud"
DEFAULT_PROJECT_ID = "javes-core"


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    display_name: str
    type: str
    requires_external_adapters: bool
    supports_chat: bool
    supports_tools: bool
    supports_embeddings: bool
    priority: int
    env_keys: tuple[str, ...] = ()
    model_env: str = ""
    default_model: str = ""


PROVIDERS: tuple[ProviderSpec, ...] = (
    ProviderSpec("ollama", "Ollama", LOCAL, False, True, False, True, 10, model_env="OLLAMA_VOICE_MODEL", default_model="llama3.2:3b"),
    ProviderSpec("gemini", "Gemini", CLOUD, True, True, True, False, 20, ("GEMINI_API_KEY",), "JAVIS_GEMINI_MODEL", "gemini-2.5-flash"),
    ProviderSpec("claude", "Claude", CLOUD, True, True, True, False, 30, ("ANTHROPIC_API_KEY",), "JAVIS_CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
    ProviderSpec("openai", "OpenAI", CLOUD, True, True, True, True, 40, ("OPENAI_API_KEY",), "JAVIS_OPENAI_MODEL", "gpt-4o-mini"),
    ProviderSpec("openrouter", "OpenRouter", CLOUD, True, True, True, False, 50, ("OPENROUTER_API_KEY",), "JAVIS_OPENROUTER_MODEL", "openai/gpt-oss-120b:free"),
)


def _configured(spec: ProviderSpec) -> bool:
    if spec.id == "ollama":
        return True
    if spec.id == "claude" and safe_config.claude_exec_enabled():
        return True
    return any(bool(os.environ.get(name, "").strip()) for name in spec.env_keys)


def _enabled(spec: ProviderSpec) -> bool:
    if spec.requires_external_adapters and not safe_config.external_adapters_enabled():
        return False
    if spec.id == "claude":
        return True
    return _configured(spec)


def _model(spec: ProviderSpec) -> str:
    if not spec.model_env:
        return spec.default_model
    return (os.environ.get(spec.model_env) or spec.default_model).strip()


def _ollama_host() -> str:
    raw = (os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").strip()
    if "://" not in raw:
        raw = "http://" + raw
    raw = raw.replace("0.0.0.0", "127.0.0.1")
    parsed = urllib.parse.urlparse(raw)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 11434
    return f"{host}:{port}"


def ollama_available(probe: bool = False, timeout: float = 0.2) -> bool | None:
    if not probe:
        return None
    host_port = _ollama_host()
    host, _, raw_port = host_port.partition(":")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        return None
    try:
        with socket.create_connection((host, int(raw_port or "11434")), timeout=timeout):
            return True
    except OSError:
        return False


def provider_status(spec: ProviderSpec, probe_ollama: bool = False) -> dict:
    health = provider_health.public_status(spec.id)
    out = {
        **asdict(spec),
        "enabled": _enabled(spec),
        "configured": _configured(spec),
        "model": _model(spec),
        "health_status": health["health_status"],
        "last_error_type": health["last_error_type"],
        "last_error_at": health["last_error_at"],
        "cooldown_until": health["cooldown_until"],
        "in_cooldown": health["in_cooldown"],
    }
    out.pop("env_keys", None)
    if spec.id == "ollama":
        out["host"] = _ollama_host()
        out["available"] = ollama_available(probe=probe_ollama)
    return out


def all_providers(probe_ollama: bool = False) -> list[dict]:
    return [provider_status(spec, probe_ollama=probe_ollama) for spec in PROVIDERS]


def get_spec(provider_id: str) -> ProviderSpec | None:
    return next((spec for spec in PROVIDERS if spec.id == provider_id), None)


def selected_provider_ids(mode: str | None = None, capability: str = "chat") -> list[str]:
    mode = (mode or safe_config.provider_mode()).strip().lower()
    if mode not in {"local", "cloud", "auto"}:
        mode = "auto"

    def supports(spec: ProviderSpec) -> bool:
        if capability == "tools":
            return spec.supports_tools
        if capability == "embeddings":
            return spec.supports_embeddings
        return spec.supports_chat

    specs = sorted(PROVIDERS, key=lambda item: item.priority)
    if mode == "local":
        specs = [spec for spec in specs if spec.type == LOCAL]
    elif mode == "cloud":
        specs = [spec for spec in specs if spec.type == CLOUD]
    else:
        specs = [spec for spec in specs if spec.type == LOCAL] + [spec for spec in specs if spec.type == CLOUD]

    out = []
    for spec in specs:
        if not supports(spec) or not _enabled(spec):
            continue
        if provider_health.is_in_cooldown(spec.id):
            continue
        out.append(spec.id)
    return out
