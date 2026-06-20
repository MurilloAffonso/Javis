# Voz no Haiku + contexto enxuto (velocidade/leveza em 1º lugar) — 18/06

## O que foi decidido

Murillo confirmou prioridade pra voz: **velocidade e leveza acima de tudo**, não
só economia. Antes ele tinha cogitado plugar o app/plano do ChatGPT direto na
voz — expliquei que não dá (app não tem interface programável, só Codex tem
CLI pela assinatura do ChatGPT, e Codex não tem streaming, seria pior). Decisão
final: continua só Claude, mas no modelo mais leve.

## Mudanças

**`claude_brain.py`**
- Novo `_VOICE_MODEL` (env `JAVIS_CLAUDE_VOICE_MODEL`, padrão
  `claude-haiku-4-5-20251001`) — separado do `_MODEL` (Opus, usado no
  raciocínio pesado de texto).
- `answer()` e `answer_stream()` agora aceitam `model=` opcional, sobrescrevendo
  o padrão por chamada.

**`server.py`** — os DOIS pontos de entrada da voz passam `model=_VOICE_MODEL`
(Haiku) e cortam o histórico injetado de 4 pra 2 trocas (`limit=2`):
1. `/voice` (streaming SSE, linha ~700) — também removi a injeção do
   `briefing.estado_resumido()` no contexto da voz (pesava o prompt sem ajudar
   bate-papo falado; ficava só no caminho de texto).
2. `/v1/chat/completions` (app de voz/VTuber, linha ~1353).

O caminho de **texto** (`_brain()`, usado por `/chat/stream` digitado) NÃO
mudou — continua no Opus (raciocínio mais forte), porque o pedido era
especificamente sobre a voz.

## Por quê

Murillo: digitando ele quer resposta completa; falando, quer rápido e leve,
sem pesar a cota da assinatura à toa com Opus em bate-papo simples.

## Alternativas consideradas

- Plugar o app do ChatGPT (plano Plus/Pro) na voz: IMPOSSÍVEL — app não expõe
  interface programável, só GUI manual.
- Codex (assinatura ChatGPT, via CLI) na voz: técnicamente possível mas sem
  streaming, 10-40s de silêncio por resposta — pior que o problema que estamos
  resolvendo.
- Manter Opus na voz: descartado — é o modelo mais pesado/lento, contrário à
  prioridade que o Murillo deu agora.

## Verificação

`python -c "import server; import claude_brain"` OK · `claude_brain._VOICE_MODEL`
= `claude-haiku-4-5-20251001` · `pytest tests/` 71/71.

Teste ao vivo pendente: Murillo falar e sentir se a resposta vem mais rápida
com o Haiku, e se a qualidade do papo continua boa o suficiente (Haiku é mais
simples que Opus — pode precisar reajustar se ficar "burro" demais pra
perguntas com mais substância).

## Próximo passo

1. Murillo testa ao vivo e compara a sensação de velocidade com o Opus de antes.
2. Se quiser meio-termo (mais inteligente que Haiku, mais rápido que Opus):
   trocar `JAVIS_CLAUDE_VOICE_MODEL` pra `claude-sonnet-4-6`.

**Sem commit/push — Murillo revisa e decide o que comita.**
