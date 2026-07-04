"""Orchestrator — roteamento por LLM com multi-brain e squad autônomo.

Flow:
  input → classify → brain selection
    main     → LLM direto
    conclave → debate 3 agentes (multi-rodada se complexity=complex)
    squad    → agentes especializados debatem entre si
    memory   → busca na _memoria/ + resposta contextual
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field

# Cérebro = Claude pela assinatura (sem Ollama, decisão 19/06). 'DEFAULT_MODEL' é
# só um rótulo herdado por params de modelo; a seleção real é no claude_brain.
DEFAULT_MODEL = "claude"
TIMEOUT       = 30

SYSTEM_ORCHESTRATOR = """\
Você é o orquestrador da Jamba, assistente pessoal de Murillo Affonso.

Analise o input e retorne SOMENTE um JSON válido (sem markdown, sem explicação):

{
  "intent": "<o que o usuário quer em 2-4 palavras>",
  "complexity": "simple|medium|complex",
  "brain": "main|conclave|squad|memory|exec",
  "agents": ["<lista de agentes necessários>"],
  "plan": "<plano de ação em 1-2 frases>",
  "requires_action": true|false,
  "action_intent": "<intent do command_router ou null>",
  "response_type": "text|code|analysis|plan|deliverable",
  "conclave_rounds": 1
}

Regras de complexity:
- simple:  pergunta direta, 1 passo, conversa casual
- medium:  análise, planejamento, 2-3 passos
- complex: projeto completo, código, decisão estratégica, múltiplos domínios

Regras de brain:
- main:     raciocínio individual direto (default para simple/medium)
- conclave: decisões que precisam de debate crítico (usa conclave_rounds=2 se complex)
- squad:    tarefas que precisam de múltiplos especialistas colaborando
- memory:   buscar histórico, preferências, decisões anteriores
- exec:     tarefa de execução pura (programar, rodar, refatorar) → delega pro Codex

Agentes disponíveis: architect, developer, analyst, qa, jarvis_soul

