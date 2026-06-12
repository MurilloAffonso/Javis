# Prompt para o Codex — Painel do Jamba

Cole o texto abaixo no Codex (GPT-5.5, raciocínio Alta, modo "Pedir aprovação").

---

Você vai criar um PAINEL (dashboard) novo para o projeto Jamba, um assistente pessoal estilo JARVIS.

## REGRA CRÍTICA — não quebrar nada
- Crie SOMENTE 3 arquivos NOVOS, todos em `_apps/javis-local-interface/frontend/`:
  - `painel.html`
  - `painel.css`
  - `painel.js`
- NÃO edite, NÃO renomeie e NÃO apague NENHUM arquivo existente (especialmente `index.html`, `app.js`, `style.css`, e qualquer coisa em `backend/`). Outro agente está trabalhando nesses arquivos ao mesmo tempo.
- O backend já serve o painel em `http://localhost:8000/painel` (rota já criada). Não precisa mexer no servidor.

## Estética (combinar com o app)
- Fundo escuro tipo HUD sci-fi. Paleta:
  - fundo `#06060f`, superfície `#0d0d1a`, borda `#22223a`
  - ciano `#00e5ff` (destaque), roxo `#a855f7`, verde `#22c55e`, vermelho `#ef4444`
  - texto `#e2e8f0`, texto fraco `#5a6478`
  - fonte: 'Segoe UI', system-ui; mono: 'Consolas'
- Cantos arredondados (8px), brilhos suaves (glow ciano), animações discretas. Visual "centro de comando".
- Cabeçalho com "JAMBA · PAINEL" e um relógio ao vivo.

## Dados — consuma estes endpoints (já existem, GET, JSON)
- `GET /status` → `{ services: { "Open WebUI": {status, port}, "Ollama": {status, port}, "Voz sandbox": {status, port} }, ts }`
- `GET /reminders` → `{ pending: [ { text, due, falta_min } ] }`
- `GET /profile` → `{ facts: ["fato 1", "fato 2", ...] }`  (o que o Jamba sabe sobre o senhor)
- `GET /integrations` → `{ youtube, google, canva, spotify, openweather, telegram }` (booleans)
- `GET /history` → `{ history: [ { ts, user, response, intent, brain, ms } ] }`  (use os últimos ~10)
- `GET /agents` → `{ agents, conclave, meta, total }`

Use `fetch("http://localhost:8000" + rota)`. Atualize a cada 10s (setInterval). Trate erros sem quebrar (try/catch, mostra "—").

## Layout do painel (cards num grid responsivo)
1. **Lembretes** — lista de `pending` com o texto e "em X min". Se vazio: "Nenhum lembrete".
2. **Memória** — lista os `facts` do `/profile` (o que o Jamba sabe sobre o senhor).
3. **Serviços** — status de cada serviço do `/status` (bolinha verde/vermelha + nome + porta).
4. **Integrações** — chips de `/integrations`: verde se true ("conectado"), cinza se false ("desligado"). Rótulos: YouTube, Google, Spotify, Canva, Clima, Telegram.
5. **Últimas conversas** — últimos itens do `/history`: pergunta do usuário + resposta curta + tempo (ms) e o "brain".
6. **Resumo** — total de mensagens (tamanho do history), total de agentes (`/agents` total), e quantas integrações conectadas.

## Qualidade
- Código limpo, comentado em português, sem dependências externas (só HTML/CSS/JS puro).
- `painel.html` referencia `painel.css` e `painel.js` por caminho relativo (`painel.css`, `painel.js`).
- Responsivo: o grid quebra bem em telas menores.
- Não use frameworks, não instale nada.

Ao terminar, me diga como abrir (deve ser `http://localhost:8000/painel`).
