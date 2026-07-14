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


def _night_kill_switch_active() -> bool:
    try:
        from execution.night_mode import KILL_SWITCH

        return KILL_SWITCH.exists()
    except Exception:
        return False


def _execution_stats() -> dict:
    """Fundação passiva do executor (R4.1). Só contagens/flags — nunca objetivo,
    stdout, stderr, diff ou paths sensíveis completos."""
    stats = {
        "execution_schema_present": False,
        "supervised_execution_enabled": safe_config.supervised_execution_enabled(),
        # R4.5 — Modo Madrugada: só flags, nunca o que ela rodou
        "night_mode_enabled": safe_config.night_mode_enabled(),
        "night_mode_kill_switch_active": _night_kill_switch_active(),
        "active_execution_tasks": 0,
        "active_worktrees": 0,
        "orphan_worktrees": 0,
        "worktree_root_configured": False,
        # R4.2A — filas de aprovação/review (só contagens)
        "awaiting_execution_approval": 0,
        "awaiting_merge_approval": 0,
        "awaiting_review": 0,
        "failed_execution_tasks": 0,
        # R4.2B — adapters presentes + estados do fluxo real (só contagens)
        "supervised_adapters_present": False,
        "executions_running": 0,
        "executions_testing": 0,
        "executions_timed_out": 0,
        "executions_awaiting_review": 0,
        # R4.2C1 — merge local controlado (só contagens)
        "approved_for_merge": 0,
        "merge_conflicts": 0,
        "completed_execution_tasks": 0,
        "preserved_worktrees": 0,
        # R4.2C2 — integração API/Command Center (só presença/contagens)
        "execution_api_present": False,
        "execution_command_center_present": False,
        "legacy_direct_execution_callers": 0,
        "supervised_tasks_total": 0,
        "pending_execution_approvals": 0,
        # R4.3B1 — fechamento da execução (só contagens; sem paths/hashes)
        "awaiting_review_without_commit": 0,
        "internal_prompt_artifacts": 0,
        "execution_commits_ready": 0,
    }
    try:
        from execution.executor_adapter import CodexAdapter, ClaudeCodeAdapter  # noqa: F401
        stats["supervised_adapters_present"] = True
    except Exception:
        pass
    try:
        from execution.execution_facade import ExecutionFacade  # noqa: F401
        stats["execution_api_present"] = True
    except Exception:
        pass
    try:
        stats["execution_command_center_present"] = (
            JAVIS_ROOT / "_apps" / "javis-local-interface" / "frontend" /
            "command-center" / "js" / "views" / "exec.js"
        ).exists()
        legacy_sources = [
            JAVIS_ROOT / "_apps" / "javis-local-interface" / "backend" / "orchestrator.py",
            JAVIS_ROOT / "_apps" / "javis-local-interface" / "backend" / "server.py",
        ]
        forbidden = ("brain_switch.dispatch", "code_agent.dispatch", "claude_exec.dispatch")
        stats["legacy_direct_execution_callers"] = sum(
            text.count(term)
            for path in legacy_sources if path.exists()
            for text in [path.read_text(encoding="utf-8", errors="ignore")]
            for term in forbidden
        )
    except Exception:
        pass
    try:
        from execution import worktree_manager as wm
        root = wm.WorktreeManager().worktree_root
        stats["worktree_root_configured"] = True
        disk_ids = {d.name for d in root.iterdir() if d.is_dir()} if root.exists() else set()
        stats["active_worktrees"] = len(disk_ids)
    except Exception:
        disk_ids = set()
    try:
        has_tbl = db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='execution_tasks'"
        )
        if has_tbl:
            stats["execution_schema_present"] = True
            import repositories as repo
            et = repo.execution_tasks
            stats["active_execution_tasks"] = et.count_active()
            # filas por estado (awaiting_merge_approval = já aprovado p/ merge,
            # aguardando o passo de merge, que chega na R4.2B)
            stats["awaiting_execution_approval"] = et.count_by_status("pending_approval")
            stats["awaiting_review"] = et.count_by_status("awaiting_review")
            stats["awaiting_merge_approval"] = et.count_by_status("approved_for_merge")
            stats["failed_execution_tasks"] = et.count_by_statuses(("failed", "timed_out"))
            stats["executions_running"] = et.count_by_status("running")
            stats["executions_testing"] = et.count_by_status("testing")
            stats["executions_timed_out"] = et.count_by_status("timed_out")
            stats["executions_awaiting_review"] = et.count_by_status("awaiting_review")
            stats["approved_for_merge"] = et.count_by_status("approved_for_merge")
            stats["merge_conflicts"] = db.count("execution_tasks", "last_error=?", ("merge_conflict",))
            stats["completed_execution_tasks"] = et.count_by_status("completed")
            stats["supervised_tasks_total"] = db.count("execution_tasks")
            stats["pending_execution_approvals"] = db.count(
                "approvals",
                "status=? AND action=?",
                ("pending", "execution.start"),
            )
            preserved = db.query(
                "SELECT task_id FROM execution_tasks "
                "WHERE status IN ('failed','timed_out','review_rejected') "
                "AND COALESCE(worktree_path,'')<>''"
            )
            stats["preserved_worktrees"] = len({r["task_id"] for r in preserved} & disk_ids)
            review_rows = db.query(
                "SELECT task_id, status, source_commit, worktree_path FROM execution_tasks "
                "WHERE status IN ('awaiting_review','approved_for_merge','completed')"
            )
            for row in review_rows:
                worktree_path = Path(row.get("worktree_path") or "")
                if not worktree_path.exists():
                    continue
                if (worktree_path / ".javes_execution_prompt.txt").exists():
                    stats["internal_prompt_artifacts"] += 1
                source_commit = (row.get("source_commit") or "").strip()
                if not source_commit:
                    if row.get("status") == "awaiting_review":
                        stats["awaiting_review_without_commit"] += 1
                    continue
                try:
                    head = subprocess.check_output(
                        ["git", "rev-parse", "HEAD"],
                        cwd=str(worktree_path),
                        text=True,
                        stderr=subprocess.DEVNULL,
                    ).strip()
                except Exception:
                    head = ""
                if head and head != source_commit:
                    stats["execution_commits_ready"] += 1
                elif row.get("status") == "awaiting_review":
                    stats["awaiting_review_without_commit"] += 1
            db_ids = {r["task_id"] for r in db.query("SELECT task_id FROM execution_tasks")}
            stats["orphan_worktrees"] = len(disk_ids - db_ids)
    except Exception:
        pass
    return stats


