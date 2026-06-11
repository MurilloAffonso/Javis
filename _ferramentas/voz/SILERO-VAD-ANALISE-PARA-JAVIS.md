# Análise do Silero VAD para o Javis

Data: 2026-06-11  
Repositório: https://github.com/snakers4/silero-vad  
Clone em: `_referencias/silero-vad/`

---

## 1. O que é Silero VAD

Silero VAD é um detector de atividade de voz (Voice Activity Detector) de nível empresarial,
pré-treinado em mais de 6000 línguas. Diferencia fala de silêncio/ruído com alta precisão,
processando 1 chunk de áudio (~30ms) em menos de 1ms em CPU single-thread.

Licença: MIT. Sem telemetria, sem chaves, sem expiração.

---

## 2. Como ele detecta fala

- Modelo neural LSTM que processa janelas de 512 amostras (32ms) a 16000 Hz
- Retorna uma probabilidade de fala (0.0 a 1.0) por janela
- Tem máquina de estados interna: IDLE → ACTIVE (speech) → INACTIVE → IDLE
- Usa dupla verificação: **probabilidade neural** + **threshold de dB** (volume mínimo)
- Smoothing window evita oscilações rápidas

---

## 3. Formatos suportados

- Sample rates: **8000 Hz** e **16000 Hz** (nativo)
- Entrada: tensores PyTorch (Float32) ou ONNX runtime
- I/O de arquivo: via torchaudio (WAV, opus, etc.) ou soundfile
- Sem arquivo: pode rodar em chunks de áudio em streaming (via WebSocket)

---

## 4. Tem PyTorch?

Sim — dependência padrão: `torch>=1.12.0` + `torchaudio>=0.12.0`.

**Status no venv do sandbox:** `torch 2.10.0+cpu` ✅ instalado.  
`torchaudio`: ❌ NÃO instalado.  
`silero-vad` (pacote): ❌ NÃO instalado.

---

## 5. Tem ONNX?

Sim — opção alternativa sem torchaudio:
```
pip install silero-vad[onnx-cpu]  # adiciona onnxruntime
```
Permite rodar o modelo sem PyTorch puro, mas I/O de arquivo precisa ser implementado manualmente.
Para uso em streaming (WebSocket chunks), o ONNX é totalmente viável.

**O frontend do Open-LLM-VTuber já usa Silero VAD v5 via ONNX** (pacote `@ricky0123/vad-web` bundled em WASM).

---

## 6. Serve para CPU?

**Sim — projetado para CPU.** Em benchmarks oficiais:
- 1 chunk de 30ms: < 1ms em single CPU thread
- Modelo JIT: ~2MB
- ONNX pode ser 4-5x mais rápido que PyTorch em CPU

Para a GTX 1650 com 4GB VRAM (já ocupada pelo Ollama), CPU é o caminho certo.

---

## 7. Como pode melhorar o VAD atual do Javis

### Situação atual
O pipeline tem **dois níveis de VAD**:
1. **Frontend (browser):** `@ricky0123/vad-web` — Silero VAD v5 em WASM/ONNX, roda no browser
2. **Backend Python:** `vad_model: null` — Silero VAD desabilitado no `conf.yaml`

O frontend é o único VAD ativo agora. Ele detecta a fala no browser e manda o áudio para o backend só quando detecta fala. O backend VAD (quando ativo) serve para **interrupção**: detectar quando Murillo começa a falar enquanto o Javis está respondendo em voz.

### Melhorias possíveis

| Problema | Solução Silero |
|---|---|
| Frases curtas rejeitadas pelo browser | Ajustar `minSpeechFrames: 1` (já feito ✅) |
| Corte prematuro de fala | Ajustar `redemptionFrames` e `negativeSpeechThreshold` (já feito ✅) |
| Muito barulho de fundo captado | Habilitar backend Silero + `db_threshold` como filtro de volume |
| Interrupções não detectadas enquanto Javis fala | Habilitar backend Silero VAD (opção B) |
| Fala em português ainda misfirei | Ajustar `prob_threshold: 0.4 → 0.3` no backend para pt-BR |

---

## 8. Riscos de integrar agora

| Risco | Detalhe |
|---|---|
| Instalar `silero-vad` quebra o venv | Improvável — torch já instalado, mas não testado |
| `torchaudio` pode ser difícil de instalar (Windows) | Requer versão específica compatível com torch 2.10.0 |
| Backend VAD + frontend VAD podem entrar em conflito | Dois filtros em série podem rejeitar fala válida |
| `db_threshold: 60` pode ser alto demais para voz baixa | Se Murillo falar baixo, backend bloqueia mesmo com prob alta |
| Latência: VAD no backend acrescenta ~1ms por chunk | Negligível, mas adiciona uma camada |

---

## 9. O que deve ficar para depois

- Fine-tuning do modelo em português (requer dataset rotulado de voz brasileira)
- Substituição completa do frontend VAD pelo Python Silero (pipeline próprio — Opção C)
- Usar Silero VAD ONNX diretamente em `voice_bridge.py` para pré-filtrar transcrições ruins
- Torchaudio para I/O de arquivo (WAV analysis, testing)
