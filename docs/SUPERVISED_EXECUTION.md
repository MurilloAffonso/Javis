# Executor supervisionado — R4.1 (fundação)

Data: 2026-07-11

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
merge da R4.2C1) e `failed_execution_tasks` (failed + timed_out).

---

# R4.2B — Adapters supervisionados em worktree

A R4.2B conecta adapters supervisionados à fundação segura, mas a execução continua desligada por padrão por `JAVIS_ENABLE_SUPERVISED_EXEC=False`. Nenhum merge é implementado nesta fase.

## Fluxo

Quando a flag for injetada explicitamente em ambiente de teste/controlado, o serviço `execution/execution_service.py` conduz:

```
approved → preparing_workspace → running → testing → awaiting_review
```

O fluxo para obrigatoriamente em `awaiting_review`. `approved_for_merge` alimenta o merge local da R4.2C1; integra??o com Command Center fica para a R4.2C2.

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

---

# R4.2C1 — Merge local controlado

A R4.2C1 adiciona `execution/merge_service.py` para integrar localmente uma `execution_task` em `approved_for_merge` à `source_branch` registrada. Não há integração com orchestrator, chat ou Command Center nesta fase.

## Pré-condições

O merge só roda quando:

- a task é carregada por `task_id` + `project_id`;
- `status == approved_for_merge`;
- `merge_approval_id` existe, pertence à mesma task/projeto, tem ação `execution.merge`, está aprovado e já foi consumido pelo gate persistido;
- `repository_path` passa pela allowlist do `WorktreeManager`;
- `work_branch` é uma branch `javes/exec/<task_id>` e nunca `master`/`main`;
- o repositório não tem mudanças rastreadas staged/unstaged nem operação Git em andamento;
- a worktree reconstruída pelo `task_id` existe e está na branch esperada;
- a `work_branch` tem pelo menos um commit novo sobre a `source_branch`.

## Proteção `source_commit`

`execution_tasks.source_commit` registra o HEAD da `source_branch` quando a workspace é preparada. Antes do merge, o serviço compara o HEAD atual da `source_branch` com esse valor. Se mudou, bloqueia com `source_branch_moved` e não tenta rebase, reset ou resolução automática.

## Merge

O serviço usa somente argv estruturado com `shell=False`:

```
git checkout <source_branch>
git merge --no-ff --no-edit <work_branch>
```

Nunca executa `push`, `force`, `reset --hard`, `clean`, `rebase`, squash automático ou merge em branch diferente da `source_branch` registrada.

## Estados e evidência

Em sucesso: `approved_for_merge → merged → completed`, relatório sanitizado via `result_collector`, e remoção da worktree somente após o merge concluído.

Em conflito: executa `git merge --abort`, preserva a worktree, registra `merge_conflict` sanitizado e marca `review_rejected`.

Em erro: preserva a worktree, registra erro sanitizado e marca `failed`.

## Doctor (R4.2C1)

O doctor mostra somente contagens: `approved_for_merge`, `merge_conflicts`, `completed_execution_tasks`, `preserved_worktrees`. Não mostra paths, diff, objective, stdout, stderr nem mensagens de erro.

## Próximo passo

R4.2C2 — integração segura com orchestrator e Command Center. R4 ainda não está concluída.
---

# R4.2C2 — Integração segura com Orchestrator e Command Center

A R4.2C2 conecta o fluxo supervisionado ao Javes sem execução automática. Pedidos
de programação deixam de chamar `brain_switch.dispatch`, `code_agent` ou
`claude_exec`; o Orchestrator cria uma `execution_task`, solicita o gate
`execution.start` e para em `pending_approval`.

## Fachada única

`execution/execution_facade.py` é o ponto único usado por API, Orchestrator e
Command Center. Toda operação exige `task_id` + `project_id`; string vazia nunca
significa “todos”. A fachada não recebe `repository_path`, `worktree_path` ou
branch vindos do frontend.

Operações expostas:

- criar/listar/consultar task;
- solicitar e consumir approval `execution.start`;
- iniciar execução somente via `ExecutionService`;
- solicitar e consumir approval `execution.merge`;
- chamar `ControlledMergeService`;
- cancelar estados permitidos sem apagar evidência;
- ler somente resumo/diff/testes sanitizados do `ResultCollector`.

## Orchestrator

Pedidos detectados como programação seguem:

```
pedido do usuário → execution_task draft → approval execution.start → pending_approval → parar
```

Não há chamada direta para Codex, Claude Code, `brain_switch.dispatch`,
`code_agent.dispatch` ou `claude_exec.dispatch`. `JAVIS_ENABLE_SUPERVISED_EXEC`
continua `False`; mesmo após approval, `/execution/tasks/{task_id}/start`
retorna `blocked/supervised_execution_disabled` até a flag ser habilitada em teste
controlado.