def snapshot(probe_ollama: bool = False) -> dict:
    sqlite_accessible = False
    pending_approvals = "indisponivel"
    session_stats = {
        "total_sessions": 0,
        "sessions_by_project": {},
        "javes_core_sessions": 0,
        "legacy_history_found": False,
        "session_project_inconsistencies": 0,
    }
    if db.DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(db.DB_PATH), timeout=2)
            try:
                pending_approvals = conn.execute(
                    "SELECT COUNT(*) FROM approvals WHERE status=?",
                    ("pending",),
                ).fetchone()[0]
                sqlite_accessible = True
                try:
                    has_sessions = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'"
                    ).fetchone()
                    if has_sessions:
                        rows = conn.execute(
                            "SELECT project_id, COUNT(*) FROM chat_sessions GROUP BY project_id"
                        ).fetchall()
                        sessions_by_project = {str(r[0]): int(r[1]) for r in rows}
                        session_stats = {
                            "total_sessions": sum(sessions_by_project.values()),
                            "sessions_by_project": sessions_by_project,
                            "javes_core_sessions": sessions_by_project.get(gate.CORE_SCOPE, 0),
                            "legacy_history_found": ((JAVIS_ROOT / "_apps" / "javis-local-interface" / "_data" / "chat_history.json").stat().st_size > 0)
                            if (JAVIS_ROOT / "_apps" / "javis-local-interface" / "_data" / "chat_history.json").exists() else False,
                            "session_project_inconsistencies": 0,
                        }
                except Exception:
                    pass
            finally:
                conn.close()
        except Exception:
            sqlite_accessible = False

    providers = provider_registry.all_providers(probe_ollama=probe_ollama)
    return {
        **_execution_stats(),
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
        **session_stats,
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
        f"- total_sessions: {data.get('total_sessions', 0)}",
        f"- javes_core_sessions: {data.get('javes_core_sessions', 0)}",
        f"- sessions_by_project: {data.get('sessions_by_project', {})}",
        f"- legacy_history_found: {data.get('legacy_history_found', False)}",
        f"- session_project_inconsistencies: {data.get('session_project_inconsistencies', 0)}",
        f"- supervised_execution_enabled: {data.get('supervised_execution_enabled', False)}",
        f"- night_mode_enabled: {data.get('night_mode_enabled', False)}",
        f"- night_mode_kill_switch_active: {data.get('night_mode_kill_switch_active', False)}",
        f"- execution_schema_present: {data.get('execution_schema_present', False)}",
        f"- active_execution_tasks: {data.get('active_execution_tasks', 0)}",
        f"- worktree_root_configured: {data.get('worktree_root_configured', False)}",
        f"- active_worktrees: {data.get('active_worktrees', 0)}",
        f"- orphan_worktrees: {data.get('orphan_worktrees', 0)}",
        f"- awaiting_execution_approval: {data.get('awaiting_execution_approval', 0)}",
        f"- awaiting_merge_approval: {data.get('awaiting_merge_approval', 0)}",
        f"- awaiting_review: {data.get('awaiting_review', 0)}",
        f"- failed_execution_tasks: {data.get('failed_execution_tasks', 0)}",
        f"- supervised_adapters_present: {data.get('supervised_adapters_present', False)}",
        f"- executions_running: {data.get('executions_running', 0)}",
        f"- executions_testing: {data.get('executions_testing', 0)}",
        f"- executions_timed_out: {data.get('executions_timed_out', 0)}",
        f"- executions_awaiting_review: {data.get('executions_awaiting_review', 0)}",
        f"- approved_for_merge: {data.get('approved_for_merge', 0)}",
        f"- merge_conflicts: {data.get('merge_conflicts', 0)}",
        f"- completed_execution_tasks: {data.get('completed_execution_tasks', 0)}",
        f"- preserved_worktrees: {data.get('preserved_worktrees', 0)}",
        f"- execution_api_present: {data.get('execution_api_present', False)}",
        f"- execution_command_center_present: {data.get('execution_command_center_present', False)}",
        f"- legacy_direct_execution_callers: {data.get('legacy_direct_execution_callers', 0)}",
        f"- supervised_tasks_total: {data.get('supervised_tasks_total', 0)}",
        f"- pending_execution_approvals: {data.get('pending_execution_approvals', 0)}",
        f"- awaiting_review_without_commit: {data.get('awaiting_review_without_commit', 0)}",
        f"- internal_prompt_artifacts: {data.get('internal_prompt_artifacts', 0)}",
        f"- execution_commits_ready: {data.get('execution_commits_ready', 0)}",
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
