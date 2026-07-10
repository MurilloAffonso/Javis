# CURRENT STATE — Javes (FONTE CANÔNICA)

> **Este arquivo é a FONTE DE VERDADE do estado atual do Javes.**
> Ao responder sobre **estado atual**, **próximas fases**, **o que falta** ou
> **próximo passo**, este arquivo **prevalece** sobre qualquer roadmap antigo
> (`estado-atual.md`, `proximos-passos.md`, `_logs/` datados ou `git log`).
> Aqueles ficam como **histórico**; a decisão vigente é a daqui.

**Atualizado:** 2026-07-10
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

> **Executor ainda DESLIGADO.** A R4.1 é só fundação: nenhum agente é executado,
> o fluxo atual de execução não foi alterado, e `JAVIS_ENABLE_SUPERVISED_EXEC`
> continua `False`.

---

## 🎯 PRÓXIMO PASSO OFICIAL

**R4.2 — Adapters supervisionados + approval persistido + result collector**

`CodexAdapter`/`ClaudeCodeAdapter` sobre a fundação R4.1 (mesmo contrato), consumo
do approval persistido (2 gates: exec e merge) e `result_collector` com diff/test
report sanitizados. Nada roda no repo vivo — só na worktree isolada.

---

## Fases seguintes (ordem oficial)

1. **R4.2 — Adapters + approval persistido + result collector** (próximo passo acima).

2. **R4.3 — Endurecimento adicional / sandbox opcional**
   Bloqueio de rede real (Docker `--network none` opcional, nunca default),
   limites de recurso e hardening extra do executor.

3. **Integrações externas e canais**
   Browser, Telegram, WhatsApp, MCP e automações externas só depois da R4,
   sempre atrás de default-deny, approval e escopo explícito.

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
