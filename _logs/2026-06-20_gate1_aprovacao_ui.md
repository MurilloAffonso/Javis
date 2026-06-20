# Aprovação humana Gate 1 na interface — 20/06

Fecha o ciclo humano-no-loop: a aprovação que ficava só pendente no SQLite agora
é DECIDIDA pelo Murillo na interface (aprovar/rejeitar), persistindo a decisão.

## Backend
- **`migrations/schema.sql`** + **`db.py`**: tabela `approvals` ganhou `task_id` e
  `note`. Migração ADITIVA idempotente (`ALTER TABLE ADD COLUMN` no `init_db`, ignora
  se a coluna já existe) — funciona em DB novo E nos que já existiam.
- **`repositories.py`** (`_Approvals`): `add(..., task_id)`, `get(id)`,
  `decide(id, approved, note)`.
- **`server.py`**:
  - `GET /approvals/pending` → lista pendentes do SQLite (id, subject, agent,
    task_id, status, detail, created_at).
  - `POST /approvals/{id}/decide` body `{decision, note}` → valida, atualiza o
    status (`approved`/`rejected`) + `note` + `decided_at`, registra em
    `action_logs` (intent `approval_decide`), devolve `approvals_pending` novo.
    Recusa re-decidir (409) e decision inválido (400). NÃO chama integração
    externa, NÃO publica, NÃO envia WhatsApp — só registra.
- **`agent.py`** (`_fluxo_pauta_vp`): a aprovação Gate 1 criada já vincula
  `task_id` = a task t1 (Gate 1) do pipeline.

## UI (sem tela nova, sem mudar design)
- **`index.html`**: bloco `#approvals-box` no TOPO do painel CONVERSA (panel-chat),
  aparece só quando há pendência. (1ª tentativa foi no `activity-panel`, mas ele
  está colapsado/width:0 no layout do chat — movido pra CONVERSA, que é visível.)
- **`app.js`**: `loadApprovals()` (puxa /approvals/pending, render dos cards),
  `decideApproval(id, decision)` (POST decide, atualiza card + /stats + toast).
  Roda no init e a cada 30s. Cada card: assunto, agente, task, campo de observação
  e botões Aprovar (verde) / Rejeitar (vermelho).
- **`style.css`**: `.approvals-box/.ap-*` reaproveitando as variáveis de tema
  (âmbar pro alerta, verde/vermelho pros botões). Sem nova identidade visual.

## Testes (`tests/test_approvals.py`, DB temporário isolado)
1. listar pendentes · 2. aprovar (status+note+decided_at) · 3. rejeitar ·
4. approvals_pending diminui após decisão · 5. endpoint registra em action_logs
(intent approval_decide) + recusa re-decidir (409) · 6. decisão SEM chamada de
integração externa (checa o source do endpoint). Suíte: **71 → 77 passed**.

## Verificação ao vivo (Playwright)
- Bloco visível no topo da CONVERSA (379px), mostrando a Gate 1 real
  "Aprovar a pauta da semana… (Gate 1)", agente nova, com botões e campo de nota.
- Rejeitei uma aprovação de TESTE (id=2) pela UI com observação →
  `approvals_pending` 2→1, card resolvido, Gate 1 real permanece pendente.
- DB confirmou: id=2 `rejected`, note salva, decided_at preenchido; `action_logs`
  com `intent=approval_decide, status=rejected`.
- Contadores do topo reais via /stats: 4 msgs, 16 agentes.
- Screenshot: `_logs/screenshots/gate1-aprovacao-ui2.jpeg`.

## Critérios — todos atendidos
1. ✅ Pendente aparece na interface. 2. ✅ Aprovar muda status no SQLite.
3. ✅ Rejeitar muda status. 4. ✅ /stats atualiza approvals_pending.
5. ✅ action_logs registra a decisão. 6. ✅ Design preservado.
7. ✅ Sem integração externa. 8. ✅ Suíte passa (77).

## Pendente (próximas fases)
- Quando aprovar a Gate 1 de verdade, o fluxo ainda NÃO avança sozinho pra Raia
  de Design (a decisão é registrada; o avanço automático é passo futuro).
- Botão poderia recarregar o Quadro também (hoje recarrega /stats + a lista).

## Regras respeitadas
Sem push · sem dashboard novo · sem mudar identidade visual · sem integração
externa · JSON/Markdown intactos · SQLite compatível · sem forçar /chat (cota).
