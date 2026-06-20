# Vistoria — cérebro & orquestração do Javis — 19/06

Pedido do Murillo: "faz uma vistoria e melhora tudo" (foco no que vínhamos
mexendo: cérebro, execução, orquestramento). Vistoria do fluxo `_brain` →
`agent.respond` → ferramentas → executor.

## Mapa do fluxo (como está hoje)

`/chat`, `/chat/stream` e `/voice` → `server._brain()`:
1. `command_router.route()` classifica intent por palavra-chave (sem LLM).
2. Fast-path: ação local óbvia (abrir app, hora, clima) → executa na hora, sem LLM.
3. Conclave (só se o senhor liga o ⚔️).
4. **`agent.respond()`** — cérebro com ferramentas (tool-use). Caminho único de
   conversa E ação desde a correção de hoje.
5. Fallback: Ollama local (offline quase sempre).

`agent.respond` cascata: Claude assinatura → OpenAI → Claude API → OpenRouter.
Tool-use pela assinatura = JSON em texto (Claude headless não tem function-call
nativo), parseado e executado por `_exec_tool`.

## Achados e o que foi feito

### ✅ CORRIGIDO — conversa prometia mas não executava (CRÍTICO)
Ver `_logs/2026-06-19_fix-conversa-nao-executava.md`. Removido o atalho que
mandava conversa pro cérebro de raciocínio (só promete). Validado AO VIVO hoje:
pedido "programe criar arquivo X" → `tools:['programar']` → executor rodou em
background → arquivo `_outbox/teste_orquestramento_19jun.txt` criado de verdade.

### ✅ CORRIGIDO — agente pulava a ferramenta e respondia de cabeça ("fingir que fez")
Sintoma: pedir análise do Fluxograma.pdf → respondia certo MAS `tools:[]` (não
abriu o arquivo, respondeu da memória/estado do projeto). Risco de inventar.
Fix em `agent._respond_claude_subscription`: REGRA DURA no system prompt — se o
senhor cita arquivo/URL/pedido de criar-executar/notas, OBRIGA a usar a
ferramenta (`analisar_arquivo`/`ler_pagina`/`programar`/`buscar_conhecimento`);
"responder de memória sobre o que está num arquivo é fingir que fez — proibido".
Validado AO VIVO: mesmo pedido agora → `tools:['analisar_arquivo']` (chama a
ferramenta). 71/71 testes passando.

### ⚠️ ABERTO — sem reserva de cérebro quando a assinatura falha/zera (decisão do Murillo)
`call_claude`/`call_openai` (usados por Conclave, file_analyzer, squads,
analyzers...) → assinatura; se voltar vazio, cai em `_call_ollama` → Ollama
offline → erro seco. Hoje o `analisar_arquivo` morreu assim. Desde a migração
18/06 (100% assinatura, sem OpenAI de reserva) não há rede de segurança boa.
Opções (decisão dele): (a) subir o Ollama com um modelo decente como reserva
real; (b) manter OpenAI só como fallback de emergência (não primário); (c)
deixar como está e conviver com o erro quando a cota some.

### ⚠️ ABERTO — markitdown não lê PDF que é imagem (diagrama)
O Fluxograma.pdf é um diagrama (imagem), markitdown extrai ~nada de texto, então
`analisar_arquivo` não tem o que analisar. Pra ler diagrama precisaria de visão
(OCR/modelo multimodal). Não é bug de orquestração — é limitação da ferramenta
pra esse tipo de arquivo. Pra fluxogramas, o caminho é mandar a IMAGEM pra um
modelo com visão, não markitdown.

### ℹ️ NOTA — voz (entrada/saída) ainda usa OpenAI, e está CERTO assim
`/transcribe` (Whisper/gpt-4o-transcribe) e TTS (`tts-1`) e `embed()` (embeddings
do knowledge) usam `OPENAI_API_KEY`. Isso NÃO é o "ChatGPT cérebro" que o senhor
mandou tirar — é I/O de voz e busca semântica, que a assinatura não oferece. Se
remover a OPENAI_API_KEY, a voz para de ouvir/falar. Manter.

### ℹ️ NOTA — latência alta da assinatura
Medido hoje: 34–52s por resposta (cold-start do subprocess `claude`). É o custo
de rodar tudo pela assinatura. Perceptível na voz.

## Prioridade sugerida pro próximo passo
1. Decidir a reserva de cérebro (item aberto 1) — é o que faz o Javis "ficar mudo".
2. Se quiser ler fluxogramas/prints: rota de visão pra imagem (separada do markitdown).
3. Latência: avaliar manter Haiku (mais rápido) no caminho principal de voz.

## Verificação
- `py_compile` agent.py/server.py — OK.
- `pytest tests/ -q` → 71 passed.
- 2 testes ao vivo (programar + analisar_arquivo) confirmaram o tool-use real.

Arquivo de prova deixado: `_outbox/teste_orquestramento_19jun.txt` (não apaguei).
**Sem commit/push — Murillo revisa e decide.**
