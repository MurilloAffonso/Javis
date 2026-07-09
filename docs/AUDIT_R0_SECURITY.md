# Auditoria R0 de Segurança — Javis antigo

Data da auditoria: 2026-07-08  
Escopo: snapshot e segurança do Javis antigo, somente leitura e documentação.  
Restrições cumpridas: não foi instalado pacote, não foi executado servidor/agente/Codex/Claude, não houve commit, push, limpeza, movimentação, renomeação ou exclusão de arquivos, e nenhum conteúdo de `.env`, token, credencial ou chave foi aberto.

## Branch atual

- Branch: `master`
- Tracking: `master...origin/master`

## Status Git

Comando executado: `git status -sb`

```text
## master...origin/master
?? Codex
?? "Sem título.canvas"
?? Vem
?? _referencias/
?? fibonacci.py
?? test_fibonacci.py
```

Comando executado: `git branch --show-current`

```text
master
```

Comando executado: `git log --oneline -10`

```text
d78eebe chore: sincroniza estado, docs de delegacao Codex, DNA (mentores + megabrain) e material de ingest
801cb39 test(voz): cobre portao de 25s (janela de conversa /v1/chat/completions)
f31331e feat(rag): rerank medido e descartado (piora RRF); portao de relevancia apertado
edf797b feat(voz): RAG da voz filtra por escopo - fecha bug de identidade (Javes vs VP)
f33c09c feat(rag): categorizacao deterministica de escopo (pessoal/projeto/vp) no ingest
918c005 docs: estado-atual.md reflete o que rodou 2026-06/07 (voz free grounded, Codex async, ingest, Estudio, DNA free)
d78fe65 feat(voz): grounding com estado do projeto + RAG - fim das alucinacoes
3e2f375 feat: cerebro de voz via OpenRouter free - resposta 3-6x mais rapida (grátis)
cbfa8fe chore: atualiza lista free do OpenRouter apos vistoria - Nemotron 3 Ultra 550B no fallback
da7ffb1 feat: DNA extraido por modelo FREE (OpenRouter) - economia ativa sem Claude
```

Observação: o comando pedido `git ls-files | findstr /i "token credential credentials secret key env pem p12"` foi bloqueado pela allowlist do LeanCTX antes de executar o filtro. A checagem equivalente foi feita a partir da saída de `git ls-files`, sem abrir conteúdo de arquivos.

## Arquivos sensíveis rastreados ou suspeitos

Comando executado: `git ls-files .env`

```text
```

Resultado:

- `.env` não está rastreado pelo Git.
- `.env` existe no diretório local como arquivo ignorado, mas seu conteúdo não foi aberto.
- Arquivo rastreado com nome sensível por padrão:
  - `.env.example`
- Arquivos rastreados com a palavra `token` no nome, sem indicação de segredo pelo nome:
  - `_logs/2026-06-11_token-economy-audit.md`
  - `_logs/token-economy.md`
- Arquivos ignorados/suspeitos por nome, sem conteúdo aberto:
  - `.claude/settings.local.json`
  - `_apps/javis-local-interface/_data/token_usage.jsonl`
  - `_apps/javis-local-interface/_data/javis.db`
  - `_apps/javis-local-interface/_data/chat_history.json`
  - `_memoria/*.json` operacionais, incluindo perfil, lembretes e padrões de voz

## Arquivos não rastreados

Comando executado: `git ls-files --others --exclude-standard`

```text
Codex
"Sem título.canvas"
Vem
_referencias/megabrain-video/video.mp4
fibonacci.py
test_fibonacci.py
```

Relevância:

- `Codex` e `Vem`: arquivos/pastas soltos na raiz, não rastreados.
- `_referencias/megabrain-video/video.mp4`: referência pesada e externa ao núcleo.
- `fibonacci.py` e `test_fibonacci.py`: arquivos soltos de teste/experimento na raiz.
- `Sem título.canvas`: artefato solto de Obsidian/canvas na raiz.

## Caches, runtime e lixo detectado

Detectado por `git status --ignored -sb` e listagem de raiz, sem limpeza:

- Segredos/config local ignorados:
  - `.env`
  - `.claude/settings.local.json`
  - `.claude/scheduled_tasks.lock`
- Diretórios de ferramenta/runtime:
  - `.chainlit/`
  - `.codegraph/`
  - `.codex/`
  - `.playwright-mcp/`
  - `_apps/javis-local-interface/.chainlit/`
  - `_apps/javis-local-interface/.files/`
  - `_apps/javis-local-interface/.venv_chainlit/`
