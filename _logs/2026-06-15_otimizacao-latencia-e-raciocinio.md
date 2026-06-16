# 2026-06-15 — Otimização de latência e raciocínio do Jamba

## Contexto
Murillo relatou que a conversa "travava bastante", as respostas demoravam e o
"raciocínio se perdia". Investigação feita medindo os endpoints ao vivo
(`/chat`, `/chat/stream`, `/voice/stream`) e analisando prints da interface e do
painel da OpenAI.

## O que foi decidido / feito

### 1. Confiabilidade dos provedores (agent.py)
- **Timeout de 20s** em todas as chamadas de LLM (OpenAI/Claude/OpenRouter +
  streaming), configurável via `JAVIS_LLM_TIMEOUT`. `max_retries=1` na OpenAI.
- **Logs visíveis** (`[agent] ...`) no lugar dos `except: pass` silenciosos.
- Mantido `gpt-4o-mini` como cérebro (decisão do Murillo — sem investir em
  OpenRouter pago; saldo OpenAI estava OK: ~$3,95 de crédito, uso mínimo).

### 2. Buffering do SSE (server.py) — causa nº 1 do "travando"
- Medição provou: o servidor gerava o evento `meta` em ~2ms, mas o navegador só
  recebia ~2–3,7s depois. O uvicorn segurava os primeiros chunks pequenos.
- **Fix:** `_SSE_PADDING` (comentário SSE de ~2KB) no início de todo stream
  (`/chat/stream` e `/voice/stream`). 1º byte: **3,75s → 0,22s** (medido).

### 3. Roteador sequestrando a conversa (command_router.py + server.py)
- A palavra-chave greedy **`"projeto "`** fazia qualquer frase com "projeto"
  abrir uma pasta (visto no print: "O nome do projeto é Vem Passear" abriu o
  explorador). Removida; mantidos os comandos explícitos.
- Guarda **`_FAST_OPEN` + >6 palavras**: comando de abrir/navegar embutido em
  frase longa = conversa, não dispara ação.

### 4. Conversa volta a raciocinar com ferramentas (server.py/agent.py)
- A otimização `chat_text` (conversa sem tools) deixava respostas ocas (sem
  acesso a `buscar_conhecimento`/`lembrar_fato`). **Removida.**
- Agora conversa E ação passam pelo agente com ferramentas (`agent.respond`).
  O feedback instantâneo é garantido pelo padding, não pelo streaming "burro".

### 5. Transcrição mais precisa (server.py /transcribe)
- `whisper-1` → **`gpt-4o-transcribe`** (configurável via
  `JAVIS_TRANSCRIBE_MODEL`), com **prompt-viés** dos nomes próprios (Jampa, Vem
  Passear, Murillo, Picãozinho...). Degrada para whisper-1 se indisponível.
- Validado round-trip TTS→transcribe: nomes próprios transcritos corretamente.

## Por quê
A voz/transcrição embolada (ex.: "limpar-se a jampa") entregava lixo ao cérebro,
e o roteador interceptava conversa como ação — duas causas do "raciocínio
perdido". O buffering do SSE causava a sensação de travamento.

## Alternativas consideradas
- Investir $5 no OpenRouter (modelo pago): descartado — saldo OpenAI OK e
  gpt-4o-mini atende. OpenRouter fica só como último fallback.
- Manter streaming token-a-token sem tools: descartado — sacrificava raciocínio.
- Realtime API (voz fala→fala, ~300ms): anotado como caminho futuro, mas é
  reconstrução do fluxo de voz, não config.

## Verificação
- 54 testes passando. `/chat` ~2,5s, `/chat/stream` 1º byte 0,22s.
- Frases declarativas/perguntas não abrem mais pasta; respostas com conteúdo
  real. Transcrição valida nomes próprios.

## Próximo passo
- Avaliar memória de longo prazo (hoje só últimas 6 mensagens) — possível causa
  residual de "raciocínio perdido" em conversas longas.
- Considerar Realtime API se a prioridade virar latência de voz quase instantânea.
- Nada commitado — aguardando aprovação do Murillo.
