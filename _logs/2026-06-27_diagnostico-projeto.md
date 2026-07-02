# DIAGNÓSTICO DO PROJETO JAVIS

Data: 2026-06-25

## 1. O que é o Javis

Assistente pessoal e operacional de Murillo (não é produto, não é trading/financeiro). Funções declaradas no README: conversa com contexto persistente, memória, captura de ideias, organização de projetos, pesquisa/síntese, registro de decisões e (em evolução) execução de ações no computador com aprovação humana.

Governança do próprio repo (CLAUDE.md/AGENTS.md): escopo restrito à pasta `javis/`, nada de commit/push sem aprovação explícita, leitura obrigatória antes de editar, uso de LeanCTX para economia de tokens.

## 2. Estrutura de pastas (visão geral)

```
javis/
├── _apps/javis-local-interface/   — único app de código (backend FastAPI + frontend SPA)
├── _memoria/        (13 arquivos) — identidade, regras, decisões, testes — maduro
├── _logs/            (77 arquivos) — decisões + checkpoints de sessão — muito ativo
├── _skills/           (41 arquivos) — playbooks de agentes/processos — muito ativo
├── _projetos/                      — cerebro-jampa/vem-passear (campanha real, 3 gates)
├── _outbox/           (22 arquivos) — entregáveis (textos, criativos, relatórios)
├── _prompts/            (8 arquivos) — prompts do Open WebUI
├── _docs/                (7 docs)    — roadmap, visão operacional, E2E
├── _ideias/              (4 arquivos) — baixo volume, processado regularmente
├── _ferramentas/                    — LeanCTX, voz (sandbox), agentmemory, integrações
├── _arquitetura/, _templates/, _treinamento/, _referencias/, _estado/, _sessoes/ — suporte
├── _inbox/                          — vazio (sinal bom: processado)
├── data/                            — state_store.db, stream_store
├── docs/                            — notas "superpowers" (planos futuros)
├── .obsidian/, .chainlit/, .codex/, .codegraph/, .playwright-mcp/ — config de ferramentas
├── README.md, AGENTS.md, CLAUDE.md, JAVIS-CEREBRO.md — documentação raiz
├── docker-compose.yml               — Open WebUI + Ollama
└── ~40 screenshots PNG na raiz       — capturas de UI (sujeira leve)
```

Nenhuma pasta crítica está vazia ou abandonada. Separação clara entre código, memória/operação e entregas.

## 3. _apps/javis-local-interface (o coração do código)

**Backend (Python/FastAPI):**
- `agent.py` — orquestrador com tool-use via Claude Haiku 4.5 (default desde 21/06, mais barato que Sonnet); tool gating reduz ~30→10-15 tools por chamada; fallback Claude → OpenAI gpt-4o-mini → Ollama local; timeout 20s.
- `server.py` — endpoints `/chat` (SSE streaming), `/status`, `/agents`, `/history`; monta `/central` e `/command-center` se existirem.
- `command_router.py` — roteamento por palavra-chave (13 intents, sem LLM), com risk map (critical/medium/low/none).
- `actions.py` — whitelist de ações seguras; bloqueia delete/install/git push/shell arbitrário; loga tudo em JSONL.
- Suporte: `claude_brain.py` (RAG), `claude_exec.py` (executor Codex), `history_store.py`, `db.py`/`db_sync.py` (SQLite), `tts_local.py` (Piper), `knowledge.py` (índice Obsidian), `telegram_bridge.py`, `browser_agent.py`, `approval_effects.py`.

**Frontend (HTML/JS):** SPA com 3 abas (Conversa, Quadro Kanban, Agentes), SSE streaming, Bootstrap 5 + Pico CSS. Subpastas isoladas `/central` e `/command-center` (protótipos paralelos).

**Testes:** 189/189 passando (pytest + playwright).

**Dependências (requirements.txt):** fastapi, anthropic, openai, piper-tts, chainlit, browser-use, mcp, yt-dlp, markitdown, ddgs, beautifulsoup4 — stack coerente com as funções declaradas.

## 4. Trajetória recente (git log)

Desenvolvimento ativo e contínuo (commits quase diários nas últimas semanas):
- Fusão de projetos (Cérebro Jampa indexado no RAG, painel "Javis Dev" removido)
- Auto-sync do RAG, botão Sincronizar
- Capacidades novas: treino automático, pulso, browser, MCP, playbooks
- Aba Treinamento + fallback OpenRouter free
- JAVIS Command Center (chat por voz + orquestração)
- TTS local Piper, memória Obsidian ampliada, telemetria de custo

Padrão: features frequentes, refactors de consolidação, disciplina de registrar decisões em `_logs/` antes de mudanças estruturais.

## 5. Pontos de atenção / sujeira

| Item | Observação | Ação sugerida |
|---|---|---|
| `cohort_blocks.txt`, `openrouter_models.html` na raiz | Dumps/estudos pontuais, não pertencem à raiz | Mover para `_logs/` ou `_ferramentas/` |
| `app_ui.py.py` | Nome com typo (duplo `.py`) | Confirmar com Murillo antes de renomear/remover |
| `Sem título.canvas`, `Sem título 1.canvas` | Canvas vazios do Obsidian | Provavelmente lixo, confirmar antes de apagar |
| `teste_voz.txt` (vazio) | Scratch sem conteúdo | Idem |
| `_apps/.../backend/_scratch/*` (não versionado, `??` no git status) | Benchmarks/inspeção de PDF/áudio temporários | Ok manter como scratch; não commitar |
| ~40 screenshots PNG na raiz (~12MB) | Histórico de UI, fora de `_logs/screenshots` | Considerar mover para `_logs/screenshots/` |
| `.env` modificado | Contém chaves de API (Anthropic, OpenAI, OpenRouter, Gemini, Telegram) | Nunca commitar; já está no `.gitignore` |

Nenhum item é crítico — é sujeira cosmética, não risco funcional.

## 6. Saúde geral

- ✅ Backend robusto e testado (189/189), com camadas de segurança (whitelist, dry_run, aprovação humana)
- ✅ Memória e decisões bem registradas e atualizadas (`_memoria/`, `_logs/`)
- ✅ Documentação consistente (README, AGENTS.md, CLAUDE.md, _docs/)
- ✅ Projeto integrado ativo: campanha Vem Passear Jampa com pipeline de 3 gates
- ⚠️ Pequena sujeira de arquivos soltos na raiz (ver seção 5)
- ⚠️ Existem duas interfaces paralelas (`/central` e `/command-center`) — vale confirmar com Murillo se ambas ainda são necessárias ou se uma é legado

## 7. Próximos passos sugeridos (não executados, apenas diagnóstico)

1. Decidir o destino dos arquivos soltos na raiz (seção 5) — perguntar a Murillo antes de mover/apagar.
2. Confirmar se `/central` (protótipo) ainda é necessário frente ao `/command-center` (v2/v3).
3. Nenhuma ação de código foi feita neste diagnóstico — é só leitura/relatório, conforme pedido.
