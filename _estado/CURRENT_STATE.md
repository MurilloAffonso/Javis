# CURRENT STATE — Javes (FONTE CANÔNICA)

> **Este arquivo é a FONTE DE VERDADE do estado atual do Javes.**
> Ao responder sobre **estado atual**, **próximas fases**, **o que falta** ou
> **próximo passo**, este arquivo **prevalece** sobre qualquer roadmap antigo
> (`estado-atual.md`, `proximos-passos.md`, `_logs/` datados ou `git log`).
> Aqueles ficam como **histórico**; a decisão vigente é a daqui.

**Atualizado:** 2026-07-14
**Mantido por:** hardening arc (R1 → R5.1 concluído)

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
| **R5.1** | Canais externos auditados: browser com aprovação amarrada ao `payload_hash`, MCP gateado por approval persistido e hash canônico de `tool + arguments`, Telegram aprovado como daemon por allowlist de `chat_id` + filtro de intent | ✅ **Concluído** |
| **R5.2** | Painel da Madrugada no Command Center: preflight read-only + kill switch (`GET /madrugada/status`, `POST /madrugada/kill-switch`), sem botão de executar (rodar continua só no CLI, por design); fix de TDZ circular no `exec.js` que quebrava a interface inteira | ✅ **Concluído** |

> **Executor supervisionado OPERACIONAL.** R4.4B2 provou o fluxo com tarefa real; R4.4C-1 e C-2 puseram teto de recurso no adapter E na fase de testes.
> **Modo Madrugada não fura os gates:** ela só reusa o `run` do fluxo R4.4B e é incapaz de rodar task que não esteja em `approved` — estado que só o humano cria, consumindo approval single-use amarrado ao `spec_hash`. Merge continua humano, de manhã. Ver `_logs/2026-07-14_R4.5_modo-madrugada.md`.
> **Uma task por noite, por desenho:** o executor só admite uma task real ativa por vez, e duas tasks da mesma noite sairiam do mesmo `source_commit` — mergear a primeira deixaria as outras em `source_branch_moved`, inmergeáveis.
> **Canais externos auditados:** browser e MCP agora validam *o que* foi aprovado, não apenas que existe approval; Telegram permanece fora de rota HTTP direta, limitado por allowlist de `chat_id` e intent filtering. Ver `_logs/2026-07-14_R5.1_browser-approval-binding.md` e `_logs/2026-07-14_R5.1_audit-telegram-mcp.md`.
> **Madrugada tem UI:** painel read-only no Command Center (aba "Madrugada") mostra preflight ao vivo e oferece o kill switch; rodar continua só no CLI, por design. Ver `_logs/2026-07-14_R5.2_ui-madrugada.md`.
> **Primeira noite real feita (14/07):** task `docs_only` executada desassistida ponta a ponta, parou em `awaiting_review`. Na revisão humana o conteúdo do agente saiu parcialmente alucinado (Telegram descrito errado, funções/colunas inexistentes) e a task caiu em `source_branch_moved` — foi rejeitada. O ciclo mecânico funcionou; o gate de revisão pegou o problema de mérito, que é pra isso que ele existe.
> **Docker `--network none` avaliado e adiado** — ganho marginal sobre allowlist + validação pós-execução + Job Object; impossível na fase do agente (precisa da API). Ver `_logs/2026-07-14_R4.4C-2_bug-safe-python-e-sandbox-nos-testes.md`.
---

## PROXIMO PASSO OFICIAL

**WhatsApp — 4º canal externo (do zero, com `payload_hash` desde o começo)**

Executor supervisionado + Madrugada + browser/MCP/Telegram auditados estão
fechados. O próximo marco de capacidade é o canal WhatsApp (OpenWA), atrás de
default-deny, token local, escopo e approval amarrada ao payload (destino +
mensagem) — o mesmo padrão de R5.1, agora aplicado desde o desenho.

Madrugada continua disponível a qualquer momento:

    python scripts/javes_madrugada.py preflight
    python scripts/javes_madrugada.py run --confirm "ARMAR MADRUGADA"
    python scripts/javes_madrugada.py off     # aborta a noite

Exige os três flags (`JAVIS_ENABLE_NIGHT_MODE`, `JAVIS_ENABLE_SUPERVISED_EXEC`,
`JAVIS_ENABLE_REAL_PROGRAMMING_TASKS`).
---

## Fases seguintes (ordem oficial)

4. **Novos canais externos**
   WhatsApp (próximo), browser ampliado, MCP ampliado e automações externas só
   entram atrás de default-deny, approval escopado e hash do payload autorizado.
5. **Madrugada no painel de Operação**
   Integrar o preflight da Madrugada ao painel de Operação (hoje é aba separada),
   junto das aprovações pendentes.
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
