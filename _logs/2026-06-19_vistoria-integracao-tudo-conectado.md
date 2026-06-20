# Vistoria de integração — "tudo conectado, sem erro" — 19/06

Murillo pediu pra garantir tudo funcionando, conectado, erros corrigidos,
organizado e orquestrado. Em vez de afirmar, VERIFIQUEI de verdade.

## Verificações (reais)
- **Import**: 16/16 módulos core importam limpo (server, agent, agent_runner,
  llm_providers, claude_brain, claude_exec, conclave, orchestrator, actions,
  file_analyzer, knowledge, briefing, mission_board, command_router,
  agents.specialized, agents.meta).
- **Testes**: `pytest tests/ -q` → 71 passed.
- **Servidor ao vivo (:8000, auto-reload pegou tudo de hoje)**: /status, /agents,
  /missions, /briefing, /brain/active → todos HTTP 200.
  - 17 agentes, 6 missões (inclui `pipeline-marketing-vem-passear-jampa`),
    brain ativo = claude.
- **Frontend**: view Fluxo VP renderiza (6 raias/4 gates/loop); `node --check` OK.

## Bugs REAIS encontrados e corrigidos nesta vistoria
1. **Indicador de status sempre "offline" (conectividade)** — a constante
   `API = "http://localhost:8000"` no `app.js` estava fixa em `localhost`, mas a
   página é servida por `127.0.0.1`. `localhost` resolve pra IPv6 `::1` (onde o
   servidor não escuta) → todo fetch de status dava timeout → tudo "offline".
   **Fix:** `const API = window.location.origin` (mesma origem da página).
2. **/status lento (estourava o timeout do cliente)** — o endpoint testava as
   portas dos serviços via `socket.create_connection(("localhost", port))`, e o
   `localhost`→IPv6 fazia cada serviço offline ESPERAR o timeout inteiro,
   passando dos 4s do cliente. **Fix:** usar `127.0.0.1` + timeout 0.5 → /status
   caiu pra ~1s. Confirmado no navegador: indicador **CLAUDE acende online**.
3. **Indicador "OLLAMA" obsoleto** (depois de remover o Ollama) — trocado por
   **CLAUDE**, alimentado por um campo novo `brain` no `/status`
   (`claude_brain.available()`). HTML/JS/endpoint atualizados juntos.

## Mapa honesto: o que está conectado de ponta a ponta
CONECTADO E FUNCIONANDO:
- Cérebro único Claude (assinatura) em chat/voz, Conclave, agentes, raciocínio.
- Visão: analisar imagem/PDF-diagrama (Fluxograma lido de verdade).
- Quadro Kanban ↔ `codex_backlog.md` (missões reais, incl. Pipeline Marketing).
- View Fluxo VP (pipeline em raias) ↔ fluxograma-vem-passear.md.
- /status ↔ indicador CLAUDE/WEBUI (agora de verdade).
- 71 testes, imports limpos, endpoints 200.

AINDA MOCK / PENDENTE (não inventei que está pronto):
- View "Workflows" (canvas SVG) — é layout de demonstração, não plugado em
  missão real (o real é o "Quadro" e o "Fluxo VP").
- Feed de atividade na Sala — dados mock.
- Publicação no Instagram (raia Distribuição) — manual; sem integração de post.
- Embeddings/voz (Whisper+TTS) dependem de OPENAI_API_KEY (intencional).

## Custo conhecido (já registrado)
Sem reserva de cérebro: se a cota da assinatura zerar, responde com mensagem
clara (sem Ollama). Latência da assinatura 30-80s.

**Sem commit/push — Murillo revisa e decide.**