## API

Rotas supervisionadas:

- `GET /execution/tasks`
- `POST /execution/tasks`
- `GET /execution/tasks/{task_id}`
- `GET /execution/tasks/{task_id}/result`
- `POST /execution/tasks/{task_id}/request-start-approval`
- `POST /execution/tasks/{task_id}/approve-start`
- `POST /execution/tasks/{task_id}/start`
- `POST /execution/tasks/{task_id}/request-merge-approval`
- `POST /execution/tasks/{task_id}/approve-merge`
- `POST /execution/tasks/{task_id}/merge`
- `POST /execution/tasks/{task_id}/cancel`

Todas exigem token local e `project_id`. Outro projeto recebe bloqueio genérico
ou `not_found`, sem revelar objetivo, prompt, paths, stdout, stderr ou diff bruto.

## Command Center

A aba **Execução** mostra apenas dados sanitizados:

- `task_id` resumido, projeto, executor, status e datas;
- status dos approvals de execução/merge;
- status de testes e contagem de arquivos alterados;
- risco e ações permitidas pelo estado;
- resumo, diff sanitizado e relatório de testes via endpoint de resultado.

O botão **Executar** fica desabilitado enquanto
`JAVIS_ENABLE_SUPERVISED_EXEC=False`. O frontend não envia `repository_path`,
`worktree_path` ou branches.

## Doctor (R4.2C2)

Novas contagens passivas:

- `execution_api_present`
- `execution_command_center_present`
- `legacy_direct_execution_callers`
- `supervised_tasks_total`
- `pending_execution_approvals`
- `awaiting_review`
- `approved_for_merge`
- `completed_execution_tasks`

O doctor segue sem mostrar objective, prompt, diff, stdout, stderr ou paths
completos.

## Próximo passo

R4.3 — teste controlado do executor supervisionado e hardening. Modo Madrugada
somente depois de teste real controlado e aprovado. R4 ainda não está concluída.

---

# R4.3A — CLI para smoke test controlado

A R4.3A prepara um fluxo manual para o primeiro teste real do executor
supervisionado. Durante a implementação e validação desta fase, nenhum Codex real
e nenhum Claude Code real foram executados; os testes usam fakes/mocks.

## CLI

Entrada:

```
python scripts/javes_execution_smoke.py prepare --executor claude
python scripts/javes_execution_smoke.py approve-start --task-id <task_id> --approval-id <approval_id> --confirm "APROVAR TESTE CONTROLADO"
set JAVIS_ENABLE_SUPERVISED_EXEC=1
python scripts/javes_execution_smoke.py run --task-id <task_id> --confirm "EXECUTAR TESTE CONTROLADO"
python scripts/javes_execution_smoke.py status --task-id <task_id>
```

`project_id` fica fixo em `javes-core`. O objetivo é fixo e não aceita texto livre:
criar/atualizar somente `docs/EXECUTION_SMOKE_TEST.md` na worktree com o conteúdo
permitido do smoke test.

## Segurança

- timeout máximo de 300 segundos;
- somente uma task smoke ativa por vez;
- `approve-start` exige frase exata e consome approval `execution.start`;
- `run` exige `JAVIS_ENABLE_SUPERVISED_EXEC=1` no processo atual e frase exata;
- `run` recusa task sem approval consumido, task já executada e status diferente
  de `approved`;
- preflight valida schema, `CURRENT_STATE.md`, executor, repo limpo de alterações
  rastreadas, work branch segura e ausência de outro smoke em execução;
- não há merge, push, scheduler, browser, Telegram, MCP, WhatsApp ou Modo Madrugada;
- status mostra somente resumo sanitizado, contagem de arquivos e se a worktree
  está preservada, sem stdout/stderr bruto, segredos ou paths completos.

## Executor inicial

O primeiro teste real recomendado é com Claude Code. Claude continua limitado a
Read/Edit/Write, sem Bash. Codex continua preparado, mas falha fechado enquanto o
sandbox `workspace-write` não estiver validado explicitamente.

## Próximo passo

R4.3B — primeiro smoke test real manual com Claude Code. Modo Madrugada continua
bloqueado.

---

# R4.3B1 — Commit controlado e diff de arquivos novos

O primeiro smoke real com Claude Code alcançou `awaiting_review`, mas revelou que
arquivos novos permaneciam apenas untracked na worktree: `git diff --stat` ficava
vazio, `HEAD` não avançava e `.javes_execution_prompt.txt` aparecia como artefato
interno.

## Fechamento correto

Após o adapter editar e os testes passarem, `execution/execution_service.py` segue:

```
running → testing → testes aprovados → remover prompt temporário
→ commit local controlado → result_collector → awaiting_review
```

`awaiting_review` só é alcançado quando existe commit novo na `work_branch`,
`HEAD != source_commit` e o `ResultCollector` consegue coletar diff sanitizado.

