# Safe Startup — Javis antigo

Data: 2026-07-08  
Estado: R2 aplicado, mas servidor ainda nao deve ser iniciado para uso operacional.

## O que pode rodar

- Leitura de codigo e documentacao.
- `python -m py_compile` em arquivos alterados.
- `scripts/safe_audit.ps1` para diagnostico local sem rede.
- Comandos Git locais de leitura/status.

## O que fica desabilitado por padrao

- Adaptadores externos.
- Codex CLI.
- Claude Code headless, incluindo raciocinio via `claude_brain.py`.
- Browser visivel, leitura web, Playwright e `browser-use`.
- Telegram long polling.
- MCP stdio/tool calls.
- Acoes locais de abrir app, pasta, terminal, VS Code, Open WebUI, sites, musica, reindexacao e escrita de ideias.
- Efeitos VP/Jampa em workflow, aprovacoes e rotas mutaveis.
- CORS wildcard.

## Flags

Todas sao `false` por padrao:

```text
JAVIS_ENABLE_EXTERNAL_ADAPTERS=false
JAVIS_ENABLE_CODEX_EXEC=false
JAVIS_ENABLE_CLAUDE_EXEC=false
JAVIS_ENABLE_BROWSER=false
JAVIS_ENABLE_TELEGRAM=false
JAVIS_ENABLE_MCP=false
JAVIS_ENABLE_LOCAL_ACTIONS=false
JAVIS_ENABLE_VP_EFFECTS=false
JAVIS_DEV_ALLOW_CORS=false
```

Observacoes:

- `JAVIS_ENABLE_EXTERNAL_ADAPTERS` e o kill-switch geral para provedores, browser, Telegram e MCP.
- Para ligar Codex, seriam necessarias `JAVIS_ENABLE_EXTERNAL_ADAPTERS=true` e `JAVIS_ENABLE_CODEX_EXEC=true`.
- Para ligar Claude Code headless, seriam necessarias `JAVIS_ENABLE_EXTERNAL_ADAPTERS=true` e `JAVIS_ENABLE_CLAUDE_EXEC=true`.
- Para ligar browser automation, seriam necessarias `JAVIS_ENABLE_EXTERNAL_ADAPTERS=true` e `JAVIS_ENABLE_BROWSER=true`.
- Para CORS wildcard, seria necessario `JAVIS_DEV_ALLOW_CORS=true`; nao usar como padrao.

## Comportamento esperado quando bloqueado

Rotas e modulos protegidos devem retornar:

```json
{
  "status": "disabled_by_default",
  "reason": "requires_explicit_enable"
}
```

## R1 — Gates por rota

Gate central: `_apps/javis-local-interface/backend/gate.py`.

Bloqueadas por padrao com `JAVIS_ENABLE_EXTERNAL_ADAPTERS=false`:

- `POST /knowledge/dna`
- `POST /knowledge/ingest`
- `POST /knowledge/reindex`
- `GET /knowledge/search`
- `POST /wa/analyze`
- `POST /upload`

Exigem `project_id=project:cerebro-jampa`:

- `POST /tasks/{id}/run-studio`
- `POST /tasks/{id}/prepare-distribution`
- `POST /tasks/{id}/status`
- `POST /tasks/{id}/complete`
- `POST /wa/analyze`
- `POST /wa/save-voice`
- mutacoes `POST/PATCH/DELETE /vp/*`
- mutacoes `POST /jampa/*`

Exigem aprovacao humana explicita nesta R1 (`approved=true`):

- `POST /knowledge/dna`
- `POST /knowledge/ingest`
- `POST /wa/save-voice`
- `POST /upload`

Validacoes:

- `/upload`: extensao permitida, bloqueio de scripts/executaveis, limite de tamanho e temp file somente dentro do repo.
- `/knowledge/ingest`: `folder` resolvido e bloqueado se tiver `..` ou sair de `JAVIS_ROOT`.
- auto-reindex/build/search de knowledge respeita `external_adapters`.
- contexto VP/Jampa nao entra no RAG global do Javis core sem escopo explicito.

Contrato de bloqueio:

```json
{
  "status": "blocked",
  "reason": "project_id_required",
  "scope": "project:cerebro-jampa"
}
```

```json
{
  "status": "approval_required",
  "reason": "human_approval_required"
}
```

R2 aplicado:

