# SQLite como camada de persistência — 20/06

Objetivo (Murillo): transformar mensagens, tarefas, logs, aprovações, agentes e
projetos em dados persistentes consultáveis — SEM reescrever o que existe.
SQLite entra como camada ADITIVA (dual-write), compatível com JSON/Markdown.

## Arquivos criados
- **`backend/db.py`** — conexão SQLite (`_data/javis.db`), `init_db()` idempotente
  (roda `migrations/schema.sql`), helpers `execute/query/query_one/count`. WAL ligado.
- **`backend/migrations/schema.sql`** — as 8 tabelas (tudo `IF NOT EXISTS`).
- **`backend/repositories.py`** — um repositório por entidade (messages, tasks,
  approvals, logs, agents, projects, workflows, memories), cada um com add/list/
  count. Tolerante a falha (o chamador não quebra se o banco der erro).
- **`backend/db_sync.py`** — `bootstrap()`: cria tabelas + faz seed (projetos,
  agentes dos rosters mente+vp, workflows) + espelha as tarefas do `mission_board`
  na tabela `tasks`. Idempotente, roda no boot. NÃO é fonte de verdade — só espelha.

## Tabelas criadas (8)
`projects`, `agents`, `workflows`, `tasks`, `messages`, `approvals`,
`action_logs`, `memories` (+ índices em created_at/status).

## Arquivos alterados (dual-write, sem quebrar nada)
- **`server.py`**:
  - `@app.on_event("startup")` chama `db_sync.bootstrap()`.
  - `chat()` e `chat_stream()` chamam `_persist_messages()` (grava user+assistant
    no SQLite além do `history_store`/JSON).
  - novo endpoint **`GET /stats`** (contadores reais: messages, agents, tasks,
    approvals_pending, projects).
- **`logger.py`**: além do JSONL, dual-write em `action_logs`.
- **`agent.py`** (`_fluxo_pauta_vp`): além de salvar a pauta e marcar o Quadro,
  agora grava no SQLite a task como `done` e cria a **APROVAÇÃO Gate 1 pendente**.
- **`frontend/index.html` + `app.js`**: contador "agentes" ganhou id; `refreshStats()`
  puxa `/stats` a cada 30s e substitui os valores fixos ("8 agentes") por reais.
  (Sem tela nova, sem mudar design — só os números viraram reais.)

## Endpoints conectados
- `GET /stats` → contadores reais (UI consome).
- Chat (`/chat`, `/chat/stream`) → grava em `messages`.
- Logger (todas as ações) → grava em `action_logs`.
- Fluxo da pauta → grava `tasks` (done) + `approvals` (Gate 1 pendente).

## Testes realizados
- `pytest tests/ -q` → **71 passed** (sem regressão).
- `bootstrap()` → 18 tasks espelhadas, 16 agentes, 2 projetos, 1 workflow.
- Aceitação do fluxo SEM gastar cota (Nova monkeypatchada — a cota da assinatura
  reseta 2h; a geração real da Nova já foi provada antes):
  - ✅ fluxo retorna com Gate 1; pauta salva (pauta real preservada via backup/restore).
  - ✅ Quadro: Raia 1 (t0) = `done` (mission_board E SQLite).
  - ✅ `approvals`: 0 → 1 pendente, subject "Aprovar a pauta… (Gate 1)", agent=nova.
  - ✅ `action_logs`: +1, intent=gerar_pauta_vp, agent=nova.
  - ✅ `messages`: dual-write grava user+assistant (testado via `_persist_messages`;
    o `/chat` real também já persistiu na chamada anterior).
  - ✅ `/stats` ao vivo: messages, agents=16, approvals_pending=1, tasks_done=12.

## Critérios de sucesso — todos atendidos
1. ✅ Fluxo "cria a pauta da semana" funciona. 2. ✅ Nova gera. 3. ✅ Task no Quadro.
4. ✅ Aprovação Gate 1 pendente no SQLite. 5. ✅ Log em action_logs.
6. ✅ Mensagens em messages. 7. ✅ Contadores da UI vêm de /stats. 8. ✅ Suíte passa.

## O que ficou pendente (próximas fases)
- `javis.db` é estado de runtime — NÃO commitado (regenerável por `bootstrap`);
  adicionar ao `.gitignore`.
- Quadro ainda LÊ do `mission_board` (Markdown), com o SQLite só espelhando.
  Migrar a leitura do Quadro pro SQLite é passo futuro (sem urgência; hoje espelha).
- Aprovar/rejeitar pela UI (botão que chama `approvals.decide`) — endpoint e tela
  ainda não feitos (a aprovação fica registrada e pendente; decisão é manual).
- `workflows`/`memories` têm tabela e repo, mas ainda pouco alimentados.
- Login/auth e demais tabelas de produto: fases seguintes do roadmap.

## Regras respeitadas
Sem push · sem tela nova · sem mudar design · sem integração externa (WhatsApp/
Gmail/Sheets/Instagram) · JSON/Markdown atuais intactos · SQLite aditivo/compatível.
