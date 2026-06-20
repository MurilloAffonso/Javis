# Gate 2 → Distribuição + Gate 3 (modo seguro) — 20/06

Aprovar os criativos (Gate 2) destrava a etapa de Distribuição em MODO SEGURO:
prepara um pacote textual de publicação, salva em arquivo e cria o Gate 3 ANTES
de qualquer publicação. NÃO publica, NÃO conecta WhatsApp/Instagram/GMB.

## Regra de avanço do Gate 2 (`approval_effects.py`)
- Identificação (`is_gate2_criativos`): agent `estudio` + assunto "criativos da semana".
- **Aprovado** (`_advance_gate2`): marca a task de Design `gate_approved`; cria a
  task de Distribuição (SQLite) `[Distribuição] Preparar pacote de publicação da
  pauta aprovada` (agent midas, status pending, origem approval_id); loga
  `workflow_advance` + Journey `approval_approved`/`workflow_advanced`/
  `distribution_task_unlocked` (na task de Design). Idempotente: se a task de
  Distribuição já existe, não duplica.
- **Rejeitado** (`_reject_gate2`): NÃO cria Distribuição; Journey `approval_rejected`/
  `adjustment_required`; **Design volta pra pending** (disponível pra ajuste) +
  sinal em memories. Refatorei `_journey` pra receber `task_id` (Gate 1 e Gate 2
  ancoram em tasks diferentes).

## Endpoint criado
`POST /tasks/{task_id}/prepare-distribution` — roda a preparação na task de
Distribuição. Idempotente (409 se já existe).

## Arquivo gerado
`_projetos/cerebro-jampa/posts/distribuicao-semana.md` — TEMPLATE LOCAL que lê
`pauta-semana.md` + `criativos-semana.md`: calendário sugerido (dia/peça/canais/
horário), canais (Feed/Stories/WhatsApp Status/Google Meu Negócio), legenda final
+ CTA + melhor horário por peça, `[CONFIRMAR COM MURILLO]` e **checklist antes de
publicar**. Termina em "aguardando aprovação (Gate 3)".

## Journey Log (na task de Distribuição)
`agent_called` (midas) → `file_generated` (midas) → `approval_requested`.

## Gate 3 criado
subject "Aprovar distribuição antes de publicar", agent `midas`, status pending,
task_id = task de Distribuição. Aparece em `/approvals/pending` e no painel da UI.

## Arquivos alterados
- `backend/approval_effects.py`: Gate 2 (is_gate2_criativos, _advance_gate2,
  _reject_gate2); `_journey` agora recebe task_id.
- `backend/distribution.py` (novo): `preparar_distribuicao_vp`, `run_distribution`,
  `is_distribution_task`, template local.
- `backend/server.py`: endpoint `POST /tasks/{id}/prepare-distribution`.
- `frontend/app.js`: botão "📤 Preparar Distribuição" no card da task de
  Distribuição (pending/in_progress) + `runDistribution()` (toast "Distribuição
  preparada. Gate 3 aguardando aprovação." + refreshStats + loadApprovals).

## Testes (`tests/test_distribution.py`) — 107 → 112 passed
- aprovar Gate 2 cria task de Distribuição (pending, midas) + distribution_task_unlocked;
- rejeitar Gate 2 NÃO cria Distribuição + Design volta pra pending;
- preparar gera distribuicao-semana.md (calendário/canais/checklist/[CONFIRMAR]/Gate 3)
  + eventos agent_called/file_generated/approval_requested;
- cria Gate 3 (midas) e aparece em /approvals/pending; idempotente (1 só Gate 3);
- sem integração externa nem publicação (source check).

## Verificação ao vivo (Playwright)
Criei + aprovei o Gate 2 pelo endpoint → "Distribuição destravada (sem publicar)",
task de Distribuição criada. No Quadro: card com botão "📤 Preparar Distribuição";
ao rodar → Pendente → Em andamento (IN_PROGRESS, midas), Gate 3 criado (midas) e
visível em /approvals/pending. Estado restaurado depois. Screenshot:
`_logs/screenshots/distribuicao-gate3.jpeg`.

## Pendências (próximas fases)
- Aprovar o Gate 3 ainda NÃO publica nada (publicação real fica pra fase com
  plugin/integração, fora deste escopo) — é o próximo passo natural do workflow.
- Distribuição é template (lê pauta+criativos); enriquecer com o Midas (assinatura)
  quando houver cota.

## Regras respeitadas
Sem push · sem tela nova grande · sem mudar design · sem integração externa · sem
publicar · sem gerar imagem · sem Missions · SQLite fonte principal · Markdown/JSON
intactos.
