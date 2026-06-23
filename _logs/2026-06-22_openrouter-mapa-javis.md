# Mapa estratégico: OpenRouter × pilares do Javis

**Data:** 22/06/2026
**Contexto:** Murillo pediu uma fuçada no OpenRouter (modelos, Fusão, chat) cruzando
com TODOS os pilares do Javis: comando de voz, cérebro, editores de vídeo,
gerenciamento de página, editor de imagem/foto, gravação de conteúdo, carrossel
Vem Passear, criação de texto, análise, e o treinamento (IA monitorando
Instagram/TikTok/YouTube em alta).

---

## A verdade que orienta tudo

**OpenRouter é um *mercado de cérebros*, não um app.** Ele fornece o **modelo**
(texto, imagem, voz, frame de vídeo) mais barato/bom para cada tarefa. Mas o
editor de vídeo, o gerenciador de página e o monitor de redes sociais são
ferramentas/APIs **separadas** — o OpenRouter só fornece a inteligência que roda
dentro delas. "Ter modelo de imagem" ≠ "ser editor de imagem".

## Mapa pilar a pilar

| Pilar do Javis | OpenRouter dá (cérebro) | Ainda precisa (app/cano) | Encaixe |
|---|---|---|---|
| Comando de voz | TTS (Grok Voice/Voxtral) + STT via `/audio/speech` | Mic + orquestração (já existe) | 🟢 (mas local é + barato) |
| Cérebro texto/análise | Free (Llama 3.3 70B, Nex-N2-Pro) + DeepSeek V4 Flash | Nada — já plugado | 🟢🟢 melhor |
| Criação de texto / carrossel VP | Qualquer LLM (free serve) | — | 🟢 |
| Editor de imagem / foto | Nano Banana Pro / Nano Banana 2 (edita via prompt) | App de edição OU plugin | 🟡 ⚠️ regra Adobe/Canva |
| Editores de vídeo | LLM que pilota o editor | Descript / CapCut (o editor em si) | ⚪ OpenRouter ≠ editor |
| Gerenciamento de página | LLM pra escrever/decidir post | API Instagram/Meta/TikTok (postar) | ⚪ precisa APIs sociais |
| Treinamento (monitorar IG/TikTok/YT em alta) | LLM pra analisar + web_search/web_fetch (Fusão) | Cano de ingestão (scraper/API redes) | 🟡 cérebro sim, dados não |
| Conclave / decisão difícil | Fusão (painel + juiz, ~5× custo) | Já existe Conclave próprio | 🟡 referência |

## O 80/20

Dos 8 pilares, o OpenRouter resolve **limpo e barato só 3**: cérebro de texto,
criação de texto e (com ressalva) voz. Os outros 5 ele **não resolve sozinho** —
precisam de app (vídeo/imagem) ou de API social (gerenciamento/monitoramento).

Tradução: **OpenRouter = motor de inteligência do Javis, não a fábrica inteira.**

## Custos de referência (jun/2026)

- Free: Llama 3.3 70B, Nex-N2-Pro, Nemotron 3 Ultra, Cohere North Mini Code
  (rate-limit ~20/min, 200/dia, sem cartão). **IDs do test plan do Codex
  validados ao vivo: existem e são free.**
- Pago + barato: DeepSeek V4 Flash ~US$ 0,09/0,18 por milhão (in/out). US$ 1 ≈ 11M
  tokens de entrada. Sem markup por token; só 5,5% na compra de crédito.
- Voz cascata mínima: Groq Whisper v3 (~US$ 0,04/h ≈ grátis) ou faster-whisper
  local (US$ 0) + Piper TTS local (US$ 0). Ver análise de voz (Seção E.1 do
  RESERVATORIOS + esta).

## Alertas cravados

1. **Imagem/carrossel via Nano Banana conflita com a regra "criativo só via plugin
   Adobe/Canva".** Não usar sem Murillo revisar a regra antes.
2. **Monitorar redes "em alta" não é OpenRouter.** Exige cano de dados (API oficial
   ou scraper, com risco de ToS). OpenRouter entra só na análise do que o cano
   trouxe.

## Decisão / próximo passo

- **Ordem recomendada:** atacar primeiro o único 🟢🟢 — cérebro de texto grátis
  (Gemini free / Llama free na cascata). É o de maior valor e menor risco.
- **Teste grátis disponível (não autorizado ainda):** Nex-N2-Pro vs Llama 3.3 70B
  (free, US$ 0), 3 prompts sintéticos do test plan do Codex — exige aprovação
  explícita porque faz chamada de rede com a OPENROUTER_API_KEY.
- **Testar chat/Fusão ao vivo:** requer login do Murillo (gasta crédito da conta).

## Fontes

Navegação ao vivo em openrouter.ai/models (22/06) + pesquisas jun/2026 já citadas
no RESERVATORIOS.md (Seção E).
