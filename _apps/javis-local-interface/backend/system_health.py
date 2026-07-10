"""Shared read-only health snapshot for status, doctor and future UI."""
from __future__ import annotations

from pathlib import Path
import os
import sqlite3
import subprocess
import sys

import db
import gate
import provider_registry
import safe_config


JAVIS_ROOT = Path(__file__).resolve().parents[3]


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=str(JAVIS_ROOT), text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def snapshot(probe_ollama: bool = False) -> dict:
    sqlite_accessible = False
    pending_approvals = "indisponivel"
    if db.DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(db.DB_PATH), timeout=2)
            try:
                pending_approvals = conn.execute(
                    "SELECT COUNT(*) FROM approvals WHERE status=?",
                    ("pending",),
                ).fetchone()[0]
                sqlite_accessible = True
            finally:
                conn.close()
        except Exception:
            sqlite_accessible = False

    providers = provider_registry.all_providers(probe_ollama=probe_ollama)
    return {
        "branch": _git(["branch", "--show-current"]) or "unknown",
        "git_status": _git(["status", "--short", "--branch"]),
        "python": sys.version.split()[0],
        "sqlite_accessible": sqlite_accessible,
        "provider_mode": safe_config.provider_mode(),
        "rag_embedder": (os.environ.get("JAVIS_RAG_EMBEDDER") or "ollama").strip().lower() or "ollama",
        "providers": providers,
        "providers_registered": [item["id"] for item in providers],
        "providers_enabled": [item["id"] for item in providers if item["enabled"]],
        "providers_healthy": [item["id"] for item in providers if item["health_status"] == "healthy" and not item["in_cooldown"]],
        "providers_cooldown": [item["id"] for item in providers if item["in_cooldown"]],
        "local_token_configured": bool(gate._configured_local_token()),
        "external_adapters": safe_config.external_adapters_enabled(),
        "local_actions": safe_config.local_actions_enabled(),
        "vp_effects": safe_config.vp_effects_enabled(),
        "codex_exec": safe_config.codex_exec_enabled(),
        "claude_headless": safe_config.claude_exec_enabled(),
        "browser": safe_config.browser_enabled(),
        "telegram": safe_config.telegram_enabled(),
        "mcp": safe_config.mcp_enabled(),
        "current_state_present": (JAVIS_ROOT / "_estado" / "CURRENT_STATE.md").exists(),
        "rag_index_present": (JAVIS_ROOT / "_memoria" / "knowledge_index.json").exists(),
        "pending_approvals": pending_approvals,
        "default_project_id": gate.CORE_SCOPE,
    }


def render_text(data: dict) -> str:
    lines = [
        "Javes doctor",
        f"- branch: {data['branch']}",
        f"- git_status: {data['git_status'].splitlines()[0] if data.get('git_status') else 'unknown'}",
        f"- python: {data['python']}",
        f"- sqlite_accessible: {data['sqlite_accessible']}",
        f"- provider_mode: {data['provider_mode']}",
        f"- rag_embedder: {data['rag_embedder']}",
        f"- local_token_configured: {'sim' if data['local_token_configured'] else 'nao'}",
        f"- external_adapters: {data['external_adapters']}",
        f"- local_actions: {data['local_actions']}",
        f"- vp_effects: {data['vp_effects']}",
        f"- codex_exec: {data['codex_exec']}",
        f"- claude_headless: {data['claude_headless']}",
        f"- browser: {data['browser']}",
        f"- telegram: {data['telegram']}",
        f"- mcp: {data['mcp']}",
        f"- CURRENT_STATE.md: {data['current_state_present']}",
        f"- rag_index: {data['rag_index_present']}",
        f"- pending_approvals: {data['pending_approvals']}",
        f"- default_project_id: {data['default_project_id']}",
        "- providers:",
    ]
    for item in data["providers"]:
        extra = ""
        if item["id"] == "ollama":
            available = item.get("available")
            extra = f", available={available}" if available is not None else ", available=not_probed"
        lines.append(
            f"  - {item['id']}: type={item['type']}, enabled={item['enabled']}, "
            f"configured={item['configured']}, health={item['health_status']}, "
            f"cooldown={item['in_cooldown']}, last_error={item['last_error_type'] or 'none'}, "
            f"model={item['model']}{extra}"
        )
    return "\n".join(lines)
