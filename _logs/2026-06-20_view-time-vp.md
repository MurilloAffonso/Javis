# View "Time Vem Passear" — os 5 agentes na interface — 20/06

## Pedido
Plugar o squad da Vem Passear (`vp_squad`, 5 agentes com contrato) numa view, com
o contrato à mostra e botão pra acionar.

## O que foi feito
Nova view **Time VP** (`👥`), que bebe do endpoint `GET /vp/agents` e mostra os 5
agentes como cards, cada um com o CONTRATO visível.

- **`frontend/index.html`**: botão na sidebar (`data-view="timevp"`, depois do
  Fluxo VP) + container `#view-timevp` com `#tvp-grid`.
- **`frontend/app.js`**: `renderVPSquad()` (fetch `/vp/agents`), `_vpCard()`
  (card com Entra/Sai/**Não faz** + textarea + botão), `runVPAgent()` (POST
  `/vp/agents/run`, mostra "trabalhando ~40s", renderiza o resultado em markdown);
  hook em `switchView`; entrada em `VIEW_TITLES`.
- **`frontend/style.css`**: `.tvp-*` (grid de cards, contrato, "Não faz" com barra
  vermelha, textarea, botão violeta, área de resultado).

## Verificação (real, Playwright no servidor ao vivo)
- `node --check app.js` — OK.
- `switchView('timevp')` → view ativa, título "Time Vem Passear".
- DOM: **5 cards** (Olheiro, Nova, Estúdio, Midas, Analista), cada um com "Não faz"
  e botão "Acionar". Confirmado no screenshot: cada card mostra ENTRA / SAI /
  NÃO FAZ (em vermelho) + campo de tarefa + botão.
- Backend já validado antes: `/vp/agents` total 5; execução real do Midas
  respeitou o contrato (rascunho, não inventou preço). 71 testes passando.
- Screenshot: `_logs/screenshots/time-vp-interface2.jpeg`.

## Estado final da amarração (tudo conectado)
| Camada | Status |
|---|---|
| Visual do fluxo (Fluxo VP) | ✅ |
| Tarefas (Pipeline no Quadro, Raia 1 rodada) | ✅ |
| Contratos (agentes-contratos.md, 5) | ✅ |
| Backend (vp_squad executável) | ✅ |
| **UI do time (Time VP, aciona de verdade)** | ✅ agora |

O "quem faz o quê" agora está EXPLÍCITO na tela: cada agente mostra o que entra,
o que sai e o que NÃO faz, e dá pra acionar ali mesmo.

**Sem commit/push — Murillo revisa e decide.**
