# CURRENT STATE — Javes (FONTE CANÔNICA)

> **Este arquivo é a FONTE DE VERDADE do estado atual do Javes.**
> Ao responder sobre **estado atual**, **próximas fases**, **o que falta** ou
> **próximo passo**, este arquivo **prevalece** sobre qualquer roadmap antigo
> (`estado-atual.md`, `proximos-passos.md`, `_logs/` datados ou `git log`).
> Aqueles ficam como **histórico**; a decisão vigente é a daqui.

**Atualizado:** 2026-07-09
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

---

## 🎯 PRÓXIMO PASSO OFICIAL

**R3 — Sessões isoladas por `project_id`**

Histórico, escopo de RAG e approvals chaveados por `project_id` (`history_store.py` hoje é global).

---

## Fases seguintes (ordem oficial)

1. **R3 — Sessões isoladas por `project_id`**
   Histórico, escopo de RAG e approvals chaveados por `project_id`
   (`history_store.py` hoje é global). Impede vazamento de contexto entre
   `javes-core` e projetos externos (ex.: `cerebro-jampa`).

2. **R4 — Codex supervisionado em worktree/sandbox**
   Execução (`code_agent.py`/`claude_exec.py`) roda em **git worktree**
   descartável, não no repo vivo; merge só após aprovação. Codex como
   especialista atrás de approval + sandbox + auditoria Claude. Docker opcional,
   nunca default.

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
