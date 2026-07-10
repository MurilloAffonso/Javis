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

`JAVIS_ENABLE_SUPERVISED_EXEC` — default **False**. Nesta fase, mesmo ligada,
nenhum agente roda (não há adapter). Ligar de verdade só faz sentido na R4.2.
