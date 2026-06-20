# Ações operacionais do Quadro via SQLite — 20/06

O Quadro deixou de ser só visualização: mover um card altera o status no SQLite,
registra o Journey Log e atualiza a UI. Sem integração externa.

## Endpoint criado
`POST /tasks/{task_id}/status` — body `{ "status": "...", "note": "..." }`.
Status aceitos: `pending | in_progress | gate_approved | completed | killed`.

Comportamento (`task_lifecycle.change_task_status`):
- valida o status; atualiza no SQLite + `updated_at`;
- registra evento `status_changed` em `task_events` com metadata
  `{from_status, to_status, source:"board", note}`;
- registra `task_status_changed` em `action_logs`;
- `/stats` reflete (contagens por status).

Regras:
- `completed`/`killed` REUSAM `complete_task` (não duplica morte/digest);
- task `completed`/`killed` NÃO volta pra `pending` por aqui (bloqueado, 409);
- idempotente: mesmo status = no-op (`unchanged`).

## Frontend (Quadro operacional)
- **`frontend/app.js`**:
  - Coluna "Em andamento" passou a aceitar `running` E `in_progress`; cada coluna
    ganhou `setStatus` (pending → pending · running → in_progress · approved →
    gate_approved · completed → completed).
  - Cards agora são **arrastáveis** (`draggable`, `data-ext-id`), exceto
    `completed`/`killed` (não reabre pelo Quadro).
  - Drag-and-drop reescrito: `quadroDrop` lê o `data-set-status` da coluna alvo e
    faz `POST /tasks/{ext_id}/status`, com feedback (toast) + `refreshStats()` +
    `renderQuadro()`. Mover pra "Concluído/Morto" mostra "Entidade concluída.
    Digest gerado.".
  - "Ver jornada" segue no card; após a mudança, a jornada reflete o
    `status_changed`.
- Sem mudar identidade visual (reaproveitou `.dragging`/`.drag-over` existentes).

## Journey Log
Cada mudança no Quadro cria `status_changed` com metadata
`from_status / to_status / source:"board" / note`.

## Testes (`tests/test_quadro_actions.py`) — 96 → 102 passed
- muda status pelo endpoint (SQLite atualizado);
- registra `status_changed` com metadata correta;
- registra `task_status_changed` em action_logs;
- bloqueia reabrir task completed/killed;
- mover pra completed reusa lifecycle/digest (task_completed/entity_killed/
  ai_digest_created + digest_text);
- idempotência (mesmo status = unchanged) + status inválido → 409 + /stats reflete.

## Verificação ao vivo (Playwright)
Task descartável: arrastável=true; movida Pendente → Em andamento (card mudou de
coluna, Quadro re-renderizou); jornada passou a ter `status_changed`; movida pra
Concluído/Morto → status COMPLETED, selo "📄 digest", card ficou não-arrastável.
Nenhuma integração externa chamada (só repo/task_lifecycle). Demo limpa depois.
Screenshot: `_logs/screenshots/quadro-acoes.jpeg`.

## Arquivos alterados
- `backend/task_lifecycle.py`: `change_task_status` + `_BOARD_STATUSES`.
- `backend/server.py`: endpoint `POST /tasks/{id}/status` (+ `StatusRequest`).
- `frontend/app.js`: colunas com `setStatus`, cards arrastáveis, drag-drop via
  `/tasks/{id}/status`.

## Pendências (próximas fases)
- "in_progress" não tem efeito de negócio além do status (é sinal visual/registro).
- Reabrir entidade encerrada exigiria endpoint próprio (deliberadamente fora).
- Mover não escreve de volta no Markdown (o Markdown segue como fallback de
  leitura; o estado operacional vive no SQLite).

## Regras respeitadas
Sem push · sem tela nova grande · sem mudar identidade visual · sem integração
externa · sem Missions · sem gerar criativo · Markdown/JSON intactos.
