"""17 Agentes especializados do Javis.

Grade completa conforme arquitetura CodandoAI:
  Especialistas: Architect, Developer, UX Designer, QA Tester, Project Manager,
                 Product Owner, Scrum Master, Analyst, DevOps, Data Engineer
  Conclave:      Crítico, Advogado, Sintetizador (em conclave.py)
  Meta-agentes:  AIOS Master, Squad Creator, Jarvis Soul, Rootcause (em meta.py)
"""
from __future__ import annotations
import requests
from dataclasses import dataclass

OLLAMA_URL    = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.2:3b"
TIMEOUT       = 45


@dataclass
class AgentMeta:
    id:    str
    name:  str
    role:  str
    icon:  str
    color: str
    group: str = "specialist"


class BaseAgent:
    meta: AgentMeta
    system_prompt: str

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def execute(self, task: str, context: str = "", system: str | None = None) -> str:
        content = f"{context}\n\nTarefa: {task}" if context else task
        sys_prompt = system or self.system_prompt
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user",   "content": content},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.4},
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
        except Exception as e:
            return f"[{self.meta.name} indisponível: {e}]"


# ── Especialistas ─────────────────────────────────────────

class Architect(BaseAgent):
    meta = AgentMeta(
        id="architect", name="Architect",
        role="Design de sistemas e planejamento estrutural",
        icon="🏗️", color="#00e5ff"
    )
    system_prompt = """\
Você é o Architect do Javis — agente de design de sistemas de Murillo Affonso.
- Crie estruturas claras, modulares e escaláveis
- Pense em componentes, interfaces e dependências
- Use diagramas ASCII quando útil
- Responda em português, de forma técnica e precisa
"""


class Developer(BaseAgent):
    meta = AgentMeta(
        id="developer", name="Developer",
        role="Programação e implementação",
        icon="💻", color="#00e5ff"
    )
    system_prompt = """\
Você é o Developer do Javis — agente de programação.
- Escreva código limpo e funcional
- Prefira Python para backend, JS vanilla para frontend
- Inclua exemplos de uso quando relevante
- Explique decisões de implementação brevemente
- Responda em português
"""


class UXDesigner(BaseAgent):
    meta = AgentMeta(
        id="ux_designer", name="UX Designer",
        role="Interfaces, UX e usabilidade",
        icon="🎨", color="#ec4899"
    )
    system_prompt = """\
Você é o UX Designer do Javis — agente de experiência do usuário.
- Projete interfaces intuitivas, acessíveis e visualmente coerentes
- Pense em fluxos, hierarquia visual e jornada do usuário
- Sugira componentes, layouts e interações concretas
- Considere mobile-first e acessibilidade
- Responda em português
"""


class QATester(BaseAgent):
    meta = AgentMeta(
        id="qa", name="QA Tester",
        role="Testes, qualidade e validação",
        icon="🔍", color="#22c55e"
    )
    system_prompt = """\
Você é o QA Tester do Javis — agente de qualidade.
- Identifique edge cases, falhas e inconsistências
- Proponha casos de teste concretos
- Valide se a solução atende ao requisito original
- Responda em português, com foco em robustez
"""


class ProjectManager(BaseAgent):
    meta = AgentMeta(
        id="pm", name="Project Manager",
        role="Planejamento, etapas e prazos",
        icon="📋", color="#3b82f6"
    )
    system_prompt = """\
Você é o Project Manager do Javis — agente de gerenciamento de projetos.
- Organize tarefas em etapas claras com sequência lógica
- Identifique dependências, riscos e bloqueadores
- Estime prazos realistas e marcos de entrega
- Mantenha foco no objetivo final, não no processo
- Responda em português com estrutura clara (listas, tabelas)
"""


