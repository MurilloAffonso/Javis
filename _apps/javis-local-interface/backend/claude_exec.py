"""Claude Exec — motor de EXECUÇÃO do Jamba via ASSINATURA do Claude (Claude Code).

O Jamba delega tarefas de execução ("programa X", "cria Y", tarefas multi-step)
para o Claude Code headless (`claude -p`), que roda pela ASSINATURA do Murillo —
sem gastar token da API Anthropic (que está sem crédito).

Modelo de custo (igual ao projeto de referência):
  Execução  → assinatura Claude (flat)   ← ESTE módulo
  Voz/chat  → créditos OpenAI

Segurança (allowlist segura):
  - allowedTools: Read, Edit, Write, Bash (edita/cria/roda testes)
  - permission-mode acceptEdits (auto-aceita edições, headless)
  - escopo padrão na pasta do Javis, mas aceita qualquer pasta via parâmetro
  - hook PreToolUse em .claude/settings.json BLOQUEIA git push/reset/clean, rm -rf, sudo
  - SEM commit automático (regra do CLAUDE.md)

CRÍTICO: o subprocesso roda com ANTHROPIC_API_KEY REMOVIDA do ambiente, senão o
Claude Code tentaria usar a API (sem crédito) em vez da assinatura.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import threading
import time as _time
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]

_TIMEOUT = int(os.environ.get("JAVIS_CLAUDE_EXEC_TIMEOUT", "900"))
_ALLOWED_TOOLS = ["Read", "Edit", "Write", "Bash"]
_SYSTEM_HINT = (
    "Você executa tarefas para Murillo. Tem acesso a QUALQUER pasta do computador dele. "
    "Seja objetivo. "
    "NUNCA faça git commit/push, nem delete arquivos sem ser explicitamente pedido."
)

_CLAUDE_BIN: str | None = shutil.which("claude")

# Estado global visível ao /exec/status (thread-safe via _exec_lock)
_exec_lock = threading.Lock()
_exec_state: dict = {
    "running": False, "task": "", "pasta": None,
    "started_at": None, "exit_code": None, "lines": [],
}


def available() -> bool:
    return _CLAUDE_BIN is not None


def get_status() -> dict:
    """Retorna cópia do estado atual da execução (para o endpoint /exec/status)."""
    with _exec_lock:
        s = dict(_exec_state)
        s["lines"] = list(s["lines"])
    return s


def _env() -> dict:
    """Ambiente do subprocesso SEM ANTHROPIC_API_KEY → força login por assinatura."""
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def run(task: str, pasta: str | None = None) -> str:
    """Executa a tarefa via Popen, streamando linhas para _exec_state em tempo real."""
    task = (task or "").strip()
    if not task:
        return "O que devo executar, senhor?"
    if not available():
        return ("O Claude Code não está instalado, senhor. Instale e faça login na "
                "assinatura para eu executar tarefas por aqui.")
    work_dir = Path(pasta) if pasta else JAVIS_ROOT
    if not work_dir.is_dir():
        return f"A pasta '{pasta}' não existe, senhor."
    cmd = [
        _CLAUDE_BIN, "-p", task,
        "--output-format", "text",
        "--permission-mode", "acceptEdits",
        "--allowedTools", *_ALLOWED_TOOLS,
        "--add-dir", str(work_dir),
        "--append-system-prompt", _SYSTEM_HINT,
    ]
    if work_dir != JAVIS_ROOT:
        cmd += ["--add-dir", str(JAVIS_ROOT)]

    with _exec_lock:
        _exec_state.update({
            "running": True, "task": task, "pasta": str(work_dir),
            "started_at": _time.time(), "exit_code": None, "lines": [],
        })

    exit_code = -1
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(work_dir), env=_env(),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        # Stream linha a linha → _exec_state visível ao /exec/status em tempo real
        for raw in proc.stdout:
            line = raw.rstrip()
            with _exec_lock:
                _exec_state["lines"].append(line)
                if len(_exec_state["lines"]) > 500:
                    _exec_state["lines"] = _exec_state["lines"][-500:]
        proc.wait(timeout=_TIMEOUT)
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        with _exec_lock:
            _exec_state["lines"].append(f"[TIMEOUT após {_TIMEOUT // 60} min]")
    except Exception as e:
        with _exec_lock:
            _exec_state["lines"].append(f"[ERRO: {e}]")
    finally:
        with _exec_lock:
            _exec_state["running"] = False
            _exec_state["exit_code"] = exit_code

    with _exec_lock:
        all_lines = list(_exec_state["lines"])
    out = "\n".join(all_lines).strip()
    return out or "Executei, mas sem saída de texto, senhor."


def _run_bg(task: str, pasta: str | None = None) -> None:
    """Roda em background e enfileira o resultado como notificação."""
    out = run(task, pasta=pasta)
    msg = f"Terminei de executar, senhor: {task}\n{out[-500:]}"
    try:
        import reminders
        reminders._due_queue.append({"text": msg[:600]})
        reminders._notify_telegram(msg[:600])
    except Exception:
        pass


def audit(pasta: str | None = None) -> str:
    """Vistoria rápida (30s) após Codex — valida estrutura e padrões."""
    work_dir = Path(pasta) if pasta else JAVIS_ROOT
    if not work_dir.is_dir():
        return ""
    cmd = [
        _CLAUDE_BIN, "-p",
        "Faz audit rápido dos arquivos modificados (ls -la | tail -20). Mostra: (1) arquivos novo/alterado, (2) se código segue padrão básico. SEM detalhes, max 3 linhas.",
        "--output-format", "text",
        "--permission-mode", "acceptEdits",
        "--allowedTools", "Read", "Bash",
        "--add-dir", str(work_dir),
    ]
    try:
        proc = subprocess.run(
            cmd, cwd=str(work_dir), env=_env(),
            capture_output=True, text=True, timeout=35,
        )
        return (proc.stdout or "").strip()[:200]
    except Exception:
        return ""


def dispatch(task: str, pasta: str | None = None) -> str:
    """Inicia a tarefa em background (execução demora) e confirma na hora."""
    task = (task or "").strip()
    if not task:
        return "O que devo executar, senhor?"
    if not available():
        return ("O Claude Code não está instalado/logado, senhor. Sem ele, eu uso o "
                "Codex como reserva para programar.")
    threading.Thread(target=_run_bg, args=(task, pasta), daemon=True).start()
    return f"Já comecei a executar isso pela assinatura do Claude, senhor: {task}. Te aviso ao terminar."