## Commit local controlado

`execution/commit_service.py` coleta alterações válidas com:

- `git diff --name-only`;
- `git diff --cached --name-only`;
- `git ls-files --others --exclude-standard`.

Cada arquivo é validado como relativo, dentro da worktree, não ignorado e não
sensível. O stage usa somente:

```
git add -- <arquivo explícito>
```

Nunca usa `git add .`, `git add -A`, `git add --all`, merge ou push. A mensagem
do commit é fixa:

```
javes(<task_id>): resultado da execução supervisionada
```

## Artefatos internos

`.javes_execution_prompt.txt` é reconstruído dentro da worktree e removido após o
adapter terminar, inclusive em falha/timeout. Ele não entra no diff, na contagem
de arquivos, no stage, no commit nem chega à master.

## ResultCollector

Quando há `source_commit`, o pacote de revisão usa:

```
git diff --stat <source_commit>..HEAD
git diff <source_commit>..HEAD
```

Assim arquivos originalmente untracked entram no diff e no diff stat depois do
commit local controlado. Conteúdo e paths continuam sanitizados/truncados.

## Doctor

Novas contagens passivas:

- `awaiting_review_without_commit`;
- `internal_prompt_artifacts`;
- `execution_commits_ready`.

O Doctor não mostra paths completos, conteúdo, prompt, diff bruto ou hash completo.

## Próximo passo

Repetir o smoke real com uma nova task. Modo Madrugada continua bloqueado.

---

# R4.3C — CLI de revisão e merge controlado do smoke

A R4.3C fecha o ciclo manual de revisão do smoke sem executar Codex ou Claude e
sem habilitar `JAVIS_ENABLE_SUPERVISED_EXEC`. Os comandos usam a
`ExecutionFacade`, o gate persistido `execution.merge` e o
`ControlledMergeService`; nenhum deles faz push.

## CLI

```text
python scripts/javes_execution_smoke.py request-merge --task-id <task_id>
python scripts/javes_execution_smoke.py approve-merge --task-id <task_id> --approval-id <approval_id> --confirm "APROVAR MERGE CONTROLADO"
python scripts/javes_execution_smoke.py merge --task-id <task_id> --confirm "EXECUTAR MERGE CONTROLADO"
```

O `project_id` é sempre `javes-core` e não pode ser informado pelo operador.

## Revisão e aprovação

`request-merge` aceita somente task smoke em `awaiting_review`, exige evidência
persistida de testes aprovados, worktree limpa e sem untracked, branch esperada,
`source_commit` válido e pelo menos um commit novo. Em seguida cria um approval
novo de ação `execution.merge`, retorna seu id e para sem merge.

`approve-merge` exige a frase exata, valida `task_id + project_id + action`,
impede o reuso do approval `execution.start`, decide o approval persistido e o
consome uma única vez pelo gate existente. A única transição é
`awaiting_review → approved_for_merge`; nenhum merge ocorre nesse comando.

## Merge controlado

`merge` exige a frase exata e `approved_for_merge`, então delega exclusivamente
ao `ControlledMergeService`. O serviço recusa:

- `source_commit` ausente, inválido ou diferente do HEAD atual da source branch;
- repositório principal ou worktree com alterações staged/unstaged, untracked
  ou operação Git em andamento;
- worktree/branch fora do escopo da task ou sem commit novo;
- approval de merge ausente, incorreto ou não consumido.

Em sucesso, o fluxo é `approved_for_merge → merged → completed`, o relatório e
os resultados persistidos são preservados, somente a worktree reconstruída a
partir do `task_id` é removida e a resposta contém apenas status e commit final,
sem paths sensíveis. Em conflito, o merge é abortado e worktree/evidências são
preservadas para revisão. Todos os subprocessos Git usam argv estruturado,
`shell=False`, e não existe chamada a `push`.

## Validação

Os testes usam apenas repositórios e worktrees temporários. Não executam agentes,
providers, servidor ou rede e mantêm `JAVIS_ENABLE_SUPERVISED_EXEC=False`.

## Próximo passo

R4.3D — executar o primeiro merge real controlado e validar o ciclo completo.

---

# R4.3D1 — Preflight de source e encerramento de task obsoleta

A R4.3D1 separa as regras de limpeza do repositório principal e da worktree da
task. Arquivos untracked preexistentes na source não bloqueiam o merge e não são
adicionados, modificados ou removidos. A source continua bloqueada por alterações
rastreadas staged/unstaged, operação Git em andamento ou HEAD inválido.

Na worktree da task, o preflight exige limpeza completa: alterações rastreadas
staged/unstaged bloqueiam e untracked são detectados explicitamente com:

```text
git ls-files --others --exclude-standard
```

