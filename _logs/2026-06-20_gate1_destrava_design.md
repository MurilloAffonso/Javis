# Gate 1 aprovada → destrava produção de criativos (modo seguro) — 20/06

Liga o avanço do workflow: aprovar a Gate 1 da pauta VP destrava a próxima etapa
(Design), SEM gerar criativo, SEM chamar a Nova, SEM integração externa.

## Regra de avanço do workflow
`POST /approvals/{id}/decide` → após persistir a decisão, chama
`approval_effects.on_decided(approval, approved, note)`:

- **Identificação da Gate 1**: `approval.agent == 'nova'` E o assunto contém
  "pauta da semana" ou "gate 1" (`is_gate1_pauta_vp`).
- **Se APROVADA** (`_advance`):
  1. dual-write Markdown: `mission_board.set_task_done(t1)` (marca a Gate no backlog);
  2. SQLite: `db_sync.sync_tasks()` re-espelha + `tasks.set_status(t1,'gate_approved')`;
  3. libera a task de Design — **ela já existe no pipeline (t2)**, então é LIBERADA
     (status pending), não duplicada (upsert por ext_id único = idempotente);
  4. log `workflow_advance` (agente estudio), com origem no approval_id.
- **Se REJEITADA** (`_reject`): log `workflow_reject` + memória "pauta aguardando
  ajuste". NÃO cria task de Design. NÃO apaga nada.
- **Idempotência**: re-decidir é bloqueado no endpoint (409); e `_advance` ainda
  checa se a gate já está `gate_approved` → retorna `already` sem re-logar/duplicar.

Decisão de engenharia: a task de Design "[Design] Produzir os criativos da pauta
aprovada" JÁ EXISTE no backlog (t2). O correto é LIBERÁ-LA (destravar a gate que a
precede), não criar uma duplicata. A origem (approval_id) fica rastreada no log
`workflow_advance` e no `source` da task no SQLite.

## Arquivos alterados
- **`backend/approval_effects.py`** (novo): a camada de efeitos (`on_decided`,
  `is_gate1_pauta_vp`, `_advance`, `_reject`).
- **`backend/server.py`**: o endpoint `/approvals/{id}/decide` agora chama
  `approval_effects.on_decided` e devolve `advanced` + `message` pra UI.
- **`frontend/app.js`**: `decideApproval` usa a `message` do backend ("Produção de
  criativos destravada."), e dá `renderQuadro()` se o Quadro estiver aberto.
- **`frontend/style.css`**: `.ap-effect` (linha verde do efeito no card resolvido).
- **`tests/test_approvals.py`**: +4 testes (ver abaixo).

## Testes
- `aprovar_gate1_libera_design`: aprovar → t2 pending, t1 gate_approved, log
  workflow_advance, mission_board chamado (mockado p/ não tocar o backlog real).
- `aprovar_gate1_idempotente`: aprovar 2x → Design não duplica, não re-loga.
- `rejeitar_gate1_nao_cria_design`: rejeitar → nenhum Design criado, log workflow_reject.
- `endpoint_gate1_destrava_e_loga`: pelo endpoint → action_logs com `approval_decide`
  E `workflow_advance`, Design pending, message de destrave.
- Suíte: **77 → 81 passed**.

## Verificação AO VIVO (servidor real, com restauração)
Reabri a Gate 1 (id=1) → aprovei via `POST /approvals/1/decide` no servidor:
- resposta `advanced:True`, "Gate 1 aprovada. Produção de criativos destravada.";
- backlog `- [x] [Gate 1` (dual-write Markdown OK);
- SQLite t1=`gate_approved`, t2(Design)=`pending`;
- log `workflow_advance` gravado; `/stats` approvals_pending 1→0.
- **Estado RESTAURADO**: backlog revertido + Gate 1 de volta a `pending` — pra o
  Murillo aprovar de verdade pela interface.

## Critérios — todos atendidos
Gate 1 aprovada → decisão registrada → task da pauta atualizada (gate_approved) →
task de Design liberada (pending) → Quadro atualizado (dual-write) → log
(workflow_advance) → /stats atualizado. Rejeição não cria Design. Idempotente.

## Pendências (próximas fases)
- O avanço PARA na liberação da task de Design (modo seguro): NÃO gera criativo
  nem chama a Nova/Estúdio automaticamente — isso é decisão futura do Murillo.
- `gate_approved` no SQLite pode ser normalizado p/ `done` num `sync_tasks` futuro
  (cosmético; o backlog Markdown marca [x] e o histórico fica no action_logs).

## Regras respeitadas
Sem push · sem tela nova · sem mudar design · sem integração externa · sem gerar
criativo · sem chamar /chat (cota) · JSON/Markdown intactos.
