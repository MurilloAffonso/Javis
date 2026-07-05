# Estado Atual — Javis

**Atualizado:** 2026-07-05 (voz free grounded + delegação Codex assíncrona + reskin MegaBrain + ingestão de lote + Estúdio persistente + DNA no OpenRouter free)
**Testes:** 191 passing em `_apps/javis-local-interface/` (`python -m pytest tests/ -q`)

> Histórico detalhado de sessões: ver `_logs/` datados e o `git log`. Este arquivo
> é só o **snapshot atual** — mantido curto de propósito.

---

## O que o Javis É

Assistente pessoal/operacional do Murillo (persona "Javes", mordomo PT-BR), com
chat + voz, orquestração de tarefas, pipeline de campanha com aprovação humana,
e uma **máquina de conhecimento** (ingestão → DNA → grafo).

Roda **local em `localhost:8000`** (FastAPI, `backend/server.py`, Windows).
A interface é o **Command Center** em `frontend/command-center/` (não é Chainlit —
o Chainlit foi arquivado; o `.chainlit/` e `.venv_chainlit/` são vestígios).

## O que está PRONTO e TESTADO hoje

| Bloco | Estado |
|-------|--------|
| **Voz** (`server.py /voice/stream` + `voice_bridge.py`) | ✅ `JAVIS_VOICE_BRAIN=openrouter` default → OpenRouter free (1º token ~3s, total ~6s) em vez de Claude Haiku (~20s). Cascata: OpenRouter → Ollama → Claude. **Grounding** (2026-07-05): `_add_voice_grounding()` injeta `estado_resumido()` + `knowledge.answer_context()` quando a pergunta é sobre o projeto → adeus alucinação. Wake word "Javis". STT: faster-whisper local. TTS: Piper local + fallback OpenAI |
| **Delegação Codex** (`orchestrator._run_exec` + `code_agent.py`) | ✅ `JAVIS_AUTO_CODEX=1` default (persistente no `javis-start.bat`). Verbos de execução (programa/cria/refatora/roda…) roteiam pro Codex ASYNC (thread + streaming) — resposta em ~1s, Codex trabalha em fundo, notifica no fim, Claude audita |
| **DNA no free** (`dna_extractor._llm`) | ✅ cascata OpenRouter free → Gemini → Claude. Chave OpenRouter no `.env` funciona; Gemini está com 401 (opcional trocar). Teste real: fidelidade 90, 9/10 dimensões, R$0 |
| **Ingestão em lote** (`ingest.py` + `POST /knowledge/ingest`) | ✅ varre `_inbox/ingestao/*.{txt,md}`, detecta whatsapp/transcrição, roda DNA, reindexa RAG, reconstrói grafo. Assíncrono, com status ao vivo. UI didática em `js/views/ingestao.js` |
| **Estúdio de Conteúdo** (`js/views/conteudo.js` + `POST /conteudo`) | ✅ persiste no SQLite (tabela `content`). Seletor de projeto (Vem Passear / Javes pessoal) muda biblioteca + voz da IA. "Escrever com IA" via `/chat`. Conteúdo VP aparece na aba Marketing (`vempassear.js`) |
| **A Máquina** (`js/views/maquina.js` + `GET /maquina/stats`) | ✅ pipeline em grafo com métricas ao vivo do SQLite: RAG 3.622 vetores, grafo 102 nós/1.690 arestas, 3 dossiês DNA |
| **RAG híbrido** (`knowledge_hybrid.py`) | ✅ SQLite-nativo FTS5 + numpy + RRF fusion. `knowledge.answer_context()` alimenta grounding do chat E da voz |
| **Reskin MegaBrain** (`styles.css`) | ✅ preto quente `#0a0908` + laranja `#ff6a1a` em todas as 12 views. VP com toque de mar (teal `#2bd4c4`). Sidebar em lista vertical com trilho laranja |
| **Cascata multi-cérebro** (`agent.py`, `llm_providers.py`) | ✅ Conversa leve → Gemini/OpenRouter free (~2s); pesado → Claude assinatura → API paga → free |
| **command_router** | ✅ 13 intents, fast-path por palavra-chave, sem LLM |
| **Tool-use** (`agent.py`) | ✅ ~20 ferramentas; gating + prompt caching + compactação |
| **Pipeline de campanha** | ✅ 3 gates humanos (Pauta→Estúdio→Distribuição), SQLite + Journey Log |
| **Frontend** | ✅ Command Center dark+laranja com 12 views: Chat, **Ingestão**, **A Máquina**, Operação, Conclave, Missões, Execução, Tarefas, **Conteúdo**, Painel, Treino, Rotina, Vem Passear, Config |
| **Integrações** | ✅ Telegram ativo; YouTube/weather degradam sem key |

## Fluxo econômico (o que o Murillo pediu: mais barato + mais inteligente)

- **Voz** → OpenRouter free (grátis)
- **Extração de DNA** → OpenRouter free (grátis)
- **Chat leve** → Gemini/OpenRouter free (grátis)
- **Raciocínio pesado + auditoria** → Claude assinatura (paga fixa, sem tokens extras)
- **Execução de código** → Codex assinatura (paga fixa)

Resultado: o **Claude assinatura fica reservado** pro que só ele faz bem (raciocínio e auditoria), e tudo mais roda no free.

## Frentes (ver `proximos-passos.md`)

Próximo movimento aprovado: **rerank do RAG** (Cohere ou equivalente), pra a busca
que alimenta o grounding da voz e o chat ficar mais precisa. Depois disso:
categorização determinística no ingest (pessoal vs projeto vs VP).

Parqueado (não disputa foco): GraphRAG estilo LazyGraphRAG, treinamento/redes,
criativo, migração da voz-sandbox pra `/voice/stream`.
