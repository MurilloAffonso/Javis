"""agent_runner.py — executa UM agente com skill + RAG + cérebro forte.

Fatia vertical do "treinamento por skills": em vez de fine-tuning, um agente
ganha capacidade ao (1) carregar a própria SKILL.md, (2) puxar contexto real do
RAG do projeto, e (3) raciocinar no Claude (assinatura) em vez do llama fraco.

Prova de conceito com o Architect. Os ids batem com agents/specialized.py e com
o frontend, então escala pros outros 16 só adicionando `_skills/agente-<id>.md`.
"""
from __future__ import annotations
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = JAVIS_ROOT / "_skills"


def _load_skill(agent_id: str) -> str:
    """Carrega a skill do agente (_skills/agente-<id>.md), sem o frontmatter YAML."""
    path = SKILLS_DIR / f"agente-{agent_id}.md"
    if not path.is_file():
        return ""
    txt = path.read_text(encoding="utf-8", errors="ignore")
    # remove o bloco de frontmatter --- ... --- do topo, se houver
    if txt.startswith("---"):
        parts = txt.split("---", 2)
        if len(parts) == 3:
            txt = parts[2]
    return txt.strip()


# Conclave/meta não estão em AGENT_REGISTRY (vivem em meta.py/conclave.py) —
# mapeados aqui pra fechar o gap sem duplicar persona.
_EXTRA_PERSONAS = {
    "aios_master":   ("AIOS Master", "Coordena a squad"),
    "squad_creator": ("Squad Creator", "Cria squads novas"),
    "rootcause":     ("Rootcause", "Diagnóstico de falhas e aprendizado"),
    "critico":       ("Conclave Crítico", "Audita lógica e falhas"),
    "advogado":       ("Conclave Advogado", "Ataca o plano e expõe riscos"),
    "sintetizador":  ("Conclave Sintetizador", "Integra a melhor solução"),
}


def _persona(agent_id: str) -> tuple[str, str, str]:
    """Retorna (nome, papel, system_prompt base) do agente, do registro do backend."""
    try:
        from agents.specialized import AGENT_REGISTRY
        cls = AGENT_REGISTRY.get(agent_id)
        if cls:
            return cls.meta.name, cls.meta.role, cls.system_prompt
    except Exception:
        pass
    try:
        from agents.meta import Rootcause
        if agent_id == "rootcause":
            return Rootcause.meta.name, Rootcause.meta.role, Rootcause.system_prompt
    except Exception:
        pass
    if agent_id in _EXTRA_PERSONAS:
        name, role = _EXTRA_PERSONAS[agent_id]
        return name, role, ""
    return agent_id, "", ""


def _compose_system(agent_id: str) -> tuple[str, str, bool]:
    """Monta o system prompt do agente. FONTE ÚNICA: se há skill .md, ela manda
    (a persona do Python NÃO entra, pra não duplicar). Sem skill, usa a persona
    do Python como fallback. Retorna (system, nome, usou_skill)."""
    name, role, base_prompt = _persona(agent_id)
    skill = _load_skill(agent_id)
    if skill:
        header = f"Você é o {name} do Javis — {role}. Siga à risca a skill abaixo."
        return f"{header}\n\n{skill}", name, True
    fallback = base_prompt.strip() or f"Você é o {name} do Javis — {role}. Responda em português do Brasil."
    return fallback, name, False


def run_agent(agent_id: str, task: str) -> dict:
    """Roda o agente na tarefa. Skill + RAG + Claude (fallback Ollama)."""
    task = (task or "").strip()
    if not task:
        return {"status": "error", "message": "Tarefa vazia."}

    # System prompt = fonte única (skill .md manda; sem skill, persona do Python)
    system, name, used_skill = _compose_system(agent_id)

    # 1) Contexto real do projeto (RAG)
    rag = ""
    try:
        import knowledge
        rag = knowledge.answer_context(task, k=5)
    except Exception:
        rag = ""

    # 3) Raciocínio em cérebro forte, com 3 níveis de fallback:
    #    Claude (assinatura, grátis) → OpenAI gpt-4o (forte, confiável) → Ollama (local).
    brain = "claude"
    result = ""
    try:
        import claude_brain
        if claude_brain.available():
            result = claude_brain.answer(task, context=rag, system=system, timeout=180)
    except Exception:
        result = ""

    if not result.strip():
        brain = "openai"
        try:
            from llm_providers import call_openai
            user = task if not rag else f"Contexto do projeto:\n{rag}\n\nTarefa: {task}"
            result = call_openai(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.3,
            )
        except Exception:
            result = ""

    if not result.strip():
        brain = "ollama"
        try:
            from agents.specialized import AGENT_REGISTRY
            cls = AGENT_REGISTRY.get(agent_id)
            if cls:
                result = cls().execute(task, context=rag, system=system)
        except Exception as e:
            return {"status": "error", "message": f"Falha ao executar: {e}"}

    return {
        "status":    "ok",
        "agent":     agent_id,
        "name":      name,
        "brain":     brain,
        "used_skill": used_skill,
        "used_rag":   bool(rag),
        "result":    (result or "").strip(),
    }
