# Morte da entidade + AI Digest da task — 20/06

Fecha o ciclo de vida: nascimento → eventos → aprovação → avanço → CONCLUSÃO/MORTE
→ DIGEST. Camada ADITIVA no SQLite, sem LLM (digest por template local).

## Campos/tabelas alterados
- `tasks` ganhou `completed_at`, `killed_at`, `digest_text` (em `schema.sql` p/ DBs
  novos + ALTER idempotente em `db.py` p/ DBs existentes — não quebra nada).
- Novos `event_type` no Journey Log: `task_completed`, `entity_killed`,
  `ai_digest_created`.

## Arquivos alterados
- **`migrations/schema.sql`** + **`db.py`**: 3 colunas novas em `tasks` (migração
  idempotente; confirmado criadas no `javis.db` existente).
- **`repositories.py`**: `_Tasks` ganhou `get_task`, `complete_task(actor,note)`
  (status='completed' + completed_at/killed_at), `update_digest`. `_Approvals`
  ganhou `by_task` (pro digest ler aprovações da task).
- **`backend/task_lifecycle.py`** (novo):
  - `generate_task_digest(task_id)` — digest por TEMPLATE LOCAL (sem LLM): lê
    task + Journey Log + aprovações e monta: o que foi feito, quem participou,
    principais eventos, aprovação, duração, gargalos/perigos, próximo passo.
  - `complete_task(task_id, note, actor)` — encerra (completed/killed) + cria
    eventos task_completed/entity_killed → gera digest → salva na task →
    ai_digest_created → action_logs (intent task_complete). Idempotente.
- **`backend/server.py`**: `POST /tasks/{id}/complete` (body {note}) e
  `GET /tasks/{id}/digest`. O `GET /tasks/{id}/events` passou a devolver também
  `task_status`/`completed_at`/`killed_at`/`digest_text` (UI lê tudo em 1 chamada).
- **`frontend/app.js`**: na visão "Ver jornada" — mostra o status da entidade;
  se encerrada, bloco "📄 Digest da entidade"; se viva, botão discreto
  "Concluir entidade" (`completeTask` → POST /complete → re-render com o digest).
- **`frontend/style.css`**: `.jn-status/.jn-st-*`, `.jn-complete-btn`, `.jn-digest*`
  (tema reaproveitado, sem mudar identidade).

## Digest implementado (sem cota)
Template local com 7 linhas: status+duração · o que foi feito · quem participou ·
principais eventos (sequência) · aprovação · gargalos/perigos · próximo passo
recomendado. Heurísticas simples a partir dos eventos/aprovações (ex.: se houve
rejeição → "retrabalho"; se design_task_unlocked → próximo passo = produzir
criativos). Pronto pra trocar por LLM no futuro, mas hoje NÃO gasta cota.

## Testes (`tests/test_task_lifecycle.py`) — 86 → 91 passed
- concluir cria task_completed + entity_killed + ai_digest_created (+ completed_at/
  killed_at preenchidos).
- digest gerado e salvo (cabeçalho + "Próximo passo" + persistido na task).
- idempotência: 2ª conclusão recusada, sem duplicar eventos.
- /stats reflete (pending → completed nas contagens).
- endpoints POST /complete e GET /digest funcionam; re-concluir → 409.

## Verificação ao vivo (Playwright)
Entidade descartável com jornada → "Ver jornada" → botão "Concluir entidade" →
status vira `completed`, bloco "Digest da entidade" aparece com o resumo, timeline
passa a ter task_completed/entity_killed/ai_digest_created (6 eventos). Demo limpa
depois; Gate 1 real preservada (pendente). Screenshot:
`_logs/screenshots/entity-digest-ui.jpeg`.

## Pendências (próximas fases)
- Botão "Concluir/Matar entidade" no QUADRO: NÃO feito de propósito — o Quadro lê
  do Markdown (mission_board) e a conclusão/digest é conceito do SQLite; o card
  não se moveria (Markdown não muda), virando meia-feature confusa. A conclusão
  vive na visão da jornada (onde jornada+digest ficam juntos, coerente).
- Digest é template; trocar por LLM (Claude assinatura) quando fizer sentido.
- "Ver jornada"/conclusão hoje só no card de aprovação; estender pro Quadro exige
  reconciliar Markdown↔SQLite (passo futuro).

## Regras respeitadas
Sem push · sem tela nova grande · sem mudar design · sem integração externa · sem
LLM no digest · sem gerar criativo · sem Missions · SQLite aditivo · JSON/Markdown
intactos.
