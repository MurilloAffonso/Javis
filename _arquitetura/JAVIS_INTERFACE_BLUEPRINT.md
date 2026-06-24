# Javis — Proposta de Interface "Central de Comando"

> Traduz a arquitetura de squads (`_docs/arquitetura-javis-os.md`) numa UI.
> NÃO copia a identidade do PDF — usa só a lógica
> centro → projetos → squads → agentes → inputs → outputs → métricas.
> Evolui a UI atual (views: chat, quadro, projects, agents, room…). Data: 2026-06-23.

## Design System (a "pele" da central de comando)
- **Tema:** dark-first (central de comando). Fundo `#0B0E14`, superfície `#11151B`,
  card `#161B24`, borda `rgba(255,255,255,.08)`.
- **Acentos:** ciano elétrico `#22D3EE` (ação/seleção) · verde `#34D399` (online/ok) ·
  âmbar `#FBBF24` (aprovação pendente) · vermelho `#F87171` (risco/matar) ·
  roxo `#A78BFA` (conselho/IA).
- **Tipografia:** Inter/Geist (UI), JetBrains Mono (números/métricas).
- **Forma:** radius 14–16px, sombra suave, borda 1px, muito respiro (grid 8px).
- **Movimento:** transições 150–200ms; nós do mapa com hover sutil; nada piscando.
- **Princípio:** denso em informação, leve em ornamento. Cada pixel = sinal.

---

