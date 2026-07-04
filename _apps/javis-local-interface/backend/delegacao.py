"""delegacao.py — política de delegação automática Claude → Codex.

Detecta tarefas de execução pura (programar, refatorar, rodar) e as roteia pro
Codex sem classificação LLM (economia). Tarefas ambíguas caem numa rota leve no
orchestrator. Sempre injeta preâmbulo de guarda: sem git commit/push.
"""
import re
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]

# Lista de verbos inequívocos de execução (conservadora, pra minimizar falso-positivo)
EXEC_VERBS = [
    "programa", "programar", "implementa", "implementar",
    "refatora", "refatorar",
    "roda", "rodar", "executa", "executar",
    "cria", "criar", "gera", "gerar",
    "corrige", "corrigir", "fix", "fixa", "fixar",
    "testa", "testar",
    "debug", "debugar",
]

# Regex: verbo no início ou após alguns caracteres, case-insensitive
_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(v) for v in EXEC_VERBS) + r')\b',
    re.IGNORECASE
)


def enabled() -> bool:
    """Retorna True se JAVIS_AUTO_CODEX está ligado (default False)."""
    import os
    return os.environ.get("JAVIS_AUTO_CODEX", "").lower() in ("1", "true", "yes", "on")


def should_delegate(texto: str) -> bool:
    """Detecta se a tarefa é execução pura (verbo inequívoco) → delega pro Codex."""
    texto = (texto or "").strip()
    if not texto:
        return False
    return bool(_PATTERN.search(texto))


def montar_brief(texto: str, plano: str = "") -> str:
    """Monta o objetivo + preâmbulo de guarda pro Codex.

    Preâmbulo: "não faça git commit nem push; deixe no working tree"
    (honra o CLAUDE.md: commit/push continuam manuais).
    """
    brief_parts = [
        "⚠️ GUARDRAILS:",
        "- Não faça `git commit` nem `git push` — deixe as mudanças no working tree para revisão.",
        "- Trabalhe na pasta do projeto (raiz: " + str(JAVIS_ROOT) + ").",
        "",
        "TAREFA:",
        texto,
    ]
    if plano:
        brief_parts.insert(5, "")
        brief_parts.insert(6, "CONTEXTO (do planejamento):")
        brief_parts.insert(7, plano)
    return "\n".join(brief_parts)
