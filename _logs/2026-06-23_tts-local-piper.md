# Decisão: TTS local via Piper (frente "Voz local barata")

## O que foi decidido
A rota `/tts` do `server.py` agora usa **Piper local** (voz `pt_BR-faber-medium`,
qualidade média, ~60MB) como padrão — grátis, sem rede, sem chave. Cai pro
**OpenAI TTS pago** (`tts-1-hd`/`onyx`, já configurado) só se:
- o modelo Piper não estiver baixado/falhar (`tts_local.synthesize()` retorna `None`), ou
- o pedido vier com `voice`/`model` explícitos (Piper não tem essas vozes), ou
- `JAVIS_TTS_PROVIDER=openai` estiver setado no `.env`.

O ack/streaming de voz em tempo real (`_tts_sentence`/`_tts_ack`, usado no loop
de diálogo falado) **não foi tocado** — continua 100% OpenAI. A latência ali já
foi calibrada em sessão anterior (`2026-06-17_voz-latencia.md`); trocar o motor
desse caminho é um trabalho separado, não o desta frente.

O STT (`voice_bridge.py`) já era local (`faster-whisper`, CPU, int8, pt) desde
antes — não havia nada a fazer ali. A frente "voz local barata" do backlog, na
prática, só tinha o TTS pendente.

## Por quê
Mesma lógica da rota Gemini fechada antes: trocar custo recorrente por algo
local/grátis quando a qualidade é suficiente. `/tts` é usado pra falar respostas
de texto (não é o caminho de latência crítica), então a inferência onnxruntime
do Piper (CPU, ~1-2s pra uma frase) é aceitável.

## Como foi feito
- `pip install piper-tts` (wheel `cp39-abi3`, puro onnxruntime — funciona até no
  Python 3.14 deste ambiente, sem compilar nada).
- Modelo baixado de `huggingface.co/rhasspy/piper-voices` pra
  `backend/models/piper/pt_BR-faber-medium.onnx(.json)` — pasta já cobreta pelo
  `.gitignore` existente (`models/`, `*.onnx`).
- Novo módulo `backend/tts_local.py`: carrega o `PiperVoice` uma vez (cache em
  memória), sintetiza pra WAV em buffer, sem arquivo temporário.
- `server.py`: `/tts` tenta Piper primeiro (quando provider=piper, sem
  voice/model explícitos no request), senão segue pro fluxo OpenAI existente
  (inalterado).
- 7 testes novos em `tests/test_tts_local_offline.py`: ordem de fallback, 503
  sem nenhum provedor disponível, bypass por voice/model explícito, força via
  `JAVIS_TTS_PROVIDER=openai`, texto vazio, e **um teste com inferência real**
  (sem mock, pula se o modelo não estiver no disco — não depende de rede, só de
  arquivo local).
- Suíte completa: 138/138 passando (131 antes + 7 novos).

## Alternativas consideradas
- **Groq Whisper** (citado no item original do backlog) para STT — descartado:
  STT já está resolvido localmente, não havia problema a resolver aí.
- Trocar o ack/streaming também para Piper — descartado por ora: arriscaria a
  latência já calibrada do loop de voz em tempo real sem necessidade (essa rota
  não tem custo de API recorrente do jeito que o `/tts` batch tem).

## Próximo passo
Frente ativa fica livre — escolher o próximo item parqueado (OpenRouter deep /
Hermes mining / treinamento-redes / criativo).
