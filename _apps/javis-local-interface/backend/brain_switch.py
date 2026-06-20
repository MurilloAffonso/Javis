"""brain_switch.py — qual assinatura executa as tarefas de programação: Claude ou Codex.

Murillo tem duas assinaturas (Claude Code + ChatGPT/Codex). Em vez de uma ordem
fixa de fallback, ele escolhe manualmente qual roda agora — e troca quando a
cota de uma acabar. Estado persistido em `_estado/brain_ativo.json` (sobrevive
a restart do servidor).
"""
from __future__ import annotations
import json
from pathlib import Path

JAVIS_ROOT  = Path(__file__).resolve().parents[3]
_STATE_FILE = JAVIS_ROOT / "_estado" / "brain_ativo.json"
_VALID = ("claude", "codex")
_DEFAULT = "claude"


def get_active() -> str:
    try:
        data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        engine = data.get("engine")
        if engine in _VALID:
            return engine
    except Exception:
        pass
    return _DEFAULT


def set_active(engine: str) -> str:
    engine = (engine or "").strip().lower()
    if engine not in _VALID:
        raise ValueError(f"engine deve ser um de {_VALID}, recebido: {engine!r}")
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps({"engine": engine}, ensure_ascii=False), encoding="utf-8")
    return engine


def dispatch(task: str):
    """Despacha a tarefa de programação pro motor ativo (com fallback pro outro)."""
    import claude_exec
    import code_agent

    engine = get_active()
    primary, fallback = (claude_exec, code_agent) if engine == "claude" else (code_agent, claude_exec)

    if primary.available():
        return primary.dispatch(task)
    if fallback.available():
        return fallback.dispatch(task)
    return "Nem Claude Code nem Codex estão disponíveis agora, senhor."
