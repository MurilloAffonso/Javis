# crewAI (crewAIInc/crewAI) — resumo

**Fonte:** https://github.com/crewAIInc/crewAI (53.7k estrelas, Python)
**Coletado por:** esquadrão de estudo (técnico) em 2026-06-16. Resumo escrito por Claude lendo o README real do repositório, não NotebookLM.

## O que é
Framework open-source de orquestração de múltiplos agentes de IA com "papéis" (role-playing). Cada agente recebe um papel, um objetivo e ferramentas; um "crew" (equipe) coordena vários agentes trabalhando juntos numa tarefa complexa, com handoff de contexto entre eles.

## Por que importa pro Javis
É a mesma ideia arquitetural do "registry/orquestrador mestre" que o Javis já usa (Orion orquestrando Khan/Phantom/Vera etc. na galeria de agentes) — só que o crewAI é uma implementação real, testável, com 53k+ estrelas. Vale como referência de padrão pra evoluir `mission_board.py`/mode de delegação entre agentes do Javis, especialmente se algum dia quisermos automatizar de verdade o que hoje é só visual (galeria de agentes fictícia).

## Próximo passo prático
Nenhuma ação imediata — é referência de arquitetura, não algo pra instalar agora. Se o Javis evoluir pra ter agentes reais (não só visual), revisitar este repo como ponto de partida.