- Cache Python/testes:
  - `.pytest_cache/`
  - `__pycache__/`
  - `_apps/javis-local-interface/.pytest_cache/`
  - `_apps/javis-local-interface/__pycache__/`
  - `_apps/javis-local-interface/backend/.pytest_cache/`
  - `_apps/javis-local-interface/backend/__pycache__/`
  - `_apps/javis-local-interface/tests/.pytest_cache/`
  - `_apps/javis-local-interface/tests/__pycache__/`
  - `_projetos/cerebro-jampa/__pycache__/`
- Dados/runtime do app:
  - `_apps/javis-local-interface/_data/chat_history.json`
  - `_apps/javis-local-interface/_data/javis.db`
  - `_apps/javis-local-interface/_data/ref_upload.png`
  - `_apps/javis-local-interface/_data/token_usage.jsonl`
  - `_apps/javis-local-interface/_data/vp_*.json`
  - `_apps/javis-local-interface/logs/`
- Logs, dumps e screenshots:
  - `_logs/*.log`
  - `_logs/dumps/`
  - `_logs/screenshots/`
  - `_logs/voz-sandbox-stdout.log`
  - `_apps/javis-local-interface/_data/codex_task_*.log`
- Referências e artefatos externos/pesados:
  - `_referencias/ECC/`
  - `_referencias/megabrain-video/`
  - `_referencias/silero-vad/`
  - `_ferramentas/integracoes/open-notebook/notebook_data/`
  - `_ferramentas/integracoes/open-notebook/surreal_data/`
  - `_ferramentas/voz-sandbox/`
- Arquivos soltos/legados:
  - `Codex`
  - `Vem`
  - `fibonacci.py`
  - `test_fibonacci.py`
  - `Sem título.canvas`
  - `_arquivo/*.canvas`
  - `_arquivo/app_ui.py.bak`
  - `_arquivo/app_ui.py.py`
- `node_modules/`, `venv/` e `.venv/` raiz não apareceram no snapshot; foi detectado `_apps/javis-local-interface/.venv_chainlit/`.

## Integrações externas detectadas

Detectadas por nome de arquivo, rotas e referências textuais, sem execução:

- FastAPI:
  - `_apps/javis-local-interface/backend/server.py`
  - `_apps/javis-local-interface/backend/_run_server.py`
- Browser/automação local:
  - `_apps/javis-local-interface/backend/browser.py`
  - `_apps/javis-local-interface/backend/browser_agent.py`
  - `_apps/javis-local-interface/backend/actions.py`
  - `_apps/javis-local-interface/backend/app_launcher.py`
  - `_apps/javis-local-interface/backend/integrations.py`
  - `.playwright-mcp/`
- Telegram:
  - `_apps/javis-local-interface/backend/telegram_bridge.py`
- MCP:
  - `_apps/javis-local-interface/backend/mcp_client.py`
  - `_apps/javis-local-interface/data/mcp_servers.json`
- Claude/Anthropic:
  - `_apps/javis-local-interface/backend/claude_brain.py`
  - `_apps/javis-local-interface/backend/claude_exec.py`
  - `_apps/javis-local-interface/backend/agent.py`
  - `_apps/javis-local-interface/backend/agents/specialized.py`
  - `CLAUDE.md`
- Codex:
  - `_apps/javis-local-interface/backend/code_agent.py`
  - `_apps/javis-local-interface/_data/codex_*`
  - `_logs/*codex*.log`
  - `Codex` não rastreado na raiz
- OpenRouter:
  - `_apps/javis-local-interface/backend/openrouter_fallback.py`
  - `_apps/javis-local-interface/backend/openrouter_voice.py`
  - `_apps/javis-local-interface/backend/llm_providers.py`
  - `_apps/javis-local-interface/backend/browser_agent.py`
- Gemini:
  - `_apps/javis-local-interface/backend/gemini_brain.py`
  - `_apps/javis-local-interface/backend/dna_extractor.py`
  - `_apps/javis-local-interface/backend/agent.py`
- Ollama:
  - `_apps/javis-local-interface/backend/ollama_brain.py`
  - referências em `llm_providers.py`, docs e logs
- OpenAI:
  - `_apps/javis-local-interface/backend/llm_providers.py`
  - `_apps/javis-local-interface/backend/knowledge.py`
  - `_apps/javis-local-interface/backend/knowledge_hybrid.py`
  - `_apps/javis-local-interface/backend/agent.py`
  - `_apps/javis-local-interface/backend/server.py` em transcrição/LLM
- WhatsApp:
  - `_apps/javis-local-interface/backend/wa_analyzer.py`
  - `_apps/javis-local-interface/backend/integrations.py`
  - referências em VP/Jampa, templates e logs Codex
- Gmail:
  - referências em logs/configurações de UI e catálogo de integrações; não foi confirmado backend ativo nesta fase.
