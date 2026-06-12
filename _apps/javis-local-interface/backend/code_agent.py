"""Code Agent — dispara tarefas de programação pro Codex CLI dentro do projeto.

O Jamba delega "programa X" pro `codex exec`, que escreve código no projeto.
Roda em segundo plano (codar demora) e avisa quando termina (fila de lembretes/Telegram).

Requer o Codex CLI instalado:  npm install -g @openai/codex
"""
from __future__ import annotations
import os
import shutil
import subprocess
import threading
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]


def available() -> bool:
    return shutil.which("codex") is not None


def _run(task: str) -> None:
    """Executa o Codex e enfileira o resultado como notificação."""
    try:
        proc = subprocess.run(
            ["codex", "exec", task],
            cwd=str(JAVIS_ROOT),
            capture_output=True, text=True, timeout=900,
        )
        out = (proc.stdout or "").strip()
        tail = out[-500:] if out else (proc.stderr or "").strip()[-500:]
        msg = f"Terminei de programar, senhor: {task}\n{tail}" if tail else f"Terminei: {task}"
    except subprocess.TimeoutExpired:
        msg = f"A tarefa de código passou de 15 min e foi interrompida, senhor: {task}"
    except Exception as e:
        msg = f"Falhei ao programar, senhor: {e}"

    # Notifica pela fila de lembretes (interface fala) e Telegram
    try:
        import reminders
        reminders._due_queue.append({"text": msg[:600]})
        reminders._notify_telegram(msg[:600])
    except Exception:
        pass


def dispatch(task: str) -> str:
    """Inicia uma tarefa de programação em segundo plano. Retorna confirmação imediata."""
    task = (task or "").strip()
    if not task:
        return "O que devo programar, senhor?"
    if not available():
        return ("O Codex não está instalado, senhor. Instale com: npm install -g @openai/codex "
                "e faça login. Aí eu programo direto no projeto por comando.")
    threading.Thread(target=_run, args=(task,), daemon=True).start()
    return f"Já comecei a programar isso, senhor: {task}. Te aviso quando terminar."
