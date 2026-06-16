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
  - escopo só na pasta do Javis (cwd + --add-dir)
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
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]

_TIMEOUT = int(os.environ.get("JAVIS_CLAUDE_EXEC_TIMEOUT", "900"))
_ALLOWED_TOOLS = ["Read", "Edit", "Write", "Bash"]
_SYSTEM_HINT = (
    "Você executa tarefas para Murillo no projeto Javis. Seja objetivo. "
    "NUNCA faça git commit/push, nem delete arquivos sem ser explicitamente pedido."
)

# Resolve o caminho completo em import-time: subprocess.run(["claude"]) falha no
# Windows quando o uvicorn não herda o PATH do shell (WinError 2). Usar o
# caminho absoluto resolve independente do ambiente de execução.
_CLAUDE_BIN: str | None = shutil.which("claude")


def available() -> bool:
    return _CLAUDE_BIN is not None


def _env() -> dict:
    """Ambiente do subprocesso SEM ANTHROPIC_API_KEY → força login por assinatura."""
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def run(task: str) -> str:
    """Executa a tarefa no Claude Code headless (assinatura) e retorna a saída."""
    task = (task or "").strip()
    if not task:
        return "O que devo executar, senhor?"
    if not available():
        return ("O Claude Code não está instalado, senhor. Instale e faça login na "
                "assinatura para eu executar tarefas por aqui.")
    cmd = [
        _CLAUDE_BIN, "-p", task,
        "--output-format", "text",
        "--permission-mode", "acceptEdits",
        "--allowedTools", *_ALLOWED_TOOLS,
        "--add-dir", str(JAVIS_ROOT),
        "--append-system-prompt", _SYSTEM_HINT,
    ]
    try:
        proc = subprocess.run(
            cmd, cwd=str(JAVIS_ROOT), env=_env(),
            capture_output=True, text=True, timeout=_TIMEOUT,
        )
        out = (proc.stdout or "").strip()
        if not out:
            err = (proc.stderr or "").strip()
            return f"Executei, mas sem saída de texto, senhor.{(' Detalhe: ' + err[-300:]) if err else ''}"
        return out
    except subprocess.TimeoutExpired:
        return f"A tarefa passou de {_TIMEOUT // 60} min e foi interrompida, senhor: {task}"
    except Exception as e:
        return f"Falhei ao executar via Claude, senhor: {e}"


def _run_bg(task: str) -> None:
    """Roda em background e enfileira o resultado como notificação."""
    out = run(task)
    msg = f"Terminei de executar, senhor: {task}\n{out[-500:]}"
    try:
        import reminders
        reminders._due_queue.append({"text": msg[:600]})
        reminders._notify_telegram(msg[:600])
    except Exception:
        pass


def dispatch(task: str) -> str:
    """Inicia a tarefa em background (execução demora) e confirma na hora."""
    task = (task or "").strip()
    if not task:
        return "O que devo executar, senhor?"
    if not available():
        return ("O Claude Code não está instalado/logado, senhor. Sem ele, eu uso o "
                "Codex como reserva para programar.")
    threading.Thread(target=_run_bg, args=(task,), daemon=True).start()
    return f"Já comecei a executar isso pela assinatura do Claude, senhor: {task}. Te aviso ao terminar."
