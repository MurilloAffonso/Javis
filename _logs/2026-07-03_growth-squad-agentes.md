# Growth squad — 7 agentes reutilizáveis (minerados do The Agency)

**Data:** 2026-07-03

## Decisão
Murillo: implementar os agentes prioritários do The Agency como agentes de 1ª classe do
Javis, **reutilizáveis em qualquer projeto** (não só Vem Passear); dobrar os
não-prioritários dentro dos agentes existentes.

## Implementado
### 7 agentes novos (group="growth") em agents/specialized.py + AGENT_REGISTRY
- **content_strategist** ✍️ — estratégia de conteúdo/pauta (pilares, gancho 3s, repurpose)
- **short_video_editor** 🎬 — edição de Reels/TikTok (hook 3s, áudio -12/-24dB, corte na batida)
- **paid_social** 📣 — tráfego pago enxuto (retargeting first, criativo UGC, 1 variável/teste)
- **discovery_coach** 🎯 — qualificação de venda (SPIN/Gap/Sandler; qualifica antes de propor)
- **pipeline_analyst** 📊 — diagnóstico de funil (velocidade, gargalo, alerta de estagnação)
- **aeo_strategist** 🔎 — ser citado por IA de busca (FAQ+schema, guias, medir citação)
- **feedback_synth** 💬 — feedback/reviews → insight priorizado por impacto

Roster foi de 11 → **18** especialistas (via GET /agents → aparecem no dropdown
"Rodar agente especialista" da tela Tarefas; rodáveis por POST /agents/run em qualquer projeto).

### Skills detalhadas (primeiras de verdade — _skills/ estava vazio)
7 arquivos `_skills/agente-<id>.md` com missão/faz/não-faz/workflow/**métrica de sucesso**.
São a FONTE ÚNICA (agent_runner._load_skill sobrepõe a persona Python). Editáveis sem tocar código.

### Não-prioritários dobrados nos agentes existentes
- whimsy-injector → **Jarvis Soul** (deleite com propósito no tom)
- automation-governance + devops-automator → **DevOps** ("vale automatizar?" + validação/log/idempotência)
- persona-walkthrough → **UX Designer** (percorrer o fluxo na pele da persona)
- testing-workflow-optimizer → **QA** (otimizar o fluxo, não só achar bug)

## Verificação
- specialized.py sintaxe OK; get_agents_info() = 18; os 7 growth carregam skill (used_skill=True).
- Frontend não precisou mudar (a tela Tarefas já lê state.runnable de /agents).
- **Precisa restart do server.py** pra o roster novo aparecer.

## Fora de escopo (de propósito)
search-query-analyst, sprint-prioritizer (já cobertos por PM/PO), voice-ai-eng (é infra,
virou nota no gemini_brain). gemini-cli = não adotar (agente de código).