- `approved=true` nao libera mais execucao sozinho; rotas sensiveis usam aprovacao persistida em SQLite.
- rotas sensiveis exigem header local `X-Javes-Local-Token`.
- frontend Command Center e painel VP legado enviam `project_id=project:cerebro-jampa` para chamadas VP/Jampa/WA/tasks/conteudo conectado.
- rotas pendentes foram classificadas: `missions/*`, `history`, `brain/active`, `approvals/decide` e `/conteudo`.

## R2 — Approval persistido, auth local e project_id

Token local:

- header: `X-Javes-Local-Token`;
- fonte local: `JAVES_LOCAL_TOKEN` ou `JAVIS_LOCAL_TOKEN`;
- testes usam token fake controlado pelo `conftest.py`;
- o token nao e logado nem exibido.

Aprovacao persistida:

- tabela reutilizada: `approvals`;
- campos aditivos: `project_id`, `action`, `route`, `risk_level`, `requested_by`, `approved_by`, `approval_token_id`, `reason`, `metadata_json`, `updated_at`;
- status aceitos: `pending`, `approved`, `rejected`, `expired`, `canceled`;
- sem `approval_id` aprovado, a rota retorna `approval_required`;
- `approved=true` legado apenas cria/consulta gate pendente e retorna `approval_required`.

Rotas com auth local:

- `POST /knowledge/dna`
- `POST /knowledge/ingest`
- `POST /knowledge/reindex`
- `GET /knowledge/search`
- `POST /knowledge/graph/build`
- `POST /upload`
- `POST /wa/analyze`
- `POST /wa/save-voice`
- mutacoes `POST/PATCH/DELETE /vp/*`
- mutacoes `POST /jampa/*`
- `POST /tasks/{id}/run-studio`
- `POST /tasks/{id}/prepare-distribution`
- `POST /tasks/{id}/status`
- `POST /tasks/{id}/complete`
- `POST /approvals/{id}/decide`
- `GET /history/session`
- `GET /history`
- `DELETE /history`
- `POST /brain/active`
- `POST /missions/{mission_id}/nodes/{node_id}/done`
- `POST /conteudo`

Classificacao das rotas pendentes:

- `missions/*`: leitura `safe`; mutacao `auth_required + local_actions`.
- `history`: leitura `auth_required`; delete `auth_required + local_actions`.
- `brain/active`: GET `safe`; POST `auth_required + local_actions`.
- `approvals/decide`: `auth_required`; efeitos VP seguem protegidos por `vp_effects`.
- `/conteudo`: GET `safe`; POST `auth_required`; se projeto VP/Jampa, tambem `project_id_required + vp_effects`; caso contrario `local_actions`.

R3 pendente:

- RAG project-scoped real por `project_id`;
- UI explicita para cadastro/rotacao do token local;
- expiracao/TTL formal para approvals;
- auditoria de rotas de chat/voice/agents/train/browser antes de uso operacional.

## Riscos restantes

- Ainda nao ha UI dedicada para cadastrar/rotacionar o token local.
- Rotas amplas de chat/voice/agents/train/browser ainda precisam de revisao R3 antes de uso operacional.
- `_apps/javis-local-interface/iniciar-javis.bat` tambem inicia Chainlit; ainda nao deve ser usado.
- `.env` existe localmente e nao deve ser aberto.
- VP/Jampa ainda esta acoplado ao backend antigo, embora efeitos estejam bloqueados por flag.
- Runtime/caches/logs/lixo continuam na arvore por decisao da R1.

## Como testar sem executar acoes externas

1. Confirmar estado Git:

```powershell
git status -sb
```

2. Rodar diagnostico seguro:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/safe_audit.ps1
```

3. Compilar apenas os Python alterados:

```powershell
python -m py_compile _apps/javis-local-interface/backend/safe_config.py
python -m py_compile _apps/javis-local-interface/backend/server.py
```

4. Nao rodar:

```text
server.py
_run_server.py
javis-start.bat
iniciar-javis.bat
voice_bridge.py
telegram_bridge.py
code_agent.py
claude_exec.py
browser_agent.py
```

## O que falta antes de iniciar o servidor

- Implementar UI/politica operacional para token local.
- Auditar Chainlit/app_ui antes de usar `iniciar-javis.bat`.
- Classificar rotas restantes de chat/voice/agents/train/browser por risco: read-only, mutacao local, rede externa, execucao local.
- Separar ou isolar VP/Jampa do core Javis.
- Decidir politica de limpeza para caches/runtime/logs com aprovacao explicita.
- Rodar testes offline apenas depois da autenticacao e das flags serem revisadas.
