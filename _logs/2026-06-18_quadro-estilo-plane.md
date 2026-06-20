# Quadro estilo Plane sobre as missões reais — Fatia 1 — 18/06

## O que foi decidido

Murillo viu a interface do **makeplane/plane** (gerenciador de projetos
open-source, tipo Jira/Linear) e quis aquela usabilidade de **quadro Kanban**
na interface do Javis — mas reaproveitando os dados que já existem, sem instalar
o Plane (que exige Docker+Postgres+Redis).

Achado-chave: os dados do Javis **já estão no formato do Plane**. O
`mission_board.py` devolve missões (= Cycles/Modules) com nodes (= Work Items),
e cada node **já tem campo `status`** (`pending`/`running`/`done`). Faltava só
**mostrar** em colunas de status.

## Mudanças (Fatia 1 — só frontend, aditivo, zero backend novo)

- **`frontend/index.html`**: botão "📋 Quadro" na sidebar (antes de Projetos) +
  container `view-quadro` com header, filtros e `quadro-board`.
- **`frontend/app.js`**: `VIEW_TITLES.quadro`, hook `renderQuadro()` no
  `switchView`, e a função `renderQuadro()` + `setQuadroFilter()` +
  `_loadQuadroNodes()`. Achata os nodes de todas as missões em 3 colunas
  (Pendente/Em andamento/Concluído). Filtro por missão no topo (chips).
- **`frontend/style.css`**: estilos do board (`.quadro-board`, `.quadro-col`,
  `.qcard`, `.qfilter`...) usando os tokens do tema (violet/progress/emerald).

## Detalhe técnico que pegou na verificação

O endpoint `/missions` **omite os nodes** de propósito (linha 1543-1545 do
server.py: `{k:v ... if k != "nodes"}`); os nodes só vêm por
`/missions/{id}/nodes`. Então o `renderQuadro` busca os nodes de cada missão em
paralelo (`Promise.all`) com cache (`_quadroNodes`), sem precisar mexer no
backend. São ~5 missões → custo de rede irrisório.

## Verificação (real, no browser)

- `node --check app.js` → JS_OK (duas vezes: antes e depois do fix dos nodes).
- Backend no ar (200 em `/`). Playwright: abriu `/`, clicou em "Quadro",
  screenshot mostra cards reais — Pendente com tarefas (legendas, carrossel),
  Concluído cheia de tarefas riscadas, cada card com a tag da missão de origem.
- Único erro de console = `favicon.ico` 404 (pré-existente, não relacionado).

## Próximos passos (escalar o Plane)

1. **Arrastar card pra mudar status** — precisa gravar de volta. O backlog hoje
   é markdown (`_data/codex_backlog.md`); mudar status = reescrever o checkbox.
   Decidir se o Quadro passa a ser fonte de escrita.
2. **Assignee = agente** — os ids dos 17 agentes já batem; dá pra atribuir
   tarefa a agente e convocar no clique.
3. Avaliar se o Quadro vira o centro da UI (hoje entrou como view nova,
   decisão do Murillo, mantendo Projetos/Sala/Mente intactas).

## Arquivos temporários

Screenshots de verificação na raiz: `quadro-plane.png`, `quadro-plane2.png`,
`quadro-final.png`. Posso remover quando o Murillo aprovar (regra: não deleto sem
ok).

**Sem commit/push — Murillo revisa e decide o que comita.**
