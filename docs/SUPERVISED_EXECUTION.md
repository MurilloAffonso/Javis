# Executor supervisionado — R4.1 (fundação)

Data: 2026-07-10

## Escopo desta fase

Esta é **apenas a fundação** do executor supervisionado. **Nenhum agente é
executado** aqui — Codex e Claude Code continuam desligados e o fluxo atual de
execução (`code_agent`/`claude_exec`/`brain_switch`) **não foi alterado**.

A R4.1 entrega três peças seguras e testáveis:

- `execution/execution_task.py` — modelo, identidade e máquina de estados;
- `execution/worktree_manager.py` — criação/validação/remoção de worktree Git isolada;
- `execution/execution_policy.py` — política default-deny de comandos (funções puras).

Adapters (Codex/Claude), consumo de approval persistido e result collector entram
na **R4.2**.

## Onde ficam as worktrees

**Fora** do repositório principal:

```
C:\Users\noteacer\Desktop\javis-worktrees\<task_id>
```

Nunca em `C:\Users\noteacer\Desktop\javis\_worktrees`. O root é derivado
(`<pasta-do-repo>/../javis-worktrees`) e pode ser trocado por variável de
ambiente `JAVIS_WORKTREE_ROOT` — **esta fase não lê `.env`**. A resolução usa
`Path.resolve()` + validação de prefixo; o `worktree_path` é **sempre**
reconstruído a partir do `task_id`, nunca do input do usuário.

## Estado do Git

Arquivos **untracked** (ex.: `Codex`, `Vem`, `_referencias/`, `fibonacci.py`,
`test_fibonacci.py`, `Sem título.canvas`) **não bloqueiam** a criação da worktree
e nunca são copiados. Bloqueiam:

- alteração rastreada não-staged (`git diff --quiet`);
- alteração staged (`git diff --cached --quiet`);
- merge/rebase/cherry-pick em andamento;
- HEAD inválido;
- `source_branch` inexistente (`git rev-parse --verify`).

Não se usa `git status --porcelain vazio`, que bloquearia pelos untracked conhecidos.

## Máquina de estados

```
draft → pending_approval → approved → preparing_workspace → running
      → testing → awaiting_review → approved_for_merge → merged → completed
```

Falhas: `blocked`, `failed`, `timed_out`, `canceled`, `review_rejected`.
Regras: transições só para a frente; `approved` exige `approval_id`;
`approved_for_merge` exige `merge_approval_id`; `merged` só vem de
`approved_for_merge`; `completed` só vem de `merged`; estados terminais não
avançam; idempotência só quando origem == destino. Nesta fase **apenas a
presença** dos ids de aprovação é validada — o consumo do approval persistido é R4.2.

## Política de comandos (default-deny)

Análise de **argv estruturado**, não regex em shell livre. `shell=False` sempre.

Permitidos (com paths validados dentro da worktree): `git status/diff/show`,
`git log` com limite, `git add <arquivos explícitos>`, `git commit`,
`python -m py_compile`, `python -m pytest`/`pytest` com testes declarados.

Bloqueados: `git push/fetch/pull/remote/reset/clean/branch -D`,
checkout/switch para master/main, flags force, `pip/npm/pnpm/yarn/poetry/uv`
install, `curl/wget/ssh/scp/nc`, PowerShell web, subir servidor, browser,
leitura de `.env`/arquivos com nome de token/chave/credencial, qualquer path
fora da worktree, encadeamento de shell e comandos desconhecidos.

## Segurança

- **Sem push** em nenhuma hipótese (bloqueado na policy e não implementado).
- Allowed repo roots = só o repo do Javes (nos testes, root temporário isolado).
- Branch segura `^javes/exec/exec_[a-f0-9]{8,64}$`; nunca master/main.
- `task_id` `^exec_[a-f0-9]{8,64}$`, gerado internamente.
- Comandos Git com lista de argumentos, timeout e stdout/stderr capturados;
  erros **sanitizados** (sem token/chave/credencial) antes de retornar/persistir.
- Worktree preservada em `failed`/`timed_out`/`review_rejected` para auditoria;
  remoção só dentro do worktree root e, em falha, só com limpeza aprovada.

## Doctor

`python scripts/javes_doctor.py --no-probe` passa a mostrar (só contagens/flags):
`supervised_execution_enabled` (False), `execution_schema_present`,
`active_execution_tasks`, `worktree_root_configured`, `active_worktrees`,
`orphan_worktrees`. **Nunca** imprime objective, stdout, stderr, diff ou paths
sensíveis completos.

## Flag

`JAVIS_ENABLE_SUPERVISED_EXEC` — default **False**. Na R4.2B, execução real só
deve ser ligada em ambiente controlado e explícito; merge continua fora do escopo.

---

# R4.2A — Gates de aprovação + coleta de resultados

Ainda **sem executar agente e sem fazer merge**. Adiciona os dois gates humanos e
a coleta segura de resultados sobre a fundação R4.1.

## Dois gates de aprovação (`execution/execution_approvals.py`)

