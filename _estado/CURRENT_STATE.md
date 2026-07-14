# CURRENT STATE — Javes (FONTE CANÔNICA)

> **Este arquivo é a FONTE DE VERDADE do estado atual do Javes.**
> Ao responder sobre **estado atual**, **próximas fases**, **o que falta** ou
> **próximo passo**, este arquivo **prevalece** sobre qualquer roadmap antigo
> (`estado-atual.md`, `proximos-passos.md`, `_logs/` datados ou `git log`).
> Aqueles ficam como **histórico**; a decisão vigente é a daqui.

**Atualizado:** 2026-07-14
**Mantido por:** hardening arc (R1 → R4.4B2 concluído)

---

## Estado das fases

| Fase | Descrição | Status |
|------|-----------|--------|
| **R1** | Gates por rota (default-deny, `project_id`, aprovação) | ✅ **Concluído** |
| **R2** | Token local + approval persistido em SQLite | ✅ **Concluído** |
| **R2.1** | Provider fallback + modo local (`JAVES_PROVIDER_MODE`), fix `project_id` | ✅ **Concluído** |
| **R2.2** | Consolidação de estado / hardening intermediário | ✅ **Concluído** |
| **R2.2.1** | Fonte canônica de estado (este arquivo) + priorização | ✅ **Concluído** |
| **R2.3** | Provider Registry + classificação de falhas + cooldown + `javes doctor` | ✅ **Concluído** |
| **R3** | Sessões, histórico e memória isolados por `project_id` | ✅ **Concluído** |
| **R3.1** | Fechamento do escopo: tasks/approvals sempre por `project_id` + estado interno fora do prompt do Jampa | ✅ **Concluído** |
| **R4.1** | Fundação do executor supervisionado: `execution_task` + `worktree_manager` + `execution_policy` (nenhum agente roda) | ✅ **Concluído** |
| **R4.2A** | Dois gates de aprovação (`execution.start`/`execution.merge`, single-use, escopados) + `result_collector` sanitizado/truncado (sem adapters, sem merge) | ✅ **Concluído** |
| **R4.2B** | Adapters supervisionados (`CodexAdapter`/`ClaudeCodeAdapter`) + `execution_service` até `awaiting_review` (sem merge) | ✅ **Concluído** |
| **R4.2C1** | Merge local controlado apos segundo approval persistido, com protecao `source_commit` (sem chat/orchestrator/Command Center) | Concluido |
| **R4.2C2** | Integracao segura com Orchestrator e Command Center: cria `execution_task`, solicita approval e para sem execucao automatica | Concluido |
| **R4.3A** | CLI para smoke test controlado do executor supervisionado, sem executar agente real durante a implementacao | Concluido |
| **R4.3B1** | Correcao do fechamento da execucao: remove prompt interno, cria commit local controlado e coleta diff de arquivos novos | Concluido |
| **R4.3C** | CLI de revisao e merge controlado do smoke com gate `execution.merge`, approval single-use e `ControlledMergeService` | Concluido |
| **R4.3D1** | Preflight separado para source/worktree, prioridade para `source_branch_moved` e `reject-merge` idempotente | Concluido |
| **R4.3D** | Ciclo supervisionado real validado ponta a ponta, com dois approvals, testes, revisão, merge local e conclusão sem push | ✅ **Concluído** |
| **R4.4A** | Admissão segura de tarefas reais por spec estrita, allowlists, limites, snapshot imutável e approval vinculado ao hash, sem execução | ✅ **Concluído** |
| **R4.4B1** | Fluxo supervisionado de tasks reais com enforcement pós-execução, dois approvals, commit e merge controlados, validado apenas em ambientes temporários | ✅ **Concluído** |
| **R4.4B2** | Primeira task real `docs_only` executada end-to-end: dois approvals single-use, worktree isolada, testes, commit automático, merge local sem push | ✅ **Concluído** |
| **R4.4C-1** | Limites de recurso do executor via Windows Job Object (memória/CPU/nº processos, `KILL_ON_JOB_CLOSE`), sempre ligado, best-effort se pywin32 indisponível | ✅ **Concluído** |
| **R4.4C-2** | Job Object também na fase de testes (onde código do agente executa) + correção do perfil `safe_python`, que estava morto por argv fora da allowlist | ✅ **Concluído** |
| **R4.5** | Modo Madrugada: executa desassistida UMA task que o humano já aprovou acordado, para em `awaiting_review` e só pede o approval de merge; janela, kill switch e três flags, todos fail-closed | ✅ **Concluído** |

> **Executor supervisionado OPERACIONAL.** R4.4B2 provou o fluxo com tarefa real; R4.4C-1 e C-2 puseram teto de recurso no adapter E na fase de testes.
> **Modo Madrugada não fura os gates:** ela só reusa o `run` do fluxo R4.4B e é incapaz de rodar task que não esteja em `approved` — estado que só o humano cria, consumindo approval single-use amarrado ao `spec_hash`. Merge continua humano, de manhã. Ver `_logs/2026-07-14_R4.5_modo-madrugada.md`.
> **Uma task por noite, por desenho:** o executor só admite uma task real ativa por vez, e duas tasks da mesma noite sairiam do mesmo `source_commit` — mergear a primeira deixaria as outras em `source_branch_moved`, inmergeáveis.
> **Docker `--network none` avaliado e adiado** — ganho marginal sobre allowlist + validação pós-execução + Job Object; impossível na fase do agente (precisa da API). Ver `_logs/2026-07-14_R4.4C-2_bug-safe-python-e-sandbox-nos-testes.md`.
---

## PROXIMO PASSO OFICIAL

**Primeira noite real da Madrugada**

Preparar uma task `docs_only`, aprovar acordado (`approve-start`), armar a
Madrugada e revisar o diff de manhã. Só depois considerar `safe_python`.

    python scripts/javes_madrugada.py preflight
    python scripts/javes_madrugada.py run --confirm "ARMAR MADRUGADA"
    python scripts/javes_madrugada.py off     # aborta a noite

Exige os três flags ligados (`JAVIS_ENABLE_NIGHT_MODE`,
`JAVIS_ENABLE_SUPERVISED_EXEC`, `JAVIS_ENABLE_REAL_PROGRAMMING_TASKS`).
Depois disso: canais externos (browser, Telegram, WhatsApp, MCP).
---

## Fases seguintes (ordem oficial)

3. **Modo Madrugada e integracoes externas/canais**
   Modo Madrugada somente depois da R4.3 e testes controlados; browser,
   Telegram, WhatsApp, MCP e automacoes externas so depois da R4,
   sempre atras de default-deny, approval e escopo explicito.
---

## Invariantes preservadas (não regridem)

- `javis` como runtime; `cerebro-murilo` como constituição; Python/FastAPI.
- Local-first; default-deny; adaptadores externos **off** por padrão.
- `project_id` obrigatório em rotas VP/Jampa; default `javes-core` normalizado.
- Logs append-only; aprovação humana; `.env`/token/chave nunca abertos nem impressos.

---

## O que NÃO está no escopo

- Não implementar OpenClaw (só referência arquitetural — ver plano de análise).
- Não alterar a stack Python/FastAPI do Javes.
