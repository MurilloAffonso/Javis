# Auditoria R1 — Hardening inicial do startup do Javis antigo

Data: 2026-07-08  
Branch: `hardening/r1-safe-startup`  
Escopo: preparar o Javis antigo para organizacao segura, sem iniciar servidor, agentes, Codex, Claude, Telegram, MCP ou browser automation.

## Entrada principal real

- `javis-start.bat`: launcher raiz; antes ligava `JAVIS_AUTO_CODEX=1` e `JAVIS_VOICE_BRAIN=openrouter`; agora define flags seguras como `false` e `JAVIS_AUTO_CODEX=0`.
- `_apps/javis-local-interface/iniciar-javis.bat`: launcher legado que inicia backend e Chainlit; nao foi executado.
- `_apps/javis-local-interface/backend/_run_server.py`: launcher uvicorn seguro em `127.0.0.1:8000`, `reload=False`.
- `_apps/javis-local-interface/backend/server.py`: app FastAPI real. O bloco `__main__` foi restringido para `127.0.0.1`, `reload=False`.

## Modulos que podem iniciar servicos externos

- `server.py`: startup antes tentava iniciar Telegram, lembretes, indexacao e pre-aquecimento TTS; Telegram e TTS externo agora ficam inertes por flags.
- `telegram_bridge.py`: long polling via API Telegram; agora `start_background()` retorna `False` se `JAVIS_ENABLE_TELEGRAM` nao estiver ativo.
- `mcp_client.py`: conecta servidores MCP por stdio/subprocesso; `list_tools` e `call_tool` agora exigem `JAVIS_ENABLE_MCP`.
- `browser_agent.py`: opera sites reais via `browser-use` e OpenRouter; exige `JAVIS_ENABLE_BROWSER`.
- `browser.py`: busca/le paginas e pode usar Playwright ou abrir navegador; exige `JAVIS_ENABLE_BROWSER`.
- `llm_providers.py`, `agent.py`, `claude_brain.py`: provedores LLM/headless; exigem `JAVIS_ENABLE_EXTERNAL_ADAPTERS` e, no caso do Claude Code headless, `JAVIS_ENABLE_CLAUDE_EXEC`.
- `code_agent.py`: Codex CLI em background; exige `JAVIS_ENABLE_CODEX_EXEC`.
- `claude_exec.py`: Claude Code headless com permissao de edicao; exige `JAVIS_ENABLE_CLAUDE_EXEC`.

## Rotas sensiveis

- Execucao/raciocinio externo:
  - `POST /chat`
  - `POST /chat/stream`
  - `POST /voice`
  - `POST /voice/stream`
  - `POST /v1/chat/completions`
  - `POST /debate`
  - `POST /rootcause`
  - `POST /agents/run`
  - `POST /vp/agents/run`
- Browser/MCP/treino externo:
  - `POST /browser/run`
  - `GET /mcp/{server_id}/tools`
  - `POST /mcp/{server_id}/call`
  - `POST /transcribe`
  - `POST /train/youtube`
  - `POST /treinamento/resumir/{area}`
  - `POST /pulso`
- Mutacoes locais/VP/Jampa:
  - `POST/PATCH/DELETE /vp/*`
  - `POST /jampa/squad`
  - `POST /jampa/responder-lead`
  - `POST /jampa/forjar-skill`
  - `POST /conteudo`
  - `POST /brain/active`
  - `POST /approvals/{approval_id}/decide` (a decisao ainda registra; efeitos VP sao bloqueados por flag)
- Ainda precisam de autenticacao futura:
  - todas as rotas acima;
  - `DELETE /history`;
  - rotas de knowledge que reindexam/ingestam/geram DNA.

## Acoes locais perigosas

- `actions.py`: `webbrowser.open`, `os.startfile`, `subprocess.Popen`, escrita em `_ideias`, reindexacao de memoria, consulta de status de servicos e analise de site.
- `app_launcher.py`: abertura de aplicativos, pastas, sites e busca Google.
- `brain_switch.py`: altera `_estado/brain_ativo.json` e pode despachar Claude/Codex via modulos executores.
- `approval_effects.py`: altera workflow VP/Jampa no SQLite/Markdown e pode gerar pacote de publicacao manual.

## Onde ha subprocess

- `actions.py`: abre pasta, VS Code e terminal.
- `app_launcher.py`: abre apps/pastas via `cmd /c start` ou `xdg-open`.
- `claude_exec.py`: `subprocess.Popen`/`subprocess.run` para Claude Code.
- `claude_brain.py`: `subprocess.run`/`subprocess.Popen` para Claude Code headless de raciocinio.
- `code_agent.py`: `subprocess.Popen` para `codex exec`.
- `mcp_client.py`: MCP stdio pode iniciar `uvx`, `npx` ou comandos configurados.
- `_run_server.py` e `server.py`: uvicorn quando executados como entrypoint.

