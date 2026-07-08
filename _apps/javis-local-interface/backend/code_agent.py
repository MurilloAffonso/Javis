"""Code Agent — dispara tarefas via Codex CLI com streaming em tempo real.

O Jamba delega "programa X" pro `codex exec`, mostra saída linha a linha na aba Execução.
Compartilha _exec_state com claude_exec pra unificar visualização.
"""
from __future__ import annotations
import shutil
import subprocess
import threading
import time as _time
from pathlib import Path

import safe_config

JAVIS_ROOT = Path(__file__).resolve().parents[3]


def available() -> bool:
    return safe_config.codex_exec_enabled() and shutil.which("codex") is not None


def _run(task: str, pasta: str | None = None) -> None:
    """Codex com streaming linha a linha pra _exec_state (compartilhado com claude_exec)."""
    import claude_exec  # acessa _exec_state global

    if not safe_config.codex_exec_enabled():
        with claude_exec._exec_lock:
            claude_exec._exec_state.update({
                "running": False, "task": task, "pasta": pasta,
                "started_at": None, "exit_code": None,
                "lines": [safe_config.disabled_message(
                    "codex_exec",
                    f"{safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS}+{safe_config.JAVIS_ENABLE_CODEX_EXEC}",
                )],
            })
        return

    work_dir = Path(pasta) if pasta else JAVIS_ROOT
    if not work_dir.is_dir():
        return

    with claude_exec._exec_lock:
        claude_exec._exec_state.update({
            "running": True, "task": task, "pasta": str(work_dir),
            "started_at": _time.time(), "exit_code": None, "lines": [],
        })

    exit_code = -1
    try:
        proc = subprocess.Popen(
            ["codex", "exec", task],
            cwd=str(work_dir),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        for raw in proc.stdout:
            line = raw.rstrip()
            with claude_exec._exec_lock:
                claude_exec._exec_state["lines"].append(line)
                if len(claude_exec._exec_state["lines"]) > 500:
                    claude_exec._exec_state["lines"] = claude_exec._exec_state["lines"][-500:]
        proc.wait(timeout=900)
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        with claude_exec._exec_lock:
            claude_exec._exec_state["lines"].append("[TIMEOUT após 15 min]")
    except Exception as e:
        with claude_exec._exec_lock:
            claude_exec._exec_state["lines"].append(f"[ERRO: {e}]")
    finally:
        with claude_exec._exec_lock:
            claude_exec._exec_state["running"] = False
            claude_exec._exec_state["exit_code"] = exit_code

    # Notificação
    with claude_exec._exec_lock:
        all_lines = list(claude_exec._exec_state["lines"])
    out = "\n".join(all_lines[-50:]).strip()

    try:
        import reminders
        msg = f"Codex terminou: {task}\n{out[-400:]}"
        reminders._due_queue.append({"text": msg[:600]})
        reminders._notify_telegram(msg[:600])
    except Exception:
        pass


def dispatch(task: str, pasta: str | None = None) -> str:
    """Inicia Codex em background com streaming em tempo real."""
    task = (task or "").strip()
    if not task:
        return "O que devo programar, senhor?"
    if not safe_config.codex_exec_enabled():
        return safe_config.disabled_message(
            "codex_exec",
            f"{safe_config.JAVIS_ENABLE_EXTERNAL_ADAPTERS}+{safe_config.JAVIS_ENABLE_CODEX_EXEC}",
        )
    if not available():
        return ("Codex não está instalado. Instale: npm install -g @openai/codex "
                "e faça login com: codex login")
    threading.Thread(target=_run, args=(task, pasta), daemon=True).start()
    return f"Codex rodando: {task}. Veja na aba Execução em tempo real."