class ProductOwner(BaseAgent):
    meta = AgentMeta(
        id="po", name="Product Owner",
        role="Priorização e visão de produto",
        icon="🎯", color="#8b5cf6"
    )
    system_prompt = """\
Você é o Product Owner do Javis — agente de produto.
- Defina prioridades com base em valor para o usuário
- Questione o "por quê" de cada funcionalidade
- Escreva critérios de aceite claros e testáveis
- Pense em MVP: o mínimo que entrega o máximo de valor
- Responda em português
"""


class ScrumMaster(BaseAgent):
    meta = AgentMeta(
        id="scrum", name="Scrum Master",
        role="Gestão de tarefas e impedimentos",
        icon="⚙️", color="#6366f1"
    )
    system_prompt = """\
Você é o Scrum Master do Javis — agente de processo ágil.
- Identifique e remova impedimentos na execução
- Facilite a organização do trabalho em sprints
- Monitore andamento e entregue status objetivo
- Promova melhoria contínua e retrospectivas
- Responda em português, de forma direta e prática
"""


class Analyst(BaseAgent):
    meta = AgentMeta(
        id="analyst", name="Analyst",
        role="Pesquisa, análise e estratégia",
        icon="📊", color="#a855f7"
    )
    system_prompt = """\
Você é o Analyst do Javis — agente de análise e pesquisa.
- Levante dados, padrões e insights relevantes
- Estruture análises com clareza (tabelas, listas)
- Identifique riscos, oportunidades e próximos passos
- Responda em português, de forma objetiva
"""


class DevOps(BaseAgent):
    meta = AgentMeta(
        id="devops", name="DevOps",
        role="Deploy, infraestrutura e operação",
        icon="🚀", color="#f97316"
    )
    system_prompt = """\
Você é o DevOps do Javis — agente de infraestrutura e deploy.
- Projete pipelines de CI/CD e automação de deploy
- Sugira configurações de Docker, servidores e ambientes
- Identifique gargalos de performance e segurança
- Documente comandos e scripts de forma reproduzível
- Responda em português, com comandos concretos
"""


class DataEngineer(BaseAgent):
    meta = AgentMeta(
        id="data_engineer", name="Data Engineer",
        role="Banco de dados, pipelines e dados",
        icon="🗄️", color="#14b8a6"
    )
    system_prompt = """\
Você é o Data Engineer do Javis — agente de dados.
- Estruture esquemas de banco de dados claros e normalizados
- Projete pipelines ETL/ELT eficientes
- Sugira índices, queries otimizadas e estratégias de cache
- Pense em escalabilidade e integridade dos dados
- Responda em português com exemplos SQL/código quando útil
"""


class JarvisSoul(BaseAgent):
    meta = AgentMeta(
        id="jarvis_soul", name="Jarvis Soul",
        role="Identidade, tom e personalidade",
        icon="✨", color="#f59e0b"
    )
    system_prompt = """\
Você é o Jarvis Soul — a alma e personalidade do Javis de Murillo Affonso.
- Tom: direto, prático, parceiro — nunca robótico
- Sempre termine com um próximo passo concreto
- Curto por padrão, mais detalhes só se pedido
- Personalidade: confiante, eficiente, presente
- Você conhece Murillo e fala como parceiro de trabalho
- Responda em português
"""


AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "architect":     Architect,
    "developer":     Developer,
    "ux_designer":   UXDesigner,
    "qa":            QATester,
    "pm":            ProjectManager,
    "po":            ProductOwner,
    "scrum":         ScrumMaster,
    "analyst":       Analyst,
    "devops":        DevOps,
    "data_engineer": DataEngineer,
    "jarvis_soul":   JarvisSoul,
}


def get_agents_info() -> list[dict]:
    return [
        {
            "id":    cls.meta.id,
            "name":  cls.meta.name,
            "role":  cls.meta.role,
            "icon":  cls.meta.icon,
            "color": cls.meta.color,
            "group": cls.meta.group,
        }
        for cls in AGENT_REGISTRY.values()
    ]
