# View "Fluxo Vem Passear" na interface — 19/06

## Pedido
Murillo: trazer o fluxograma de marketing da Vem Passear pra DENTRO da interface
do Javis, no estilo quadro (Monday), como a entrega visual.

## O que foi feito
Nova view **Fluxo VP** (`🔀`), renderizando o pipeline em raias — espelha
`_projetos/cerebro-jampa/fluxograma-vem-passear.md`.

- **`frontend/index.html`**: botão na sidebar (`data-view="fluxovp"`, depois do
  Quadro) + container `#view-fluxovp` com header, legenda (G/C/▶/↺) e `#fvp-board`.
- **`frontend/app.js`**: `PIPELINE_VP` (6 raias + loop), `_fvpLane()`,
  `renderPipelineVP()`; hook em `switchView` (`if fluxovp → renderPipelineVP`);
  entrada em `VIEW_TITLES`. As raias e os gates batem com o .md/linha-editorial:
  Briefing(você) ▶ Conteúdo(Nova)[G] ▶ Roteiro&Copy(Nova+Midas)[C] ▶
  Produção(Design)[C] ▶ Tráfego(Midas)[G] ▶ Distribuição. Faixa de baixo = loop
  de Aprendizado (Midas mede → vira o briefing da semana).
- **`frontend/style.css`**: `.fvp-*` (raias coloridas por função, cards,
  gate-rows G=âmbar/C=violeta, setas, loop verde), tema reaproveitado.

## Verificação (real, Playwright no servidor ao vivo)
- `node --check app.js` — OK.
- `switchView('fluxovp')` → view ativa, título "Fluxo Vem Passear".
- DOM: **6 raias** (Briefing→Distribuição), **4 gates**, **5 setas**, **loop**
  presente, 1ª raia com 5 cards. Bate com o desenho.
- Console: só o 404 do favicon (pré-existente).
- Screenshot full-page: `_logs/screenshots/fluxo-vp-interface.png`.

## Follow-up pequeno (não feito)
O rodapé da sidebar ainda mostra um indicador "OLLAMA" (`#svc-ollama`), que ficou
sem sentido depois de remover o Ollama (18-19/06). Trocar pra "CLAUDE" quando der.

**Sem commit/push — Murillo revisa e decide.**
