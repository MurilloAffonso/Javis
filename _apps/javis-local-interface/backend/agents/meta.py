"""Meta-agentes do Javis — camada de coordenação autônoma.

AIOS Master   — coordena squads, decide quais agentes usar para cada tarefa
Squad Creator — monta squads dinamicamente com base na demanda
Rootcause     — diagnostica falhas, aprende e melhora o sistema

Estes agentes operam sobre os outros agentes, dando ao Javis "vida própria".
"""
from __future__ import annotations
import json
import re
from .specialized import AGENT_REGISTRY, AgentMeta, BaseAgent, DEFAULT_MODEL, TIMEOUT


# ── AIOS Master ───────────────────────────────────────────

SYSTEM_AIOS = """\
Você é o AIOS Master do Javis — o coordenador supremo de agentes de Murillo Affonso.

Sua função: analisar cada tarefa e decidir qual squad montar para executá-la.

Retorne SOMENTE JSON válido (sem markdown):
{
  "squad": ["<lista de IDs de agentes>"],
  "rounds": <1 ou 2>,
  "plan": "<plano em 2-3 frases>",
  "deliverable": "<tipo: texto|codigo|dashboard|proposta|landing|script|planilha|relatorio>",
  "priority": "<alta|media|baixa>"
}

Agentes disponíveis:
- architect      → design de sistemas, estrutura
- developer      → código, implementação
- ux_designer    → interfaces, UX, fluxo visual
- qa             → testes, qualidade, validação
- pm             → planejamento, etapas, prazos
- po             → priorização, produto, MVP
- scrum          → gestão de tarefas, impedimentos
- analyst        → pesquisa, dados, estratégia
- devops         → deploy, infraestrutura
- data_engineer  → banco de dados, pipelines
- jarvis_soul    → tom, personalidade, síntese final

Regras:
- Máximo 5 agentes por squad
- jarvis_soul sempre por último se incluído
- rounds=2 apenas para tarefas complexas (projetos, sistemas completos)
- Para conversas simples: squad=["jarvis_soul"], rounds=1
"""


class AIOSMaster:
    """Coordena qual squad montar para cada tarefa."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def plan(self, task: str, context: str = "") -> dict:
        prompt = f"{context}\n\nTarefa: {task}" if context else task
        try:
            import claude_brain
            if not claude_brain.available():
                raise RuntimeError("Claude (assinatura) indisponível")
            content = claude_brain.answer(prompt, system=SYSTEM_AIOS, timeout=TIMEOUT)
            content = re.sub(r"```(?:json)?|```", "", (content or "").strip()).strip()
            return json.loads(content)
        except Exception:
            return {
                "squad":       ["jarvis_soul"],
                "rounds":      1,
                "plan":        task,
                "deliverable": "texto",
                "priority":    "media",
            }


# ── Squad Creator ─────────────────────────────────────────

class SquadCreator:
    """Monta e executa squads dinamicamente conforme plano do AIOS Master."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._aios = AIOSMaster(model=model)

    def create_and_run(self, task: str, memory_context: str = "") -> dict:
        plan = self._aios.plan(task, memory_context)

        squad_ids  = [a for a in plan.get("squad", []) if a in AGENT_REGISTRY]
        if not squad_ids:
            squad_ids = ["jarvis_soul"]

        rounds     = int(plan.get("rounds", 1))
        deliverable = plan.get("deliverable", "texto")

        from .squad import Squad
        sq = Squad(model=self.model)
        result = sq.run(task, squad_ids, rounds=rounds)

        result["aios_plan"]   = plan
        result["deliverable"] = deliverable
        return result


# ── Rootcause ─────────────────────────────────────────────

SYSTEM_ROOTCAUSE = """\
Você é o Rootcause do Javis — agente de diagnóstico e aprendizado.

Sua função: quando uma resposta falha ou é insatisfatória, investigar a causa raiz
e propor correções para o sistema não repetir o erro.

Analise:
1. O que foi pedido
2. O que foi entregue
3. Onde falhou (agente errado? contexto insuficiente? task mal formulada?)
4. Como corrigir nesta tentativa
5. O que memorizar para não repetir

Responda em português. Seja específico e cirúrgico.
"""


class Rootcause(BaseAgent):
    meta = AgentMeta(
        id="rootcause", name="Rootcause",
        role="Diagnóstico de falhas e aprendizado",
        icon="🔬", color="#ef4444",
    )
    meta_info = {
        "id":    "rootcause",
        "name":  "Rootcause",
        "role":  "Diagnóstico de falhas e aprendizado",
        "icon":  "🔬",
        "color": "#ef4444",
        "group": "meta",
    }
    system_prompt = SYSTEM_ROOTCAUSE

    def diagnose(self, task: str, failed_response: str, agents_used: list[str]) -> dict:
        prompt = (
            f"Tarefa original: {task}\n\n"
            f"Resposta que falhou:\n{failed_response}\n\n"
            f"Agentes usados: {', '.join(agents_used)}\n\n"
            "Diagnostique a causa raiz e proponha correção."
        )
        diagnosis = self.execute(prompt)

        # Salva o aprendizado na memória automaticamente
        try:
            from .memory_bridge import MemoryBridge
            mb = MemoryBridge()
            mb.save_lesson(task, diagnosis)
        except Exception:
            pass

        return {
            "task":       task,
            "agents":     agents_used,
            "diagnosis":  diagnosis,
            "learned":    True,
        }


# ── Info para o servidor ──────────────────────────────────

META_AGENTS_INFO = [
    {
        "id":    "aios_master",
        "name":  "AIOS Master",
        "role":  "Coordena a squad",
        "icon":  "🧬",
        "color": "#00e5ff",
        "group": "meta",
    },
    {
        "id":    "squad_creator",
        "name":  "Squad Creator",
        "role":  "Cria squads novas",
        "icon":  "⚡",
        "color": "#f59e0b",
        "group": "meta",
    },
    Rootcause.meta_info,
]
