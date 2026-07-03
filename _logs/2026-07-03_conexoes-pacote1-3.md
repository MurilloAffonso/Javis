# Pacotes 1 e 3 — endpoints órfãos conectados

**Data:** 2026-07-03

## O que foi decidido
Conectar os pacotes 1 (ciclo de vida) e 3 (conhecimento) da auditoria de endpoints
órfãos, escolhidos por Murillo ("os 2"). Escritas com confirmação (1 clique).

## Pacote 1 — ciclo de vida
1. **Concluir task no Kanban** (operacao.js) — botão "✅ Concluir" nos cards não
   encerrados → confirmStrong → `POST /tasks/{id}/complete {note}` (200 ok / 409 já
   encerrada). Gera digest. `opComplete()`.
2. **Marcar/reabrir node de missão** (missoes.js) — cada node real ganha "✔ Concluir"
   / "↩ Reabrir" → confirmStrong → `POST /missions/{id}/nodes/{node}/done {done}`.
   404 = missão calculada (sintética) → toast "não editável". Atualiza nodes + %
   da missão. `miSetNodeDone()`. (Import ampliado: +opSend,opToast,confirmStrong.)
3. **Lembretes** — JÁ estavam ligados (roLoadReminders → GET /reminders). O poll
   proativo por TTS (GET /reminders/poll) fica pra fase de voz.

## Pacote 3 — conhecimento
4. **Busca RAG na busca global** (viewSearch, app.js) — nova seção "🔎 Base de
   conhecimento (RAG)" que chama `GET /knowledge/search?q=` (assíncrono, filtra
   score>0.2) e mostra path + trecho + % relevância. Guard: ignora resposta se o
   usuário mudou a busca. viewSearch não faz mais early-return quando não há match
   local (RAG ainda roda). Smoke test live: "piscinas naturais maré" → 5 hits, top
   0.718 (CEREBRO.JAMPA/base-operacional-comercial.md).
5. **Treinar do YouTube** (treino.js) — card no topo: input de URL → `POST
   /train/youtube {url}` (agent default "khan") → extrai transcrição, salva doc,
   reindexa RAG. Mostra title/channel/chars/file.

## Verificação
- Sintaxe OK nos 13 arquivos; router intacto; deps fechadas.
- Contratos conferidos no server.py + smoke test live do knowledge/search.
- Schemas reais: node {id,label,full_text,status,pct}; hit {path,chunk,score}.

## Próximo passo
1. Murillo testa (restart do server NÃO é necessário — só front + endpoints já vivos).
2. Commit (aguardando aprovação).
3. Restam miúdos da auditoria (pacote 4): /memory, /rootcause, /profile, upload.
