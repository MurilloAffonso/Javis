# Estado Atual — Javis

**Atualizado:** 2026-06-12 (sessão voice-streaming-ui)
**Responsável pela última atualização:** Claude Code — Voice/Streaming/UI upgrade + abrir_projeto fix

---

## Stack ativa

| Ferramenta | Status | Evidência |
|-----------|--------|-----------|
| LeanCTX v3.7.5 | ✅ ATIVO | 1.0M tokens salvos, 79.7% compressão, $2.73 USD |
| CodeGraph | ✅ ATIVO | 13 arquivos, 177 nós, 315 arestas indexados |
| AgentMemory | ✅ instalado | MCP configurado, em uso |
| Open WebUI | ✅ rodando | localhost:3000 (Docker) |
| Ollama + llama3.2:3b | ✅ rodando | porta 11434 |
| voz-sandbox (Open-LLM-VTuber) | ⏸ separado | porta 12393, não integrado ao Javis |
| Headroom | ✅ instalado | v0.24.0, compilado com Rust, `headroom wrap claude` disponível |

---

## Módulos do Javis Local Interface

| Módulo | Status |
|--------|--------|
| backend/command_router.py | ✅ 13 intents, testado |
| backend/voice_bridge.py | ✅ dry_run=True, 5 test files passando |
| backend/actions.py | ✅ whitelist de 9 ações seguras |
| backend/logger.py | ✅ rotação diária JSONL |
| frontend/app.js | ✅ 14/14 intents + NeuralBrain (cérebro neural animado) |
| frontend/index.html | ✅ banner neural + botões 📂 projeto e 🌐 analisar site |
| backend/site_analyzer.py | ✅ analisa URL + gera esqueleto HTML/CSS próprio |
| tests/ | ✅ 189 checks, 0 falhas |

---

## Sessões recentes

- 2026-06-10: Setup inicial, LeanCTX, Open WebUI, 6 modelos configurados
- 2026-06-11: 5 fases de auditoria (gitignore, actions, logs, intents, token economy)
- 2026-06-11: Sessão abrir-sessao/fechar-sessao — 1ª sessão com protocolo completo. Auditoria de intents: 13/13 consistentes, 189/189 testes OK.
- 2026-06-12: Voice/Streaming/UI upgrade — Whisper ASR, AutoWhisperEngine c/ VAD calibrado, streaming SSE, TTS nova, UI HUD sci-fi. abrir_projeto adicionado.
- 2026-06-12: Cérebro neural animado (NeuralBrain canvas) + análise de site (site_analyzer) por voz/chat. Ações locais executam no /chat/stream e /voice. Performance: removida dupla chamada Claude (_classify), run_in_threadpool evita travar event loop. Launcher javis-start.bat + atalhos Desktop/Startup.
- 2026-06-12: Redesign JARVIS-style — renomeado para JAMBA (wake word + prompts). Novo layout: esquerda=stats/cérebros/agentes, CENTRO=orbe circular gigante (VoiceOrb canvas, reativo à voz via mic level), DIREITA=chat. Música corrigida: tocar_musica vence youtube, _play_music extrai termo e busca, ou abre stream lofi (autoplay). Wake words Jamba em voice_bridge + VoiceEngine.
- 2026-06-12: Voz onyx (homem) tts-1-hd + trata Murillo por "senhor". Integrações: integrations.py (YouTube exato, weather), RESERVATORIOS.md (curadoria de APIs/repos por encaixe). Novas: clima (OpenWeather, intent+ação) e telegram_bridge.py (controla Jamba pelo celular via long polling, sobe no startup se TELEGRAM_BOT_TOKEN). Todas degradam sem key. Pendente: OPENWEATHER_API_KEY, TELEGRAM_BOT_TOKEN, YOUTUBE_API_KEY no .env.
- 2026-06-12: TOOL-USE (agent.py) — Claude/OpenAI function calling com 11 ferramentas; entende intenção e encadeia ações ("abre youtube e toca jazz"). Wired em /chat/stream e /voice; FAST_PATH só p/ abridores de app inequívocos. Fallback Claude→OpenAI (chave Anthropic SEM SALDO, usando OpenAI gpt-4o-mini). WAKE WORD "Jamba" (WakeWordEngine, Web Speech) — botão 🎙️, exclusivo c/ always-on 👂. ATENÇÃO: recarregar ANTHROPIC_API_KEY com saldo quando possível.
- 2026-06-12: BATCH inteligência — Murillo tem ASSINATURA Claude (não API); CLI claude headless testado = 16-22s, lento demais p/ cérebro → estratégia: usar Claude Code (este chat) p/ CONSTRUIR, OpenAI roda o Jamba. Construído: profile.py (memória/personalização, perfil.json injetado no prompt do agente), reminders.py (lembretes/timers, thread checador + fila /reminders/poll que a UI fala por TTS + Telegram), code_agent.py (bridge Codex 'programar' — requer npm i -g @openai/codex), rotina_matinal. Novas tools no agente: lembrar_fato, criar_lembrete, listar_lembretes, rotina_matinal, programar. Frontend: pollReminders 15s. Tudo testado OK.
- 2026-06-12: BATCH 2 — Codex INSTALADO (0.139.0, logado via ChatGPT, code_agent.dispatch pronto, roda na assinatura ChatGPT não gasta API). app_launcher.py: abre QUALQUER app/site do Windows (mapa ~50 apps + ms-settings URIs + start genérico) — tools abrir_app, abrir_site, pesquisar_google (testados: calculadora, google OK). WhatsApp via wa.me: integrations.whatsapp_send (abre msg pronta, user confirma) — tool enviar_whatsapp. Agente agora com ~20 ferramentas. Telegram ATIVO (token no .env, travado em TELEGRAM_ALLOWED_CHAT_ID=7840324823, bot @Jarvis_VempassearJampa_bot). Auto-send WhatsApp real exigiria whatsapp-web.js/Cloud API.
- 2026-06-12: RAG — knowledge.py: indexa .md/.txt das pastas de conhecimento (_memoria,_ideias,_projetos,_logs,_estado,_prompts,_skills,_inbox,_outbox,_ferramentas + .md da raiz; skip open-webui-data/caches; trava _MAX_FILES=800) com embeddings text-embedding-3-small (97 arquivos, 494 chunks). Busca cosine, tool buscar_conhecimento no agente. Endpoints /knowledge/reindex e /search; indexa no startup (incremental por mtime). FIX: FAST_PATH agora ignora perguntas (_looks_like_question) — "o que tá pendente no projeto?" ia abrir pasta, agora vai pro RAG. Testado: responde sobre os arquivos do Murillo corretamente. Próximos sugeridos: auto-memória + proatividade (digest matinal Telegram agendado).
- 2026-06-12: PAINEL — Codex estava em 98-99% de uso (reseta 18/jun, 1 reset), então EU construí o painel (não gastar reset dele). 3 arquivos novos: frontend/painel.{html,css,js} (HUD sci-fi, dados reais). Endpoints novos no server: GET /profile (facts), /integrations (available), e rotas /painel /painel.css /painel.js. Acessa em localhost:8000/painel. Testado no browser: 17 agentes, 3 serviços, 3 fatos, Telegram conectado. NOTA: Codex tem outros projetos (CEREBROJAMPA, CEREBRO.CLAUDE) — manter Jamba separado.

---

## O que está pendente (ver proximos-passos.md)

- ANTHROPIC_API_KEY ausente no .env (Claude usa Ollama como fallback)
- Headroom aguardando aprovação de Murillo
- Fase 2 de voz (execução real) aguardando aprovação de Murillo
