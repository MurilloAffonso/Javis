# Organograma Mente: setas de handover + paralelo — 18/06

## O que foi decidido

Murillo mostrou prints de um board no Figma (roster de vendas — Vera/Khan/
Phantom etc., o mesmo roster antigo da view "Mente" que já tinha sido
substituído pelos 17 da mente num plano salvo) com um estilo de árvore: setas
sólidas "forced handover" entre agentes em sequência, e agentes alternativos
empilhados sem seta sob o mesmo pai. Perguntou se esse estilo seria mais
didático pro organograma do Javis.

Recomendação dada: manter o agrupamento por fase (já reflete a arquitetura
real) e usar setas de handover só onde existe dependência sequencial de
verdade — não forçar isso no Conclave, que debate em paralelo (Crítico +
Advogado), não em fila.

## O que foi implementado

A view "Mente" já existia funcionando (agrupada por fase: Produto/
Construção/Qualidade/Conclave, faixa Meta no topo) — não foi um plano do
zero, foi um plano salvo (`wobbly-dreaming-dusk.md`) que já tinha sido
executado em sessão anterior. O que faltava era a camada de sequência.

- **`frontend/app.js`**: `MENTE_TREE.groups[].ids` → `flow` (array de
  estágios). Estágio com 1 agente = handover obrigatório pro próximo
  (seta ▶); estágio com vários agentes = paralelo (empilhados, sem seta
  entre eles).
  - Produto: `[[po], [pm], [scrum]]` — PO→PM→Scrum, handover real.
  - Construção: `[[architect], [developer], [ux_designer, devops, data_engineer]]`
    — Architect→Developer→(UX/DevOps/Data Eng em paralelo sob o Developer).
  - Qualidade: `[[qa, analyst]]` — paralelos, sem ordem entre si.
  - Conclave: `[[critico, advogado], [sintetizador]]` — Crítico+Advogado
    debatem em paralelo, depois handover pro Sintetizador.
  - `_orgGroup()` reescrita para renderizar `.org-flow` (estágios + setas)
    em vez do `<ul>` plano anterior.
- **`frontend/style.css`**: `.org-flow`, `.of-stage`, `.of-stage.of-parallel`
  (barra tracejada à esquerda, estilo "alternativas empilhadas" do board de
  referência), `.of-arrow` (▶ violeta).
- **`frontend/index.html`**: legenda da view Mente ganhou `▶ handover
  obrigatório` e `┊ paralelo (sem ordem)`.

### Fora de escopo (decisão deliberada)
Setas **entre grupos** (ex.: Scrum→Architect, Developer→QA) não foram
implementadas — exigiriam SVG/posicionamento absoluto sobre o mecanismo de
árvore CSS clássico já existente (bordas em `::before`/`::after`), risco de
quebrar o layout que já funciona. A dependência entre fases já é implícita
pela hierarquia (todas as fases pendem do AIOS Master).

## Verificação (real, Playwright)

- `node --check app.js` — OK.
- Servidor já rodando em `127.0.0.1:8000`.
- Naveguei pra view Mente, esperei carregar os 17 agentes do `/agents`.
- `document.querySelector('.org-flow').outerHTML` confirmado: Produto
  renderiza `PO ▶ PM ▶ Scrum` com os 3 cards certos.
- Contagem de estágios paralelos confirmada via DOM: `[3, 2, 2]` — Construção
  (UX/DevOps/Data Eng), Qualidade (QA+Analyst), Conclave (Crítico+Advogado).
- Console: só o 404 do favicon (pré-existente, sem relação).
- Screenshot full-page salvo em `_logs/screenshots/mente-org-chart-handover.png`.

## Próximo passo

- Se Murillo quiser depois: setas visuais entre fases (Scrum→Architect,
  Developer→QA) via overlay SVG, separado do mecanismo de árvore CSS atual.

**Sem commit/push — Murillo revisa e decide o que comita.**
