# Journey Log por tarefa (task_events) — 20/06

Cada tarefa do Javis vira uma entidade com linha do tempo: nascimento → eventos →
checkpoints → aprovação → avanço → conclusão. Camada ADITIVA sobre o SQLite.

## Tabela criada
`task_events` (em `migrations/schema.sql`): id, task_id, event_type, actor,
agent_id, message, metadata_json, created_at (+ índice por task_id, id).
Migração idempotente: é `CREATE TABLE IF NOT EXISTS`, e o `db.init_db()` roda o
`schema.sql` via `executescript` em todo boot — então bancos JÁ existentes ganham
a tabela automaticamente, sem ALTER e sem perder dados. (Confirmado: a tabela foi
criada no `javis.db` que já existia.)

## Arquivos alterados
- **`migrations/schema.sql`**: tabela `task_events` + índice.
- **`repositories.py`**: `TaskEventsRepository` (`_TaskEvents`) com
  `add_event(task_id, event_type, actor, message, agent_id=None, metadata=None)`,
  `list_by_task(task_id)` (ordem cronológica, `metadata_json`→dict em `metadata`),
  `count_by_task(task_id)`. Instância `repo.task_events`.
- **`backend/agent.py`** (`_fluxo_pauta_vp`): helper `_journey()` + eventos na
  jornada da PAUTA (t0): `task_created`, `intent_detected`, `agent_called`
  (nova), `file_generated` (nova), `approval_requested`. A aprovação Gate 1 agora
  ancora `task_id = t0` (a pauta) — assim "Ver jornada" mostra a timeline completa.
- **`backend/approval_effects.py`**: helper `_journey()` + eventos na decisão:
  aprovar → `approval_approved` (ator murillo), `workflow_advanced`,
  `design_task_unlocked` (estudio, metadata com a design_task); rejeitar →
  `approval_rejected` (murillo), `adjustment_required` (nova).
- **`backend/server.py`**: endpoint **`GET /tasks/{task_id}/events`** → timeline
  cronológica (horário, ator, agente, tipo, mensagem, metadata).
- **`frontend/app.js`**: botão discreto "Ver jornada" no card da aprovação +
  `viewJourney()` (toggle, puxa /tasks/{id}/events) + `_journeyRow()` (linha
  horário·tipo·ator·mensagem).
- **`frontend/style.css`**: `.ap-journey-btn` e `.jn-*` (timeline simples,
  reaproveitando o tema; sem mudar identidade).

## Eventos implementados
Fluxo da pauta: `task_created`, `intent_detected`, `agent_called`,
`file_generated`, `approval_requested`.
Gate 1 aprovada: `approval_approved`, `workflow_advanced`, `design_task_unlocked`.
Gate 1 rejeitada: `approval_rejected`, `adjustment_required`.

## Endpoints
`GET /tasks/{task_id}/events` — timeline da task.

## Testes (`tests/test_task_events.py`, DB temporário isolado) — 81 → 86 passed
- criar/listar evento (ordem, metadata parseada, agent_id, count).
- fluxo da pauta cria os 5 eventos esperados (vp_squad/mission_board/logger
  mockados; pauta real preservada via backup/restore).
- aprovar Gate 1 gera approval_approved + workflow_advanced + design_task_unlocked
  (ator murillo no approval_approved).
- rejeitar gera approval_rejected + adjustment_required e NÃO gera design_task_unlocked.
- endpoint /tasks/{id}/events retorna a timeline cronológica.

## Verificação ao vivo (Playwright)
- Card da Gate 1 com "Ver jornada"; ao clicar, timeline com os 5 eventos
  (task_created → … → approval_requested), horário·tipo·ator·mensagem. Design
  preservado. Screenshot: `_logs/screenshots/journey-log-ui.jpeg`.
- Para o demo, a Gate 1 existente (criada antes do Journey Log, task_id=t1) foi
  alinhada a t0 e a jornada da pauta (que já existia) foi reconstituída com os 5
  eventos. Novos fluxos já registram tudo nativamente.

## Pendências (próximas fases)
- "Ver jornada" só está exposto no card de aprovação; o Quadro ainda não tem o
  botão por card (fácil de estender depois).
- Conclusão/morte da task (`task_completed`/`task_closed`) ainda não emitida —
  entra quando o Design/Estúdio rodar (futuro, sem gerar criativo agora).
- `metadata` é exibida só no backend; a UI mostra horário/ator/tipo/mensagem.

## Regras respeitadas
Sem push · sem tela nova grande · sem mudar design · sem integração externa · sem
Missions · sem gerar criativo · SQLite aditivo · JSON/Markdown intactos.