## Onde ha browser automation

- `browser_agent.py`: `browser-use` com modelo via OpenRouter.
- `browser.py`: Playwright headless para leitura de paginas e `webbrowser.open` para navegacao visivel.
- `actions.py` e `app_launcher.py`: abertura visivel de sites/navegador.

## Onde ha Telegram/MCP

- Telegram:
  - `server.py` startup chamava `telegram_bridge.start_background()`.
  - `telegram_bridge.py` faz long polling em `api.telegram.org`.
  - `code_agent.py` e `claude_exec.py` podem notificar via `reminders._notify_telegram`.
- MCP:
  - `mcp_client.py`
  - `_apps/javis-local-interface/data/mcp_servers.json`
  - rotas `/ui/mcp`, `/mcp/{server_id}/tools`, `/mcp/{server_id}/call`

## Onde ha Claude/Codex headless

- Claude headless:
  - `claude_exec.py`
  - `claude_brain.py`
  - `agent.py`
  - `llm_providers.py`
  - rotas `/chat`, `/voice`, `/agents/run`, `/debate`, `/rootcause`, `/v1/chat/completions`
- Codex:
  - `code_agent.py`
  - `brain_switch.py`
  - delegacao em `_brain()` via `orchestrator._run_exec`
  - logs/prompts em `_apps/javis-local-interface/_data/codex_*`

## Onde VP/Jampa esta acoplado ao core

- `server.py`: rotas `/vempassear`, `/vp/*`, `/jampa/*`, `/vp/agents/*`.
- `vp_store.py`, `vp_squad.py`, `jampa_squad.py`, `approval_effects.py`.
- `_apps/javis-local-interface/frontend/vempassear.*`.
- `_apps/javis-local-interface/data/projects/vempassear.json`.
- `_projetos/cerebro-jampa/` e `_projetos/vem-passear/`.
- `agent.py`: tool `gerar_pauta_vp`.

## Travas implementadas por flags

Todas as flags abaixo ficam seguras por padrao em `safe_config.py`:

- `JAVIS_ENABLE_EXTERNAL_ADAPTERS=false`
- `JAVIS_ENABLE_CODEX_EXEC=false`
- `JAVIS_ENABLE_CLAUDE_EXEC=false`
- `JAVIS_ENABLE_BROWSER=false`
- `JAVIS_ENABLE_TELEGRAM=false`
- `JAVIS_ENABLE_MCP=false`
- `JAVIS_ENABLE_LOCAL_ACTIONS=false`
- `JAVIS_ENABLE_VP_EFFECTS=false`
- `JAVIS_DEV_ALLOW_CORS=false`

Comportamento quando bloqueado:

- resposta padrao: `disabled_by_default`;
- motivo: `requires_explicit_enable`;
- campo `capability` indica o adaptador bloqueado.

## Autenticacao local proposta

Nao foi implementado sistema complexo nesta fase. Proposta para R2:

- exigir token local simples em rotas sensiveis via header `X-Javis-Local-Token`;
- token lido por nome de variavel, sem registrar valor em logs;
- manter rotas read-only publicas apenas em `127.0.0.1`;
- bloquear mutacoes sem token mesmo com CORS local.

## CORS restrito

- Antes: `allow_origins=["*"]`.
- Agora: origens locais apenas:
  - `http://127.0.0.1:8000`
  - `http://localhost:8000`
  - `http://127.0.0.1:8001`
  - `http://localhost:8001`
- Wildcard so volta se `JAVIS_DEV_ALLOW_CORS=true`.
- `JAVIS_CORS_ORIGINS` permite lista explicita separada por virgula.

## Checklist antes de rodar servidor

- Confirmar que a branch esta limpa exceto mudancas intencionais.
- Confirmar que `.env` nao esta rastreado e nao foi aberto.
- Rodar `scripts/safe_audit.ps1`.
- Revisar se todas as flags permanecem `false` ou unset.
- Implementar autenticacao local para rotas sensiveis.
- Revisar rotas `knowledge/*`, `history`, `tasks/*` e `missions/*` antes de uso real.
- Separar VP/Jampa do core ou manter bloqueado por `JAVIS_ENABLE_VP_EFFECTS=false`.
- Rodar servidor apenas via `_run_server.py` ou `server.py` ja restritos a `127.0.0.1`.
- Nao usar `iniciar-javis.bat` ate auditar Chainlit/app_ui.

## Recomendacao R1

O Javis antigo ainda nao deve ser usado operacionalmente. Ele agora tem travas por padrao para reduzir risco caso alguem suba o backend, mas a R2 deve implementar autenticacao local e revisar rotas sensiveis antes de qualquer uso continuo.
