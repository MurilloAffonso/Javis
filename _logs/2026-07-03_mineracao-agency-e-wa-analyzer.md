# Mineração The Agency + Analisador de WhatsApp + AEO

**Data:** 2026-07-03

## Contexto
Murillo mandou ~20 agentes do repo The Agency + gemini-cli. Análise completa feita
(ver memory/javis-agency-agents-veredito). Veredito: minerar, não adotar. 3 TIER 1
(capacidade nova): AEO, pipeline-analyst, discovery-coach. Pediu pra implementar o que
faz sentido + analisar conversas do WhatsApp + Gemini pra voz.

## Implementado
1. **Discovery-coach → responder_lead** (jampa_squad.py) — o gerador de resposta de
   WhatsApp (fluxo-dinheiro) agora QUALIFICA antes de propor: cumprimenta+preço, e
   TERMINA puxando data/pessoas/local. Regra: não inventa proposta no vácuo se falta
   dado essencial. (Minerado de sales-discovery-coach: SPIN/qualificar antes de pitchar.)

2. **Analisador de conversas do WhatsApp** (novo, o grande pedido dele):
   - `wa_analyzer.py` — parse_export (Android pt-BR + iOS + multi-linha, descarta linhas
     de sistema), basic_stats (contagem/período/pico), analyze (Claude assinatura →
     perfil de estilo, o que vende, onde leads travam/somem, clientes perdidos, rascunho
     voz-murillo.md), save_voice_doc → grava `_projetos/cerebro-jampa/voz-murillo.md`
     (vira grounding do squad).
   - `server.py`: POST /wa/analyze {text,me}, POST /wa/save-voice {content}.
   - `treino.js`: card "📱 Analisar conversas do WhatsApp" — cola o export, mostra
     análise + stats, botão "salvar como treino".
   - 100% LOCAL (Claude assinatura), nada publicado. Via EXPORT (.txt); WhatsApp ao
     vivo (OpenWA) = fase 2.

3. **AEO checklist** (entregável estratégico) — `_projetos/cerebro-jampa/aeo-checklist.md`:
   ser citado por ChatGPT/Gemini/Perplexity quando turista pergunta "o que fazer em JP".
   FAQ+schema, guias que casam com prompt, medir citação mensal. Encaixa na missão SEO.

## Verificado
- Sintaxe OK (wa_analyzer, jampa_squad, server); parser testado (5 msgs, sistema
  descartado, iOS+Android). Frontend verify 13 arquivos verde.
- **Precisa restart do server.py** (novo módulo + endpoints).

## Pendente — decisão do Murillo: Gemini para voz
gemini-cli é agente de código (ruim p/ latência de voz). O certo p/ comando de voz é
LLM rápido. Infra multi-cérebro JÁ existe (brain_switch claude/codex; openrouter_fallback).
Opções: (a) Gemini Flash API direto (grátis, aistudio.google.com, menor latência) —
precisa GEMINI_API_KEY; (b) Gemini via openrouter_fallback (já existe, 1 modelo a mais);
(c) modelo local Ollama (grátis+privado, latência = hardware). Aguardando escolha+chave.

## Não implementado (de propósito)
pipeline-analyst (precisa volume de leads reais p/ diagnosticar) e o resto = minerar
oportunista. WhatsApp ao vivo (OpenWA) = fase 2. Fase atual = operar.
