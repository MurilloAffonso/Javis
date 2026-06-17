# Orquestramento trocado para os 17 agentes da "mente" (17/06)

**Pedido:** Murillo comparou o Javis com o "JARVIS" do codandoai.com (17 agentes
de construção/pensamento) e disse que o orquestramento faz mais sentido com esse
time da mente do que com os 8 agentes de vendas que estavam visíveis.

**Achado-chave:** o Javis JÁ TINHA os 17 da mente, idênticos aos do CodandoAI,
implementados no backend e servidos pelo endpoint `/agents` (`server.py:503`):
- `agents/specialized.py` → 10 especialistas + Jarvis Soul
- `conclave.py` → Crítico / Advogado / Sintetizador
- `agents/meta.py` → AIOS Master, Squad Creator, Rootcause

O problema era só de UI: a gallery, a sidebar e o organograma usavam um roster
de vendas hardcoded (`GALLERY_AGENTS`), em vez de puxar os 17 reais. Dois
rosters concorrentes.

**Decisões do Murillo (plano aprovado):** substituir (vendas sai da UI, código
preservado) + organograma "por fase".

## O que foi feito

**Fonte única — a UI agora bebe do `/agents`.** `app.js`:
- `GALLERY_AGENTS` de vendas renomeado para `_LEGACY_SALES_AGENTS` (preservado, não usado).
- Novo `loadAgents()` faz `fetch('/agents')`, achata specialists+conclave+meta
  num único `AGENTS`, e faz merge com `AGENT_PRESENTATION` (fase + status + tag curta,
  que o backend não tem). Fallback local `MIND_AGENTS_FALLBACK` (mesmos 17) se o fetch falhar.
- `renderAgentGallery` lê `AGENTS`, filtra por `phase`, card simplificado (sem os
  campos mock de vendas: skills/ints/queue/lastActivity).
- `openAgentChat`/`convocarAgente` usam `AGENTS` (ids batem com o backend → pronto
  pra futura execução real).
- Organograma reescrito: `MENTE_TREE` "por fase" — faixa Meta (Soul/SquadCreator/Rootcause)
  no topo → AIOS Master → grupos Produto / Construção / Qualidade / Conclave com seus agentes.
- `renderActivityFeed` atualizado para atividade de agentes da mente.

**`index.html`:** filtros da gallery (Vendas/Criativo/Dados/Ops → Produto/Construção/
Qualidade/Conclave/Meta), sidebar (8 de vendas → 7 representativos da mente),
seletor "Agente a treinar" (khan/phantom → analyst/architect/developer/aios_master).

**`style.css`:** cores por fase nos cards e tags (`og-*`), nó de grupo (`.org-group`),
faixa meta (`.org-meta-band`), tag de fase na gallery (`.gc-phase-tag`).

## Verificação real (Playwright + pytest)
- Gallery: **17 cards** com nomes vindos do backend (ex.: "Conclave Crítico", "Rootcause"
  — prova de que puxa do `/agents`, não do fallback). Filtro Conclave → 3 cards. ✓
- Aba Mente: raiz **AIOS Master**, 4 grupos (Produto/Construção/Qualidade/Conclave),
  faixa meta (Jarvis Soul/Squad Creator/Rootcause), 17 cards no total. ✓
- **Nenhum** agente de vendas (Khan/Phantom/Titan/Blade) aparece na UI. ✓
- Só o erro de console `favicon.ico` 404 (pré-existente). ✓
- `pytest tests/ -q` → **54/54**. `node --check app.js` OK. CSS balanceado.
- Screenshot em `_outbox/2026-06-17_mente-17-agentes.png`.

## Fora de escopo (follow-up)
- Wiring de execução real ao clicar num agente (rodar via squad/conclave do backend) —
  os ids já batem, falta só ligar.
- `mission_board.py` / view Sala não mexidos (não citavam vendas).

**Sem commit/push. Murillo revisa e comita.**
