# CURRENT STATE — Javes (FONTE CANÔNICA)

> **Este arquivo é a FONTE DE VERDADE do estado atual do Javes.**
> Ao responder sobre **estado atual**, **próximas fases**, **o que falta** ou
> **próximo passo**, este arquivo **prevalece** sobre qualquer roadmap antigo
> (`estado-atual.md`, `proximos-passos.md`, `_logs/` datados ou `git log`).
> Aqueles ficam como **histórico**; a decisão vigente é a daqui.

**Atualizado:** 2026-07-11
**Mantido por:** hardening arc (R1 → R4)

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

> **Executor continua DESLIGADO por padrão.** R4.1/R4.2A/R4.2B/R4.2C1/R4.2C2/R4.3A/R4.3B1/R4.3C/R4.3D1/R4.3D entregam fundacao + gates + adapters + merge local
> controlado + integracao supervisionada + CLI de smoke + fechamento com commit local controlado + CLI de revisao/merge + validacao real ponta a ponta: tarefas reais ainda nao sao liberadas de forma geral, o fluxo legado direto permanece desativado, e
> `JAVIS_ENABLE_SUPERVISED_EXEC` continua `False`.
---

## PROXIMO PASSO OFICIAL

**R4.4A — habilitação gradual de tarefas reais de programação pelo fluxo supervisionado**

Habilitar gradualmente tarefas reais mantendo allowlist, `project_id`, dois
approvals separados, worktree isolada, testes, revisão humana e merge local sem
push automático.
---

## Fases seguintes (ordem oficial)

1. **R4.4A — habilitação gradual do fluxo supervisionado** (proximo passo acima).

2. **R4.4B - Endurecimento adicional / sandbox opcional**
   Bloqueio de rede real (Docker `--network none` opcional, nunca default),
   limites de recurso e hardening extra do executor.

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