A comparação `HEAD(source_branch) == source_commit` ocorre antes das demais
checagens de limpeza. Divergência retorna `source_branch_moved` sem tentar merge,
rebase, reset, cherry-pick ou qualquer atualização automática da task.

## Rejeição de merge já aprovado

```text
python scripts/javes_execution_smoke.py reject-merge --task-id <task_id> --confirm "REJEITAR MERGE CONTROLADO"
```

O comando aceita somente `javes-core` em `approved_for_merge`, valida a frase
exata e faz `approved_for_merge → review_rejected` pela máquina de estados. A
worktree, o commit, os resultados, o diff, os testes e o approval anterior são
preservados. O evento `smoke_merge_rejected` é append-only; repetir o comando em
`review_rejected` é idempotente e não duplica o evento. Nenhum Git, agente, rede,
merge ou push é executado por esse comando.

---

# R4.3D — Ciclo supervisionado completo (CONCLUÍDA)

A validação real ponta a ponta foi concluída com sucesso no projeto
`javes-core`, comprovando o ciclo de execução, revisão e integração local sob os
guardrails supervisionados.

## Evidência da execução real

- task: `exec_9b862b81208042f6`;
- executor: `claude`;
- approval de início: `16`;
- approval separado de merge: `17`;
- status final: `completed`;
- testes: `passed`;
- `changed_files_count`: `1`;
- arquivo integrado: `docs/EXECUTION_SMOKE_TEST.md`;
- commit final da master:
  `eddb430f4f1ac1c6aa34fdaa5c272ce4d73ca29a`.

## Invariantes confirmadas

- os approvals de início e merge foram distintos;
- a worktree da task foi removida somente após o merge bem-sucedido e a
  transição para `completed`;
- resultados, diff e relatório de testes permaneceram preservados;
- arquivos untracked preexistentes da master permaneceram intactos e não foram
  incluídos no merge;
- nenhum push foi realizado;
- tasks rejeitadas e suas worktrees permaneceram preservadas para auditoria.

## Resultado

**R4.3D — CONCLUÍDA.** O ciclo supervisionado real foi validado de ponta a ponta:
task escopada por `project_id`, executor em worktree isolada, approval de início,
testes, revisão, approval separado de merge, integração local controlada e
conclusão sem push automático.

## Próximo passo

R4.4A — habilitação gradual de tarefas reais de programação pelo fluxo
supervisionado, mantendo allowlist, `project_id`, dois approvals, worktree
isolada, testes, revisão e merge local sem push automático.

---

# R4.4A — Admissão segura de tarefas reais de programação

A R4.4A substitui o objetivo fixo do smoke por uma especificação JSON estrita,
mas limita esta fase à admissão. Nenhuma tarefa real, agente, worktree ou merge é
executado. O fluxo existente de execução, revisão e merge permanece inalterado.

## CLI

```text
python scripts/javes_programming_task.py validate --spec <arquivo.json>
python scripts/javes_programming_task.py prepare --spec <arquivo.json>
```

`validate` é livre de efeitos persistentes: não inicializa SQLite, não cria task,
approval ou worktree e retorna somente metadados sanitizados e o hash da spec.

`prepare` valida novamente e exige `JAVIS_ENABLE_REAL_PROGRAMMING_TASKS=True`.
Com a flag desligada, retorna `blocked/real_programming_tasks_disabled` sem criar
o banco. Quando habilitado explicitamente, cria uma `execution_task` em
`pending_approval`, persiste snapshot canônico imutável e solicita um approval
`execution.start` vinculado a `task_id + project_id + executor + spec_hash`.

## Política fail-closed

- registro confiável inicial: somente `javes-core`, apontando internamente para o
  repositório Javes e para a source branch controlada;
- executores: somente `claude` ou `codex`;
- perfis internos: `docs_only` e `safe_python`; a spec nunca fornece comandos;
- limites máximos: 300 segundos, 5 arquivos alterados e 300 linhas de diff;
- paths relativos obrigatórios, com bloqueio de absoluto/drive/UNC/traversal,
  symlink externo, `.git`, `.env*`, segredos, SQLite, `_data`, worktrees,
  evidências, `node_modules`, `.venv` e `__pycache__`;
- uma task real ativa por `project_id`; tasks smoke não possuem snapshot R4.4A e
  continuam independentes;
- hash SHA-256 sobre JSON canônico validado; snapshot é INSERT-only e toda leitura
  operacional continua escopada por `task_id + project_id`.

As flags `JAVIS_ENABLE_REAL_PROGRAMMING_TASKS` e
`JAVIS_ENABLE_SUPERVISED_EXEC` são independentes e permanecem `False` por padrão.
Preparar uma task não cria worktree nem chama adapters.

**R4.4A — admissão segura implementada.**

## Próximo passo

R4.4B — executar uma primeira tarefa real de baixo risco, limitada a
documentação, usando dois approvals e merge controlado.