Para ações locais (action_intent):
abrir_youtube, abrir_navegador, abrir_terminal, abrir_vscode,
abrir_projeto, abrir_openwebui, tocar_musica, registrar_ideia,
status_sistema, acao_perigosa
"""

SYSTEM_MAIN_BRAIN = """\
Você é o Jamba, assistente pessoal de Murillo Affonso — um mordomo de IA estilo JARVIS.
Trate Murillo sempre por "senhor". Tom respeitoso, sereno e elegante, mas direto e prático.
Sempre termine com um próximo passo concreto. Responda em português, de forma concisa.
"""

SYSTEM_MEMORY_BRAIN = """\
Você é o Jamba no modo Memória — mordomo de IA de Murillo. Trate-o por "senhor".
Tem acesso ao histórico e decisões anteriores.
Use o contexto fornecido para dar uma resposta personalizada e relevante.
Responda em português, referenciando informações do histórico quando útil.
"""


@dataclass
class OrchestrationResult:
    intent:          str  = "desconhecido"
    complexity:      str  = "simple"
    brain:           str  = "main"
    agents_used:     list = field(default_factory=list)
    plan:            str  = ""
    requires_action: bool = False
    action_intent:   str | None = None
    response_type:   str  = "text"
    response:        str  = ""
    conclave_result: dict = field(default_factory=dict)
    squad_result:    dict = field(default_factory=dict)
    memory_context:  str  = ""
    exec_running:    bool = False
    fallback:        bool = False


class Orchestrator:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def process(self, user_input: str, history: list[dict] | None = None) -> OrchestrationResult:
        result = OrchestrationResult()

        # Atalho determinístico: se should_delegate, roteia pro Codex sem classificar
        from backend.delegacao import enabled, should_delegate
        if enabled() and should_delegate(user_input):
            response, _ = self._run_exec(user_input, "")
            result.response = response
            result.brain = "exec"
            result.exec_running = True
            return result

        plan = self._classify(user_input)
        if plan:
            result.intent          = plan.get("intent", "conversa")
            result.complexity      = plan.get("complexity", "simple")
            result.brain           = plan.get("brain", "main")
            result.agents_used     = plan.get("agents", [])
            result.plan            = plan.get("plan", "")
            result.requires_action = plan.get("requires_action", False)
            result.action_intent   = plan.get("action_intent")
            result.response_type   = plan.get("response_type", "text")
            self._conclave_rounds  = int(plan.get("conclave_rounds", 1))
        else:
            result.fallback       = True
            result.brain          = "main"
            self._conclave_rounds = 1

        if result.requires_action and result.action_intent:
            result.response = f"Executando: {result.intent}"
            return result

        brain = result.brain

        if brain == "exec":
            result.response, result.exec_running = self._run_exec(user_input, result.plan)

        elif brain == "memory":
            result.response = self._memory_brain(user_input, result)

        elif brain == "squad" or (brain == "main" and len(result.agents_used) >= 2):
            result.response, result.squad_result = self._run_squad(user_input, result)

        elif brain == "conclave" or result.complexity == "complex":
            result.response, result.conclave_result = self._run_conclave(user_input, result)

        else:
            result.response = self._main_brain(user_input, history or [])

        # Salva decisões complexas na memória automaticamente
        if result.complexity in ("medium", "complex") and result.response:
            self._auto_save(user_input, result)

        return result

    # ── Brains ────────────────────────────────────────────────

    def _run_squad(self, text: str, result: OrchestrationResult):
        from agents.meta import SquadCreator
        from agents.memory_bridge import MemoryBridge
        # Carrega contexto de memória para o AIOS Master
        mb = MemoryBridge()
        mem_ctx = mb.recall(text, limit=2)
        sc = SquadCreator(model=self.model)
        squad_result = sc.create_and_run(text, memory_context=mem_ctx)
        result.agents_used = squad_result.get("agents", result.agents_used)
        # Faz a memória crescer
        mb.grow(text, squad_result.get("synthesis", ""),
                squad_result.get("agents", []),
                squad_result.get("deliverable", ""))
        return squad_result.get("synthesis", ""), squad_result

    def _run_conclave(self, text: str, result: OrchestrationResult):
        from conclave import Conclave
        rounds = getattr(self, "_conclave_rounds", 1)
        if result.complexity == "complex":
            rounds = max(rounds, 2)
        c = Conclave(model=self.model)
        conc = c.debate(text, result.plan, rounds=rounds)
        return conc.get("synthesis", ""), conc

    def _memory_brain(self, text: str, result: OrchestrationResult) -> str:
        from agents.memory_bridge import MemoryBridge
        from llm_providers import call_claude
        mb = MemoryBridge()
        recalled = mb.recall(text)
        context = f"Memória relevante:\n{recalled}" if recalled else ""
        result.memory_context = recalled

        messages = [{"role": "system", "content": SYSTEM_MEMORY_BRAIN}]
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": text})
        try:
            return call_claude(messages)
        except Exception as e:
            return f"Memória inacessível: {e}"

    def _main_brain(self, text: str, history: list[dict]) -> str:
        from llm_providers import call_claude
        messages = [{"role": "system", "content": SYSTEM_MAIN_BRAIN}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": text})
        try:
            return call_claude(messages)
        except Exception as e:
            return f"Cérebro indisponível: {e}"

    def _run_exec(self, text: str, plano: str = "") -> tuple[str, bool]:
        """Roteia pra Codex via brain_switch com guardrails."""
        from backend.delegacao import montar_brief
        from backend import brain_switch

        brief = montar_brief(text, plano)
        response = brain_switch.dispatch(brief, engine="codex")
        # Retorna resposta + flag de que Codex foi despachado
        return response, True

    # ── Classify ──────────────────────────────────────────────

    def _classify(self, text: str) -> dict | None:
        from llm_providers import call_claude
        try:
            content = call_claude([
                {"role": "system", "content": SYSTEM_ORCHESTRATOR},
                {"role": "user",   "content": text},
            ], temperature=0.1)
            content = re.sub(r"```(?:json)?|```", "", content).strip()
            return json.loads(content)
        except Exception:
            return None

    # ── Auto-save ─────────────────────────────────────────────

    def _auto_save(self, task: str, result: OrchestrationResult) -> None:
        try:
            from agents.memory_bridge import MemoryBridge
            mb = MemoryBridge()
            if result.squad_result.get("used"):
                mb.save_decision(task, result.response, result.agents_used)
            elif result.conclave_result.get("used") and result.complexity == "complex":
                mb.save_decision(task, result.response, ["critico", "advogado", "sintetizador"])
        except Exception:
            pass
