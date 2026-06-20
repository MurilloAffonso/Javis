# Estúdio em modo seguro + Gate 2 — 20/06

Quando a task de Design está liberada, o Estúdio produz um PACOTE TEXTUAL de
criativos, salva em arquivo, registra o Journey Log e cria o Gate 2 pra aprovação
do Murillo. MODO SEGURO: sem imagem, sem publicar, sem integração externa, sem LLM.

## Endpoint criado
`POST /tasks/{task_id}/run-studio` — roda o Estúdio na task de Design.
Idempotente (409 se criativos + Gate 2 já existem).

## Arquivo gerado
`_projetos/cerebro-jampa/posts/criativos-semana.md` — por TEMPLATE LOCAL que LÊ a
`pauta-semana.md` (heurística por '## POST', extrai pilar/formato/gancho/CTA) e
monta, por peça: ideia, headline, legenda (referência à pauta), CTA, briefing
visual e orientação story/reels. Toda peça visual marcada como
`[CONFIRMAR COM MURILLO]` (fotos/assets via plugin) + seção "Observações
pendentes". Termina em "Status: ... aguardando aprovação do Murillo (Gate 2)".

## Eventos Journey Log (ancorados na task de Design / t2)
`agent_called` (estudio) → `file_generated` (estudio) → `approval_requested`.

## Gate 2 criado
subject "Aprovar criativos da semana antes de publicar", agent `estudio`,
status pending, task_id = task de Design. Aparece em `/approvals/pending` e no
painel de aprovações da UI, igual ao Gate 1.

## Workflow (run_studio)
valida task de Design → marca `in_progress` → `agent_called` → gera+salva o
arquivo → `file_generated` → cria Gate 2 (se não houver pendente) →
`approval_requested` → action_log `gerar_criativos_vp`. Idempotente.

## Arquivos alterados
- **`backend/studio.py`** (novo): `gerar_criativos_vp`, `run_studio`,
  `is_design_task`, template local, parser da pauta.
- **`backend/server.py`**: endpoint `POST /tasks/{id}/run-studio`.
- **`frontend/app.js`**: botão "🎨 Rodar Estúdio" no card da task de Design
  (pending/in_progress) + `runStudio()` (POST → toast "Criativos gerados. Gate 2
  aguardando aprovação." → refreshStats + loadApprovals + renderQuadro).
- **`frontend/style.css`**: `.qcard-studio` (botão violeta discreto).

## Testes (`tests/test_studio.py`) — 102 → 107 passed
- gera `criativos-semana.md` (com [CONFIRMAR COM MURILLO] + Gate 2 no texto) +
  eventos agent_called/file_generated/approval_requested + task in_progress.
- cria Gate 2 pendente (agent=estudio, task_id=Design) e aparece em
  /approvals/pending.
- idempotência: 2ª execução recusada, 1 só Gate 2.
- recusa task que não é de Design.
- sem integração externa nem geração de imagem (source check).
(backup/restore do `criativos-semana.md` real nos testes.)

## Verificação ao vivo (Playwright)
Quadro: card de Design com botão "🎨 Rodar Estúdio"; ao rodar → task
Pendente → Em andamento (IN_PROGRESS, agent estudio), Gate 2 criado
(agent=estudio) e visível em /approvals/pending. Estado restaurado depois
(t2 pending, Gate 2 removido, criativos removido) — pra o Murillo rodar pela UI.
Screenshot: `_logs/screenshots/estudio-gate2.jpeg`.

## Pendências (próximas fases)
- Os criativos são template (lê a pauta); enriquecer com o agente Estúdio
  (assinatura) fica pra quando houver cota — a estrutura já está pronta.
- Geração de IMAGEM e PUBLICAÇÃO deliberadamente fora (próximas fases, com plugin).
- Aprovar o Gate 2 ainda não destrava a etapa seguinte (Distribuição) — análogo
  ao que o Gate 1 faz com o Design; é o próximo passo natural do workflow.

## Regras respeitadas
Sem push · sem tela nova grande · sem mudar design · sem integração externa · sem
publicar · sem gerar imagem · sem Missions · SQLite fonte principal · Markdown/JSON
intactos.