- **Gate 1 — `execution.start`**: `request_execution_start` cria a aprovação
  (pending) e leva `draft → pending_approval`; `approve_execution_start` consome a
  aprovação (single-use) e leva `pending_approval → approved`.
- **Gate 2 — `execution.merge`**: `request_merge` cria uma aprovação **separada**;
  `approve_merge` consome e leva `awaiting_review → approved_for_merge` e preenche
  `merge_approval_id`. **Não faz merge** (isso é R4.2C).

Invariantes: a aprovação precisa estar amarrada à **mesma task e ao mesmo
`project_id`** (ação + `task_id` + `project_id` conferem); é **single-use**
(consumida via `repo.approvals.consume`); execução e merge usam aprovações
**diferentes**; o estado **não muda** sem aprovação válida.

## Coleta de resultados (`execution/result_collector.py`)

`ResultCollector.collect(task_id, project_id, worktree, stdout, stderr, test_report)`:
- **sanitiza** (token/Authorization/credencial-em-URL/segredo) e **trunca** stdout,
  stderr, diff e relatório de testes (tetos `MAX_STREAM_CHARS`/`MAX_DIFF_CHARS`);
- coleta `git status`, `git diff --stat`, diff completo (limitado) e a lista de
  arquivos alterados (validados como **dentro** da worktree);
- grava numa **raiz de resultados controlada, fora do repo**
  (`<desktop>/javis-exec-results/<task_id>`, override `JAVIS_EXEC_RESULTS_ROOT`),
  com o path reconstruído a partir do `task_id`;
- persiste `result_path`/`diff_path`/`test_report_path` na `execution_task`
  (filtrado por `task_id`+`project_id`) e devolve **só paths + contagens** — nunca
  conteúdo bruto ou segredo.

## Doctor (R4.2A)

Novas contagens (só números): `awaiting_execution_approval` (pending_approval),
`awaiting_review`, `awaiting_merge_approval` (approved_for_merge, aguardando o
merge da R4.2C) e `failed_execution_tasks` (failed + timed_out).

---

# R4.2B — Adapters supervisionados em worktree

A R4.2B conecta adapters supervisionados à fundação segura, mas a execução continua desligada por padrão por `JAVIS_ENABLE_SUPERVISED_EXEC=False`. Nenhum merge é implementado nesta fase.

## Fluxo

Quando a flag for injetada explicitamente em ambiente de teste/controlado, o serviço `execution/execution_service.py` conduz:

```
approved → preparing_workspace → running → testing → awaiting_review
```

O fluxo para obrigatoriamente em `awaiting_review`. `approved_for_merge`, merge real e Command Center ficam para a R4.2C.

## Adapters

`execution/executor_adapter.py` define um contrato comum:

- entrada: `task_id`, `project_id`, `objective`, `worktree_path`, `timeout_seconds`, `prompt_path`, `executor`;
- saída: `exit_code`, `status`, `stdout`, `stderr`, `timed_out`, `duration_ms`, `command_summary`.

`ClaudeCodeAdapter` roda apenas com ferramentas de leitura/edição/escrita (`Read,Edit,Write`) e não recebe Bash, browser, MCP ou diretórios externos. Os testes são executados pelo Javes depois, não pelo modelo.

`CodexAdapter` exige sandbox `workspace-write` verificado. Como `codex exec --help` não pôde ser inspecionado pelo allowlist local durante esta fase, o adapter falha fechado por padrão com `secure_codex_sandbox_unavailable` até que um help compatível seja injetado/verificado em ambiente controlado.

## Subprocesso e ambiente

`execution/process_utils.py` centraliza subprocesso com:

- `argv` estruturado e `shell=False`;
- `cwd` validado e fixo na worktree;
- timeout com kill da árvore de processos no Windows;
- remoção de `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` e correlatos;
- remoção de variáveis com token/chave/segredo;
- stdout/stderr sanitizados e truncados antes de persistir.

## Test Runner

`execution/test_runner.py` recebe lista explícita criada pela tarefa e permite somente:

- `python -m py_compile <arquivos explícitos>`;
- `python -m pytest -q <testes explícitos>`.

O runner aplica `execution_policy` antes de cada comando e bloqueia pytest sem alvo, flags arbitrárias, paths fora da worktree, instalação, rede e servidor.

## Evidência e estados finais

`result_collector` é chamado quando existe worktree válida, inclusive em falha. Worktrees são preservadas em `failed`, `timed_out`, `awaiting_review` e `review_rejected`. Estados finais desta fase: `awaiting_review`, `failed`, `timed_out` ou `blocked` por pré-condição.

## Doctor (R4.2B)

O doctor mostra somente contagens passivas: `supervised_adapters_present`, `executions_running`, `executions_testing`, `executions_timed_out`, `executions_awaiting_review`. Não mostra objective, prompt, stdout, stderr, diff nem paths completos.

## Caminhos antigos

`code_agent.py`, `claude_exec.py`, `orchestrator.py`, `brain_switch.py` e `delegacao.py` não foram conectados ao novo serviço. Continuam atrás das flags existentes e serão aposentados/conectados somente na R4.2C.