- VP/Jampa/Vem Passear:
  - `_apps/javis-local-interface/backend/jampa_squad.py`
  - `_apps/javis-local-interface/backend/vp_squad.py`
  - `_apps/javis-local-interface/backend/vp_store.py`
  - rotas `/vp/*`, `/jampa/*`, `/vempassear` em `server.py`
  - `_apps/javis-local-interface/frontend/vempassear.*`
  - `_apps/javis-local-interface/data/projects/vempassear.json`
  - `_projetos/cerebro-jampa/`
  - `_projetos/vem-passear/`

## Riscos críticos

- CORS aberto em `server.py`: `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`.
- API FastAPI expõe muitas rotas `POST`, `PATCH` e `DELETE`; não foi observado mecanismo de autenticação obrigatório no scan de rotas.
- Backend contém ações locais por `webbrowser.open`, `os.startfile` e `subprocess.Popen`, incluindo abertura de navegador, VS Code e terminal.
- Execução de Claude e Codex por subprocesso existe em `claude_brain.py`, `claude_exec.py` e `code_agent.py`.
- `.env` local existe ignorado; conteúdo não foi aberto, mas o backend lê várias chaves por ambiente.
- Integrações Telegram, MCP, browser automation e LLM providers estão dentro do backend; iniciar o sistema pode acionar superfície externa ou local além do chat.
- Rotas e arquivos de VP/Jampa estão acoplados ao Javis antigo, contrariando a fronteira desejada entre núcleo Javis e projetos externos.

## Riscos médios

- Muitos artefatos de runtime, logs, caches e bancos locais convivem com código fonte.
- Logs Codex/Claude e `_data` podem conter histórico operacional, prompts, respostas ou dados de negócio.
- `_referencias/` contém material externo pesado e possivelmente não curado para o núcleo.
- Há arquivos soltos na raiz (`Codex`, `Vem`, `fibonacci.py`, `test_fibonacci.py`, canvas) que confundem escopo e limpeza futura.
- Dependências e integrações aparecem parcialmente misturadas: `package-lock.json`, browser automation, Chainlit, OpenNotebook, Playwright MCP e provedores LLM.
- Gmail aparece como referência/placeholder em logs/UI, sem confirmação de implementação ativa.

## O que NÃO deve ser executado ainda

- `python _apps/javis-local-interface/backend/_run_server.py`
- `uvicorn`, Chainlit ou qualquer servidor do Javis antigo
- `javis-start.bat` e `_apps/javis-local-interface/iniciar-javis.bat`
- `voice_bridge.py`, `agent_runner.py`, `agent.py`, `orchestrator.py`
- `claude_brain.py`, `claude_exec.py`, `code_agent.py`
- Codex CLI ou Claude Code headless
- `telegram_bridge.py`
- `mcp_client.py` ou servidores MCP configurados em `data/mcp_servers.json`
- `browser_agent.py`, Playwright MCP, `browser_use` ou automações de navegador
- Ações que abrem navegador, terminal, VS Code, Open WebUI, YouTube ou WhatsApp Web
- Scripts de VP/Jampa, incluindo geradores de carrossel, squads e rotas `/vp/*` e `/jampa/*`
- Docker/OpenNotebook/Ollama/Open WebUI
- Qualquer leitura de conteúdo de `.env`, tokens, credenciais ou chaves

## Checklist para R1

- Definir fronteira operacional: núcleo Javis antigo vs VP/Jampa vs referências externas.
- Mapear todas as rotas FastAPI e marcar cada uma como leitura, mutação, execução local ou integração externa.
- Antes de rodar servidor, corrigir CORS para origem local explícita e adicionar autenticação local ou gate equivalente.
- Desabilitar por padrão adaptadores de execução: Claude, Codex, Telegram, MCP, browser automation, Open WebUI, WhatsApp e scripts VP/Jampa.
- Inventariar variáveis de ambiente por nome, sem conteúdo, e validar `.gitignore` para segredos/runtime.
- Revisar `actions.py`, `app_launcher.py`, `command_router.py` e gates de aprovação contra a whitelist real.
- Separar plano de limpeza para caches/logs/runtime, com aprovação explícita antes de apagar qualquer coisa.
- Criar lista de arquivos úteis reaproveitáveis por domínio: voz, RAG, SQLite, approvals, providers, UI, integrações.
- Rodar testes somente depois dos gates acima estarem revisados e com execução externa desabilitada.

## Recomendação final

Não rodar o Javis antigo agora. A R1 deve ser uma fase de hardening e separação: travar CORS/autenticação, desligar adaptadores externos por padrão, isolar VP/Jampa do núcleo, mapear endpoints e actions, e só então decidir o que será reaproveitado, testado ou limpo.
