# Safe Startup — Javis antigo

Data: 2026-07-08  
Estado: R1 aplicado, mas servidor ainda nao deve ser iniciado para uso operacional.

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

## Riscos restantes

- Ainda nao ha autenticacao local obrigatoria nas rotas sensiveis.
- Existem rotas de leitura/mutacao de memoria, tarefas, historico e knowledge que precisam de classificacao fina.
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

- Implementar autenticacao local simples nas rotas sensiveis.
- Auditar Chainlit/app_ui antes de usar `iniciar-javis.bat`.
- Classificar rotas restantes por risco: read-only, mutacao local, rede externa, execucao local.
- Separar ou isolar VP/Jampa do core Javis.
- Decidir politica de limpeza para caches/runtime/logs com aprovacao explicita.
- Rodar testes offline apenas depois da autenticacao e das flags serem revisadas.
