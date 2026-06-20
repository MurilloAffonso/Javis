# Gate 3 → pacote de publicação MANUAL + fim da campanha — 20/06

Aprovar a distribuição (Gate 3) gera o pacote FINAL de publicação MANUAL, fecha o
ciclo da campanha (conclui a task de Distribuição com digest) e NÃO publica nada.

## Regra de aprovação do Gate 3 (`approval_effects.py`)
- Identificação (`is_gate3_distribuicao`): agent `midas`/`distribuicao` + assunto
  "distribuição antes de publicar".
- **Aprovado** (`_advance_gate3`):
  1. Journey `approval_approved`;
  2. gera `pacote-publicacao-semana.md` (publicação MANUAL);
  3. Journey `file_generated` + `manual_publication_package_created`;
  4. `complete_task(task de Distribuição)` → status `completed` + `task_completed`
     + `entity_killed` + `ai_digest_created` + **digest** (reusa o lifecycle);
  5. log `workflow_advance`.
  Idempotente: task já encerrada → `already`.
- **Rejeitado** (`_reject_gate3`): NÃO gera pacote; Journey `approval_rejected` +
  `adjustment_required`; Distribuição **volta pra pending** (disponível pra ajuste)
  + sinal em memories.

## Arquivo gerado
`_projetos/cerebro-jampa/posts/pacote-publicacao-semana.md` — TEMPLATE LOCAL lendo
pauta+criativos+distribuição: resumo da campanha, lista final de peças, legenda
final + CTA + canal + horário por peça, **checklist manual antes de publicar**,
`[CONFIRMAR COM MURILLO]`, e o aviso destacado:
**"PUBLICAÇÃO MANUAL — nenhuma integração externa foi acionada."**

## Eventos Journey Log (na task de Distribuição)
`approval_approved` → `file_generated` → `manual_publication_package_created`
→ (lifecycle) `task_completed` → `entity_killed` → `ai_digest_created`.

## Digest / conclusão
A task de Distribuição é concluída via `task_lifecycle.complete_task` (mesmo fluxo
de morte/digest já existente) — status `completed`, `completed_at`/`killed_at`,
`digest_text` salvo. A campanha fica fechada com digest.

## Arquivos alterados
- `backend/approval_effects.py`: Gate 3 (`is_gate3_distribuicao`, `_advance_gate3`,
  `_reject_gate3`) + roteamento em `on_decided`.
- `backend/distribution.py`: `gerar_pacote_publicacao_manual_vp` +
  `_template_pacote_manual` + path `PACOTE`.
- (Sem endpoint novo: o Gate 3 usa o `POST /approvals/{id}/decide` existente.)
- (Sem UI nova: a aprovação flui pelo `decideApproval` — toast usa a `message` do
  efeito, e `renderQuadro` move o card pra Concluído/Morto com selo de digest.)

## Testes (`tests/test_gate3.py`) — 112 → 117 passed
- aprovar gera `pacote-publicacao-semana.md` (com aviso PUBLICAÇÃO MANUAL +
  checklist + [CONFIRMAR]) + eventos approval_approved/file_generated/
  manual_publication_package_created;
- aprovar conclui a task (completed + completed_at + digest) + entity_killed +
  ai_digest_created;
- rejeitar NÃO gera pacote + Distribuição volta pra pending;
- idempotência (2ª vez → already);
- sem integração externa nem publicação (source check).

## Verificação ao vivo (Playwright)
Criei + aprovei o Gate 3 pelo painel de aprovações → toast "Pacote manual de
publicação gerado. Campanha concluída com digest."; a task de Distribuição passou
de Em andamento → **Concluído/Morto** (COMPLETED, midas) com **selo de digest**; o
Gate 3 sumiu das pendentes. Estado restaurado depois. Screenshot:
`_logs/screenshots/gate3-campanha-fechada.jpeg`.

## Pipeline completo (do começo ao fim)
Pauta (Nova) → Gate 1 → Design/Estúdio (criativos) → Gate 2 → Distribuição (Midas)
→ Gate 3 → **pacote de publicação MANUAL + campanha concluída com digest**.
Tudo em modo seguro: nenhuma publicação, nenhuma integração externa, nenhuma imagem.

## Pendências (próximas fases)
- Publicação REAL (Instagram/WhatsApp/GMB) fica pra fase com plugin/integração —
  deliberadamente fora. O pacote é pra publicação manual.
- Os pacotes são template; enriquecer com os agentes (assinatura) quando houver cota.

## Regras respeitadas
Sem push · sem tela nova grande · sem mudar design · sem integração externa · sem
publicar · sem gerar imagem · sem Missions · SQLite fonte principal · Markdown/JSON
intactos.
