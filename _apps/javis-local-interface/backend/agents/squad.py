"""Squad — execução colaborativa multi-agente com debate autônomo.

Fluxo:
  Rodada 1 — análise individual (cada agente pelo seu ângulo)
  Rodada 2 — debate cruzado (cada agente responde aos outros)
  Rodada 3 — síntese (agente mais adequado integra tudo)

Inspirado em CrewAI (github.com/crewaiinc/crewai, 47k★)
e AutoGen (github.com/microsoft/autogen, 57k★).
"""
from __future__ import annotations
from .specialized import AGENT_REGISTRY, DEFAULT_MODEL


SYNTHESIS_ORDER = ["jarvis_soul", "analyst", "architect", "developer", "qa"]


class Squad:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def run(self, task: str, agent_ids: list[str], rounds: int = 2) -> dict:
        valid = [a for a in agent_ids if a in AGENT_REGISTRY]
        if not valid:
            return {"used": False, "synthesis": "", "rounds": []}

        agents = {aid: AGENT_REGISTRY[aid](model=self.model) for aid in valid}
        round_log: list[dict] = []

        # ── Rodada 1: análise individual ────────────────────────
        r1: dict[str, str] = {}
        for aid, agent in agents.items():
            r1[aid] = agent.execute(task)
        round_log.append({"round": 1, "type": "analise", "outputs": dict(r1)})

        last_outputs = dict(r1)

        # ── Rodadas intermediárias: debate cruzado ───────────────
        for rnum in range(2, rounds + 1):
            rN: dict[str, str] = {}
            for aid, agent in agents.items():
                others = "\n\n".join(
                    f"[{k}]: {v}" for k, v in last_outputs.items() if k != aid
                )
                context = f"Perspectivas dos outros agentes:\n{others}" if others else ""
                rN[aid] = agent.execute(
                    f"Com base nas perspectivas acima, refine sua análise sobre: {task}",
                    context=context,
                )
            round_log.append({"round": rnum, "type": "debate", "outputs": dict(rN)})
            last_outputs = dict(rN)

        # ── Síntese final ────────────────────────────────────────
        synth_id = next((s for s in SYNTHESIS_ORDER if s in valid), valid[0])
        synth_agent = agents[synth_id]

        all_context = "\n\n".join(
            f"[Rodada {entry['round']} — {aid}]: {txt}"
            for entry in round_log
            for aid, txt in entry["outputs"].items()
        )
        synthesis = synth_agent.execute(
            f"Integre todas as perspectivas e entregue a melhor solução final para: {task}",
            context=all_context,
        )

        return {
            "used":      True,
            "agents":    valid,
            "rounds":    round_log,
            "synthesis": synthesis,
        }

    def quick_run(self, task: str, agent_id: str) -> str:
        """Executa um único agente sem debate."""
        if agent_id not in AGENT_REGISTRY:
            return ""
        return AGENT_REGISTRY[agent_id](model=self.model).execute(task)