## 1. Tela inicial (Boot / Saudação)
Primeira coisa ao abrir. O Jamba cumprimenta e mostra o pulso do dia.
- Centro: logo Javis (orbe/núcleo pulsante) + saudação proativa ("Bom dia, senhor.
  3 aprovações esperam, a VP fechou 4 reservas ontem.").
- 3 atalhos grandes: **Continuar conversa** · **Ver aprovações (badge)** · **Abrir Central**.
- Rodapé: status dos serviços (cérebro, voz, projetos online).

## 2. Dashboard central (Home da operação)
Visão-de-tudo em um olhar. Grid de cards:
- **Linha 1 — KPIs globais:** Receita da semana · Aprovações pendentes · Squads ativos · Custo IA.
- **Linha 2 — Projetos plugados:** mini-cards (nome, fase, online, nº squads, 1 métrica).
- **Linha 3 — Fila de aprovações** (as 3 mais urgentes) + **Atividade recente** (timeline).
- **Coluna direita — Jamba:** chat compacto sempre acessível + "o que fazer agora".

## 3. Mapa visual dos projetos
Os projetos como **nós ao redor do núcleo Javis** (não lista). 
- Centro: orbe "JAVIS". Ao redor: nós de projeto (VP, e futuros).
- Cada nó: ícone, nome, anel de status (verde/âmbar), badge de pendências.
- Hover: prévia (fase, squads, métrica-chave). Clique → Tela de projeto.
- Toggle "mapa ↔ grade" pra quem prefere cards em lista.

## 4. Tela de projeto individual (genérica)
Cabeçalho do projeto + o grafo de squads dele.
- **Header:** nome, fase, fonte da verdade (atualizada há X), responsável, status.
- **Faixa de KPIs** do projeto.
- **Mapa de squads** (centro do projeto → squads por área, setas = input/output).
- **Abas:** Squads · Métricas · Aprovações · Próximos Passos · Conhecimento.

## 5. Tela do projeto Vem Passear Jampa (instância real)
A nº 4 preenchida com a VP:
- KPIs: Reservas/semana · CAC/passeio · ROAS · Ocupação.
- Mapa por fase do funil: **Atrair** (Conteúdo, Tráfego) → **Converter** (Atendimento&Vendas)
  → **Operar** (Operação ⛵) → **Reter** (Pós-venda ⭐) → **Analisar** (Dados 📊),
  + transversais (Parcerias 🤝, Site/SEO 🌐, Oferta 🏷️).
- Destaque "maré/clima de hoje" (widget específico de turismo).
- Fila de aprovações da VP (pauta, verba, WhatsApp, remarcação).

## 6. Tela de squads (o grafo)
O mapa de squads de um projeto, navegável.
- Cada squad = **card-nó** com: emoji, nome, área (cor), agente responsável,
  micro-métrica, ponto de status. 
- **Arestas animadas** mostram input→output ("Conteúdo → Tráfego → Vendas").
- Filtro por área (Atrair/Converter/Operar/Reter/Analisar).
- Clique no nó → Tela de agente.

## 7. Tela de agente individual (o Squad Contract visual)
O contrato de um squad numa tela limpa, em duas colunas:
- **Esquerda:** Faz · Não-faz (com "delega para →") · Ferramentas · Agente responsável.
- **Direita:** Input (de quem) · Output (pra quem) · Métricas (sparkline) ·
  Rotina diária/semanal · **Gatilho de aprovação** (destaque âmbar).
- Rodapé: "Rodar agora" (gera rascunho) · histórico de execuções.

## 8. Tela de métricas (Painel de Receita)
Separa o que decide do que é vaidade — visualmente.
- Topo: **métricas que movem receita** (Receita, CAC, LTV, ROAS, Payback) em cards
  grandes com tendência.
- Meio: gráfico de funil por etapa + ranking de passeios/itens por margem.
- Lateral: bloco discreto "vaidade" (likes/alcance) — cinza, fora da decisão.
- CTA: "Abrir Ritual Semanal" (Escalar/Manter/Matar).

## 9. Tela de aprovações humanas (a fila de gates)
Onde você governa. Lista priorizada de cards de decisão:
- Cada card: o que é (pauta/verba/WhatsApp/remarcação), squad de origem, contexto,
  prévia (rascunho/valor), e botões **Aprovar · Ajustar · Recusar**.
- Cor por tipo (âmbar pendente). Filtro por projeto/squad.
- Ações em lote ("Painel de Aprovação em Lote" — aprovar vários rascunhos similares).

## 10. Tela de próximos passos (roadmap)
Kanban estilo Plane (já existe) ligado à arquitetura:
- Colunas: **Agora · Próximo · Depois · Concluído**.
- Cada card linka a um squad/projeto. Puxa de `_estado/proximos-passos.md`.
- Filtro por projeto. Badge de "frente ativa".

---

## 11. Navegação lateral (rail fixo à esquerda)
Ícone + label, agrupado por nível da arquitetura:
```
◉ JAVIS (núcleo)
─────────────
🏠  Central          (dashboard)
🗺️  Projetos         (mapa)
🧩  Squads
🤖  Agentes
📊  Métricas
✅  Aprovações   ⟨badge nº⟩
🎯  Próximos passos
─────────────
💬  Conversa (Jamba)
🧠  Conselho
⚙️  Integrações
─────────────
▸ status: cérebro ● voz ● projetos ●
▸ motor ativo: Claude / Codex
```
Rail recolhível (só ícones). Breadcrumb no topo: Central › VP › Squads › Midas.

## 12. Componentes / Cards (biblioteca)
- **KPI Card:** rótulo, número grande (mono), tendência ↑↓ + %, sparkline.
- **Projeto Card:** ícone, nome, fase, anel de status, nº squads, 1 métrica, badge.
- **Squad Node:** emoji, nome, cor da área, responsável, micro-métrica, status dot.
- **Aprovação Card:** tipo (chip colorido), origem, prévia, 3 botões de ação.
- **Agente Painel:** 2 colunas (Faz/Não-faz | In/Out/Métricas), faixa de aprovação.
- **Timeline item:** hora, squad, ação, resultado.
- **Maré/Clima widget** (VP): ícone, janela de maré baixa, alerta de remarcação.
- **Chat dock:** Jamba sempre a um clique (canto/coluna).

## 13. Hierarquia visual (como o olho navega)
```
NÍVEL 0  Núcleo Javis          → orbe, sempre presente (rail + mapa)
NÍVEL 1  Projetos              → nós ao redor do núcleo
NÍVEL 2  Squads (por área)     → cards-nó dentro do projeto, cor = área
NÍVEL 3  Agente / Contrato     → tela de detalhe (faz/não-faz/in/out)
OVERLAY  Métricas              → números mono, sempre no canto dos cards
OVERLAY  Aprovações            → âmbar, sempre visível (badge no rail)
```
Tamanho/cor/posição comunicam o nível: núcleo > projeto > squad > agente.
Verde=saudável, âmbar=precisa de você, vermelho=risco. Número grande = importa.

## 14. Wireframe textual (telas-chave)

**Dashboard central (nº 2):**
```
┌──────┬──────────────────────────────────────────────┬───────────┐
│ RAIL │  Central                       [busca]  ◐ ⚙   │  JAMBA    │
│ 🏠   │ ┌─────┐┌─────┐┌─────┐┌─────┐                  │ ┌───────┐ │
│ 🗺️   │ │R$128k││ 3   ││ 14  ││$0,40│  KPIs globais   │ │"Bom dia│ │
│ 🧩   │ │receita││apr. ││squads││custo│                │ │ senhor"│ │
│ 🤖   │ └─────┘└─────┘└─────┘└─────┘                   │ └───────┘ │
│ 📊   │ PROJETOS                                       │ [conversa]│
│ ✅3  │ ┌────────┐ ┌────────┐ ┌─ + plugar ─┐          │           │
│ 🎯   │ │ VP ⛵  │ │ (vazio)│ │  projeto    │          │ ▸ fazer   │
│      │ │fase:op │ │        │ └─────────────┘          │   agora:  │
│ 💬   │ │●9 squads│ └────────┘                          │ - aprovar │
│ 🧠   │ └────────┘                                      │   pauta   │
│ ⚙    │ APROVAÇÕES (3)            ATIVIDADE             │ - ver maré│
│      │ ▸ pauta semana  [ver]     09:12 Olheiro: 4 refs │           │
│ ●●●  │ ▸ verba R$200   [ver]     08:40 Midas: 2 leads  │           │
└──────┴──────────────────────────────────────────────┴───────────┘
```

**Tela VP — mapa de squads (nº 5/6):**
```
┌──────┬───────────────────────────────────────────────────────────┐
│ RAIL │ Projetos › Vem Passear ⛵      [Squads|Métricas|Aprovações] │
│      │ KPIs: 24 reservas · CAC R$72 · ROAS 3,4x · ocup. 78%       │
│      │ 🌊 maré baixa hoje 13h–16h · ☀ sem risco de remarcação      │
│      │                                                             │
│      │   ATRAIR        CONVERTER     OPERAR     RETER    ANALISAR   │
│      │  ┌───────┐     ┌────────┐   ┌───────┐ ┌───────┐ ┌────────┐  │
│      │  │CONTEÚ.│────▶│ VENDAS │──▶│OPERAÇ.│▶│PÓS-V. │▶│ DADOS  │  │
│      │  │ 🎨 ●  │     │ 💬 ●   │   │ ⛵ ●  │ │ ⭐ ●  │ │ 📊 ●   │  │
│      │  └───────┘     └────────┘   └───────┘ └───────┘ └────────┘  │
│      │  ┌───────┐                                                  │
│      │  │TRÁFEGO│──────────┘   TRANSVERSAIS:                       │
│      │  │ 📈 ●  │              🤝 Parcerias  🌐 Site  🏷️ Oferta    │
│      │  └───────┘                                                  │
└──────┴───────────────────────────────────────────────────────────┘
```

**Tela de agente (nº 7) — contrato do squad "Midas":**
```
┌──────────────────────────────────────────────────────────────┐
│ ‹ Vem Passear › Squads › Midas 📈   (Tráfego & WhatsApp)       │
├───────────────────────────────┬──────────────────────────────┤
│ FAZ                           │ INPUT  ← Estúdio (peças Gate2) │
│ • agenda/publica              │        ← WhatsApp (mensagens)  │
│ • marca o que impulsionar     │ OUTPUT → posts + rascunhos WA  │
│ • monta resposta WhatsApp     │        → Dados (métricas)      │
│ NÃO FAZ                       │ MÉTRICAS  ╱╲___ cliques WA     │
│ • definir verba → pede Murillo│           reservas · ROAS      │
│ FERRAMENTAS Meta Ads, WA      │ ROTINA  diária: rascunhos      │
│ RESPONSÁVEL humano-no-loop    │         semanal: escala/corte  │
├───────────────────────────────┴──────────────────────────────┤
│ ⚠ APROVAÇÃO: toda mensagem enviada · qualquer verba            │
│ [ Rodar agora ]   histórico: 3 execuções hoje                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 15. Prompt para Figma (Figma AI / FigJam / designer)
> Crie um design system e telas para "Javis", um painel **central de comando** (AIOS)
> que orquestra múltiplos projetos como grafos de squads de IA. Estilo: SaaS moderno,
> dark-first, limpo e profissional (referências de vibe: Linear, Vercel, Raycast —
> NÃO copiar). Paleta: fundo #0B0E14, card #161B24, acento ciano #22D3EE, verde
> #34D399 (ok), âmbar #FBBF24 (aprovação), vermelho #F87171 (risco), roxo #A78BFA
> (IA). Tipografia Inter + JetBrains Mono pra números. Radius 14, bordas 1px sutis,
> muito respiro, grid 8px.
> Telas: (1) Dashboard central com rail lateral de ícones, faixa de KPI cards, grid
> de cards de projeto e fila de aprovações, com um dock de chat "Jamba" à direita;
> (2) Mapa de projetos como nós orbitando um núcleo central "JAVIS"; (3) Tela de
> projeto "Vem Passear" mostrando squads dispostos por fase de funil (Atrair →
> Converter → Operar → Reter → Analisar) conectados por setas input→output, com um
> widget de maré/clima; (4) Tela de agente/squad mostrando um "contrato" em duas
> colunas (Faz/Não-faz à esquerda; Input/Output/Métricas/Aprovação à direita);
> (5) Tela de Métricas separando "métricas que movem receita" (grandes) de "vaidade"
> (apagada); (6) Tela de Aprovações como fila de cards com botões Aprovar/Ajustar/
> Recusar. Componentes reutilizáveis: KPI Card, Projeto Card, Squad Node, Aprovação
> Card, Chat Dock. Entregue como auto-layout, com variantes de estado (online/
> pendente/risco) e modo rail recolhido.

## 16. Prompt para v0 / Lovable / Claude Code (código)
> Construa o front-end do "Javis — Central de Comando" em **React + Tailwind + 
> shadcn/ui**, dark-first, responsivo. Mock os dados (sem backend real por enquanto),
> tipados.
> **Layout:** rail lateral fixo recolhível com ícones+labels (Central, Projetos,
> Squads, Agentes, Métricas, Aprovações[badge], Próximos passos, Conversa, Conselho,
> Integrações) e rodapé de status (cérebro/voz/projetos, motor ativo). Breadcrumb no
> topo. Dock de chat "Jamba" persistente.
> **Tema:** CSS vars — bg #0B0E14, surface #11151B, card #161B24, border rgba(255,
> 255,255,.08), accent #22D3EE, ok #34D399, warn #FBBF24, danger #F87171, ai #A78BFA.
> Fonte Inter + JetBrains Mono (números). Radius 14.
> **Rotas/telas:** `/` Dashboard (KPI cards + grid de projetos + fila de aprovações +
> timeline); `/projects` mapa de nós orbitando o núcleo (use react-flow ou SVG);
> `/projects/vem-passear` squads por fase de funil conectados por setas, + widget
> maré/clima; `/squads/:id` o "Squad Contract" em 2 colunas (Faz/Não-faz | Input/
> Output/Métricas/Rotinas/Aprovação) com botão "Rodar agora"; `/metrics` painel
> separando receita (CAC/LTV/ROAS/Payback, cards grandes c/ sparkline via recharts)
> de vaidade (bloco apagado); `/approvals` fila de cards com Aprovar/Ajustar/Recusar
> e seleção em lote; `/next` kanban (Agora/Próximo/Depois/Concluído).
> **Componentes:** KpiCard, ProjectCard, SquadNode, ApprovalCard, AgentContract,
> ChatDock, StatusDot, TrendBadge. Estados: online(verde)/pendente(âmbar)/risco
> (vermelho). Dados mock: 1 projeto "Vem Passear" com 9 squads (Conteúdo, Tráfego,
> Atendimento&Vendas, Operação, Pós-venda, Dados, Parcerias, Site/SEO, Oferta), cada
> um com faz/não-faz/input/output/ferramentas/métricas/rotinas/aprovação. Priorize
> clareza, hierarquia visual forte e densidade informativa sem poluição.

---
> Base: `_docs/arquitetura-javis-os.md` · `_docs/vem-passear-squads.md`.
> Evolui a UI atual (views chat/quadro/projects/agents). Não substitui de uma vez —
> a navegação nova pode coexistir com as views existentes.
