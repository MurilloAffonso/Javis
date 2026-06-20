# Quadro lendo SQLite como fonte principal (Markdown = fallback) — 20/06

O Kanban deixou de depender do Markdown/mission_board: agora lê do SQLite via
`GET /tasks`. O Markdown segue como fallback/compatibilidade.

## Endpoint criado
`GET /tasks?status=&workflow=&agent=&project_id=` — tasks do SQLite com:
id, ext_id, title, status, agent, workflow (=mission), project_id, created_at,
updated_at, completed_at, killed_at, has_digest. Filtros opcionais por status,
workflow, agent, project_id. Resposta inclui `source: "sqlite"`.

## Fallback Markdown (mantido)
- Se o SQLite estiver vazio, `GET /tasks` chama `db_sync.sync_tasks()` (lê o
  `codex_backlog.md` via mission_board) ANTES de responder.
- O Markdown NÃO é apagado; o dual-write atual (flow/sync) continua.
- `sync_tasks` agora NÃO rebaixa status terminal já definido no SQLite
  (completed/killed/gate_approved) — o Markdown não sobrescreve o estado real do
  ciclo de vida. Também preenche `project_id` (mapa mission→projeto).

## Como o Quadro passou a ler SQLite
- **`frontend/app.js`**: `renderQuadro()` reescrito — busca `GET /tasks` (com
  `?workflow=` quando filtrado), monta 4 colunas mapeando status→coluna:
  - Pendente (pending) · Em andamento (running) · Aprovado/Destravado
    (done, gate_approved) · Concluído/Morto (completed, killed).
  - Novo `_quadroCard(t)`: título, agente/dono (ou workflow), status, botão
    "Ver jornada" e selo "📄 digest" se a task tiver digest.
  - Filtros (chips) montados a partir dos próprios `workflow` retornados — sem
    depender de `/missions`.
  - `viewJourney`/`completeTask` generalizados pra receber um `hostId` (servem
    o card de aprovação E o card do Quadro). "Concluir entidade" aparece dentro
    da jornada (quando a task ainda não está encerrada) e, ao concluir, o Quadro
    re-renderiza.
- **`frontend/style.css`**: grid do board 3→4 colunas; `.qcard-st`,
  `.qcard-actions`, `.qcard-jbtn`, `.qcard-digest`, cores das colunas novas
  (approved=violeta, completed=vermelho). Sem mudar identidade visual.

## Arquivos alterados
- `migrations/schema.sql` + `db.py`: colunas `agent`, `project_id` em `tasks`
  (migração aditiva idempotente).
- `repositories.py`: `_Tasks.upsert` aceita `agent`/`project_id` (COALESCE
  preserva existente); novo `for_board(status, workflow, agent, project_id)` que
  deriva o agente do Journey Log quando a coluna está vazia.
- `db_sync.py`: `sync_tasks` preenche `project_id` e preserva status terminal.
- `server.py`: endpoint `GET /tasks` (fonte principal + fallback Markdown).
- `frontend/app.js`, `frontend/style.css`: Quadro lendo SQLite (acima).

## Testes (`tests/test_quadro_tasks.py`) — 91 → 96 passed
- GET /tasks retorna tarefas do SQLite (campos esperados, source=sqlite).
- filtros status/workflow/project_id funcionam.
- Quadro renderiza do SQLite mesmo com o Markdown quebrado (independência).
- task concluída aparece como `completed` + `has_digest` + completed_at.
- fallback Markdown: SQLite vazio sincroniza do backlog e popula a tabela.

## Verificação ao vivo (Playwright)
View Quadro: 4 colunas (Pendente 6 · Em andamento 0 · Aprovado/Destravado 12 ·
Concluído/Morto 0), 18 cards, `source: sqlite`, chips de filtro por workflow,
cards com "Ver jornada" e agente derivado (ex.: "nova" no card de Conteúdo).
Screenshot: `_logs/screenshots/quadro-sqlite.jpeg`.

## Pendências (próximas fases)
- Drag-and-drop antigo (Markdown) ficou desativado no novo Quadro; mover status
  pela UI agora seria via ações (ex.: concluir). Re-habilitar arrastar com
  escrita no SQLite é passo futuro (as funções quadroDrag* seguem no código,
  inativas).
- Agente nas tasks de backlog é derivado do Journey Log (quando há); tasks sem
  eventos mostram o workflow no lugar.
- `GET /tasks` faz 2 chamadas no render (lista filtrada + lista p/ as chips);
  dá pra otimizar com um endpoint de workflows distintos depois.

## Regras respeitadas
Sem push · sem tela nova grande · sem mudar design · sem integração externa · sem
Missions · sem gerar criativo · Markdown/JSON intactos (fallback/compatibilidade).
