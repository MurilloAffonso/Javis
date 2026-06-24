# Decisão: cérebro de conversa rápida (Gemini grátis no passo 0)

## Sintoma relatado
Murillo: a conversa do Javis "dá servidor offline e demora pra responder".

## Diagnóstico (medido, não chutado)
- Servidor estava ONLINE (porta 8000 respondia). Não era queda.
- `/chat` real levava **25s** pra um "oi". A UI, esperando tanto (ou piscando num
  restart), mostra "Servidor offline" (`app.js:466`, que dispara em TypeError de
  conexão).
- Causa raiz: todo chat passa por `agent.respond()`, que começava SEMPRE no
  **Claude por assinatura** (Claude Code headless). O gargalo NÃO é o modelo
  (já é Haiku 4.5, o mais rápido) — é o **cold-start do subprocess do Claude Code**
  (~20s por chamada, independente do modelo).

## Solução
Passo 0 em `agent.respond()`: conversa LEVE → **Gemini grátis primeiro** (HTTP
direto, sem subprocess). Pedido PESADO (gatilhos `_HEAVY_HINTS`: "pensa a fundo",
"debate", "prós e contras"...) pula o Gemini e vai direto pro Claude assinatura
(cérebro forte, que sobe pra Opus via `pensar_profundo`). Gemini ainda chama
ferramentas (incl. `pensar_profundo`) quando a própria mensagem leve precisar.

Configurável: `JAVIS_CHAT_FAST_BRAIN=claude` volta ao comportamento antigo
(Claude assinatura primeiro). Sem `GEMINI_API_KEY`, o passo 0 não dispara.

## Resultado medido
| Caso | Antes | Depois |
|---|---|---|
| "oi" (conversa leve) | ~25s (Claude headless) | **~2s warm** (Gemini), 3.6s cold |
| "pensa a fundo..." (pesado) | ~25s+ | ~110s (Opus via pensar_profundo) — correto, é o caminho pesado |

Custo: **US$0** (Gemini tier grátis). Persona Jamba preservada ("Olá, senhor...").

## Testes
4 testes offline novos em `test_llm_fallback_offline.py`: chat leve usa Gemini
primeiro (fallback_used=False, não toca Claude); pedido pesado pula Gemini;
`JAVIS_CHAT_FAST_BRAIN=claude` desliga; sem key usa Claude. Os 2 testes de
fallback existentes foram isolados com `JAVIS_CHAT_FAST_BRAIN=claude` (testam o
caminho de fallback, não o passo 0). Suíte: **142/142**.

## ⚠️ Pendência operacional
O servidor em execução foi iniciado ANTES das mudanças de hoje — roda código
antigo. **Nada disto (nem Gemini, nem TTS local, nem atualizar_memoria, nem este
fast-brain) está ativo na UI até reiniciar o backend:**
`python backend/server.py` (parar o atual antes).

## Próximo passo
Reiniciar o backend e validar na UI real. Depois, commitar este bloco.
