# Prompt — Criar interface "Central de Comando" do Javis (Claude Code)

> Prompt reutilizável pra colar no Claude Code dentro do projeto local.
> Gera a 1ª versão da interface a partir dos blueprints. Data: 2026-06-23.
> Pré-requisito: os 4 arquivos abaixo devem existir nos caminhos citados
> (_arquitetura/, _projetos/vem-passear/, _templates/).

---

```text
Você está no projeto Javis (assistente/orquestrador local, backend FastAPI em
_apps/javis-local-interface). Leia o CLAUDE.md do projeto e RESPEITE as regras dele
(não deletar arquivos, não commitar sem aprovação, escopo só dentro de javis/).

CONTEXTO — leia estes 4 arquivos ANTES de qualquer coisa e me diga, em 5 linhas, que
arquitetura você entendeu:
1. _arquitetura/JAVIS_BLUEPRINT.md          (Javis = núcleo; projetos plugáveis; Squad Contract)
2. _arquitetura/JAVIS_INTERFACE_BLUEPRINT.md (design system + telas da central de comando)
3. _projetos/vem-passear/VEM_PASSEAR_SQUAD_MAP.md (10 squads reais da Vem Passear)
4. _templates/TEMPLATE_PROJETO_SQUADS.md     (modelo genérico de projeto)

OBJETIVO
Criar a PRIMEIRA versão da interface "Central de Comando" do Javis, baseada nesses
arquivos. É um protótipo navegável com dados MOCK (sem ligar no backend ainda).

REGRAS RÍGIDAS
- NÃO apague, renomeie ou modifique NENHUM arquivo existente do frontend atual
  (_apps/javis-local-interface/frontend/index.html, app.js, style.css).
- Crie tudo ISOLADO numa pasta NOVA: _apps/javis-local-interface/frontend/central/
  (assim coexiste com a interface atual e o FastAPI já serve via StaticFiles).
- Stack: HTML + Tailwind via CDN + JavaScript vanilla modular (sem build, sem npm).
  Roda abrindo o arquivo no navegador. Mantenha simples e expansível.
- Antes de criar arquivos novos, liste pra mim o que vai criar e espere meu "ok".

DESIGN SYSTEM (use exatamente — está no INTERFACE_BLUEPRINT)
- Dark-first. bg #0B0E14, surface #11151B, card #161B24, borda rgba(255,255,255,.08).
- Acentos: ciano #22D3EE (ação), verde #34D399 (ok), âmbar #FBBF24 (aprovação
  pendente), vermelho #F87171 (risco), roxo #A78BFA (IA).
- Fonte Inter (UI) + JetBrains Mono (números). Radius 14, respiro generoso, grid 8px.
- Profissional, limpo, SaaS moderno, central de comando. Bonito sem poluir.

O QUE CRIAR (nesta primeira versão)
1. central/index.html — shell com rail de navegação lateral (Central, Projetos,
   Squads, Métricas, Aprovações[badge], Próximos passos) + área de conteúdo + dock
   de chat "Jamba" no canto. Breadcrumb no topo.
2. central/css/theme.css — as variáveis do design system acima.
3. central/js/components.js — COMPONENTES REUTILIZÁVEIS (funções que retornam HTML):
   kpiCard(), projectCard(), squadNode(), agentContract(), approvalCard(),
   statusDot(), trendBadge(). Documente cada um com um comentário de uso.
4. central/js/data.js — dados MOCK: 1 projeto "Vem Passear" com os 10 squads do
   VEM_PASSEAR_SQUAD_MAP (cada squad com: nome, area, agente, faz, nao_faz, input,
   output, ferramentas, metricas, rotina_diaria, rotina_semanal, aprovacao).
5. central/js/app.js — roteador simples por hash (#/, #/vem-passear, #/squads/:id,
   #/metricas, #/aprovacoes) que renderiza as telas usando os componentes.

TELAS DESTA VERSÃO
A. Tela principal do Javis (#/): faixa de KPI cards globais + grid de cards de
   projeto (Vem Passear) + fila das 3 aprovações pendentes.
B. Tela do projeto Vem Passear (#/vem-passear): header com KPIs + MAPA DE SQUADS
   por fase do funil (Atrair → Converter → Operar → Reter → Analisar) com os
   transversais (Parcerias, Site/SEO, Oferta), squads conectados por setas
   input→output (pode ser SVG/flex simples).
C. Visualização de squads: cada squad é um card-nó clicável (squadNode) que abre
   D. Tela de agente individual (#/squads/:id): o "Squad Contract" em 2 colunas —
   Faz/Não-faz/Ferramentas/Responsável | Input/Output/Métricas/Rotinas/Aprovação,
   com a faixa de aprovação destacada em âmbar.
E. Cards de input/output/métricas reutilizáveis (usados nas telas acima).

CRITÉRIO DE PRONTO
- Abre central/index.html no navegador e navega entre as telas sem erro.
- Os 10 squads da Vem Passear aparecem com seus contratos completos.
- Componentes são reutilizáveis (mesma função usada em telas diferentes).
- Nada do frontend existente foi tocado.
- Código limpo, comentado, fácil de depois plugar nos endpoints reais do backend
  (/projects, /agents). Me explique no final como fazer essa ligação futura.

Comece lendo os 4 arquivos e confirmando a arquitetura. Depois me mostre o plano de
arquivos antes de criar.
```
