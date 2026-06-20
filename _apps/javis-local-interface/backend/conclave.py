"""Conclave — sistema de debate autônomo de 3 agentes.

Modo padrão (1 rodada):
  Crítico audita → Advogado ataca → Sintetizador integra

Modo multi-rodada (rounds > 1):
  Cada rodada: Crítico refuta → Advogado questiona → Sintetizador refina
  Resultado final = síntese da última rodada

Inspirado em multi-agent-debate (github.com/arbgjr/multi-agent-debate).
"""
from __future__ import annotations
from dataclasses import dataclass

# Conclave roda pelo cérebro único (Claude assinatura via llm_providers.call_openai,
# que é alias de call_claude). 'DEFAULT_MODEL' é só rótulo herdado. Sem Ollama.
DEFAULT_MODEL = "claude"
TIMEOUT       = 30

SYSTEM_CRITICO = """\
Você é o Conclave Crítico do Javis.
Função: auditar a lógica da solução proposta.
- Encontre inconsistências, riscos e pontos fracos
- Seja objetivo e específico — máximo 3 pontos críticos
- Em rodadas posteriores, responda às contra-argumentações anteriores
- Responda em português, de forma direta
"""

SYSTEM_ADVOGADO = """\
Você é o Conclave Advogado do Javis.
Função: atacar o plano e questionar suposições.
- Teste robustez com perguntas difíceis
- Identifique premissas não verificadas
- Em rodadas posteriores, intensifique os pontos ainda não respondidos
- Máximo 3 ataques — responda em português
"""

SYSTEM_SINTETIZADOR = """\
Você é o Conclave Sintetizador do Javis.
Função: integrar críticas e ataques em uma solução melhorada.
- Absorva os pontos válidos do Crítico e do Advogado
- Em rodadas finais: entregue a decisão definitiva, robusta e prática
- Responda em português
"""


class Conclave:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def debate(self, user_input: str, initial_plan: str = "", rounds: int = 1) -> dict:
        """Executa o debate. rounds=1 é o modo clássico; rounds>1 é autônomo multi-rodada."""
        base = f"Pedido: {user_input}\nPlano inicial: {initial_plan or user_input}"

        history: list[dict] = []  # {round, critico, advogado, synthesis}
        critico   = ""
        advogado  = ""
        synthesis = ""

        for r in range(1, rounds + 1):
            prior = ""
            if history:
                last = history[-1]
                prior = (
                    f"\n\n— Rodada anterior —\n"
                    f"Crítico: {last['critico']}\n"
                    f"Advogado: {last['advogado']}\n"
                    f"Síntese parcial: {last['synthesis']}"
                )

            ctx = base + prior

            critico   = self._call(SYSTEM_CRITICO,      ctx)
            advogado  = self._call(SYSTEM_ADVOGADO,      ctx + f"\n\nCrítica: {critico}")
            synthesis = self._call(
                SYSTEM_SINTETIZADOR,
                ctx + f"\n\nCrítica: {critico}\n\nAtaque: {advogado}"
            )

            history.append({
                "round":    r,
                "critico":  critico,
                "advogado": advogado,
                "synthesis": synthesis,
            })

        return {
            "critico":   critico,
            "advogado":  advogado,
            "synthesis": synthesis,
            "rounds":    history,
            "used":      True,
        }

    def _call(self, system: str, user_content: str) -> str:
        from llm_providers import call_openai
        try:
            return call_openai([
                {"role": "system", "content": system},
                {"role": "user",   "content": user_content},
            ], temperature=0.3)
        except Exception as e:
            return f"[Conclave indisponível: {e}]"
