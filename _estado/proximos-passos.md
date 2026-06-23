# Próximos Passos — Javis

**Atualizado:** 2026-06-23 (Gemini + voz local fechados; frente ativa LIVRE)

> Concluídos históricos: ver `git log` e `_logs/` datados. Aqui fica só o que está
> **vivo**.

---

## 🎯 FRENTE ATIVA (a única em foco agora)

**Nenhuma escolhida ainda.** Gemini e voz local fecharam (23/06) — ver em
"✅ Decidido" abaixo. Pela regra de 22/06 (uma frente por vez), o próximo passo
é Murillo escolher UM item de "🅿️ Parqueado" pra virar a próxima frente ativa.

---

## 🅿️ PARQUEADO (não disputa foco; pegar UM agora que a frente ativa abriu)

- **Treinamento/redes** — resumir vídeos do esquadrão; monitor de IG/TikTok/YT
  exige cano de dados próprio (não é OpenRouter).
- **Criativo** — só via plugin Adobe/Canva (regra). Nano Banana conflita; rever antes.

## ✅ Decidido (não disputa foco; já fechado)

- **Teste live OpenRouter** (23/06) — lote sintético, US$0, aprovado por Murillo.
  Achado-chave: os IDs free congelados em 22/06 **expiraram em 1 dia** (llama-3.3
  rate-limited, nex-n2 virou pago) → catálogo free é volátil, confirma a tese do
  Hermes. `openai/gpt-oss-120b:free` passou 3/3 (PT, tool-use, código). Gerou 3
  recomendações abertas (trocar default free; fallback multi-ID free; revisar
  override pago no .env). Detalhe: `_logs/2026-06-23_openrouter-teste-live.md`.
- **Voz local barata** (23/06) — STT já era local (faster-whisper, sem custo);
  faltava o TTS. Adicionado `tts_local.py` (Piper, voz `pt_BR-faber-medium`,
  ~60MB, gitignorado) como padrão grátis da rota `/tts`, com fallback automático
  pro OpenAI pago se o modelo faltar/falhar ou se vier voice/model explícito.
  Ack/streaming de voz em tempo real (`_tts_sentence`/`_tts_ack`) **não foi
  tocado** — fica no OpenAI (latência já calibrada, ver `2026-06-17_voz-latencia.md`).
  7 testes novos (1 com inferência onnxruntime real, sem mock). 138/138 passando.
- **Rota Gemini free na cascata** (23/06) — `_respond_gemini()` em
  `backend/agent.py`, encaixada entre Claude API e OpenRouter. Confirmada em
  produção com tool-calling real. Achado: `gemini-2.0-flash` tinha cota
  free-tier 0 nesta conta; default trocado pra `gemini-2.5-flash` (1.500
  req/dia grátis, funcionando). 131/131 testes passando na época (138/138 hoje).
  Detalhe:
  `_estado/estado-atual.md`.
- **Hermes Agent** — testado lado a lado (23/06), 4 pilares passaram. Veredito:
  **minerar, não adotar como substrato** (chassi genérico não substitui persona
  Jamba + pipeline VP + integração Cérebro Jampa). Achado extra do trace interno:
  guardrail anti-loop avisa mas não impede, e a resposta final escondeu uma
  dúvida que o próprio modelo tinha registrado no raciocínio — reforça não
  adotar. Trazer pro Javis quando der: padrão de fallback entre múltiplos
  modelos free (catálogo OpenRouter free é volátil — achado real do teste).
  Detalhe: `_logs/2026-06-23_hermes-veredito.md`.

## 🐞 Dívidas técnicas conhecidas

- Fallback do Ollama em `agent_runner.py` não cobre os 6 agentes de conclave/meta.
- Qualidade real de skills: só Architect e Developer validados via execução.

## ❌ Cancelado por decisão do Murillo

- ElevenLabs (voz por API paga) · Figma (board) · Obsidian como gestor (é só vault;
  gestão real é `_estado/`/`_logs/`).
- Reescrever do zero (22/06): descartado — a base funciona; faxina + foco em vez disso.
