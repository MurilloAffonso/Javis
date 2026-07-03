# Voz local grátis — Ollama (llama3.2:3b) no comando de voz

**Data:** 2026-07-03

## Contexto
Murillo queria voz "grátis / baixa latência / sem gastar cloud". Tentou 4x a chave do
Gemini, mas colava sempre um token `AQ.…` (temporário/sessão, não API key AIzaSy) →
sempre 401/429. Paramos de caçar chave.

## Descoberta
Ollama JÁ está rodando no PC com `llama3.2:3b` (3B, Q4) + `nomic-embed-text`. Modelo
pequeno = ideal pra comando de voz. Zero nuvem, zero chave, zero quota.

## Implementado
- `ollama_brain.py` — cliente local (espelha claude_brain: available/answer/answer_stream/ping).
  `_host()` robusto: normaliza OLLAMA_HOST (0.0.0.0→loopback, adiciona http:// e porta).
  `keep_alive=15m` mantém o modelo quente entre falas. num_predict=400.
- `server.py` `/voice/stream`: no ramo de CONVERSA (intent conversa/desconhecido), se
  `JAVIS_VOICE_BRAIN=ollama` e Ollama disponível → usa ollama_brain.answer_stream;
  senão Claude assinatura (padrão). **Ações continuam no Claude** (fast-path/_brain intactos).
  Flag OFF por padrão → voz atual inalterada; reversível.

## Latência medida ao vivo (no PC do Murillo)
- Carga fria (1ª fala): ~44s (carrega o modelo). Só a 1ª.
- Quente: **~1.1s pro 1º token, ~2.8s resposta completa** streaming. Viável pra voz.
- gemini_brain.py também ficou pronto (degradado sem chave), caso um dia pegue a AIzaSy.

## Como ligar (Murillo)
1. No `.env`: `JAVIS_VOICE_BRAIN=ollama` (opcional: `OLLAMA_VOICE_MODEL=llama3.2:3b`).
2. Reiniciar server.py.
3. Falar algo conversacional; o painel mostra brain="ollama". 1ª fala lenta (carga),
   depois ~2s. Pra evitar a fria, pode dar um "oi" ao subir (pré-aquece).
4. Flag off (ou remover) volta pro Claude.

## Verificação
- Sintaxe OK; streaming testado isolado (1.13s 1º chunk). Fiação flag-gated e reversível.
- NÃO testado o /voice/stream ponta-a-ponta com áudio (precisa do Murillo ao vivo).

## Nota
Chave Gemini `AQ.…` = token errado; a certa é `AIzaSy…` (aistudio.google.com/app/apikey).
