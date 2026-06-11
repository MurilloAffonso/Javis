# VAD Atual — Open-LLM-VTuber

Data: 2026-06-11  
Sandbox: `_ferramentas/voz-sandbox/`

---

## Arquivos encontrados

| Arquivo | Função |
|---|---|
| `frontend/assets/main-nu7uwxNJ.js` | Bundle React + VAD frontend (minificado) |
| `frontend/libs/vad.worklet.bundle.min.js` | AudioWorklet do VAD (processa áudio em thread separada) |
| `src/open_llm_vtuber/vad/silero.py` | Backend Silero VAD Python (implementado, desabilitado) |
| `src/open_llm_vtuber/vad/vad_factory.py` | Factory que instancia o VAD backend |
| `src/open_llm_vtuber/vad/vad_interface.py` | Interface abstrata do VAD |
| `conf.yaml` linhas 455–466 | Configuração do VAD backend |

---

## Parâmetros atuais

### Frontend (browser — vad.js Silero v5 via ONNX/WASM)

Configurado em `main-nu7uwxNJ.js` — já ajustado na sessão de debug:

```javascript
DEFAULT_VAD_SETTINGS = {
  positiveSpeechThreshold: 30,   // era 50 — mais sensível agora
  negativeSpeechThreshold: 20,   // era 35 — mantém fala por mais tempo
  redemptionFrames: 8            // era 35 — cicla mais rápido
}

dist.MicVAD.new({
  model: "v5",
  preSpeechPadFrames: 20,        // ~640ms antes da fala
  minSpeechFrames: 1,            // era 3 — aceita frases curtas (~96ms)
  ...
})

defaultSettings = {
  allowProactiveSpeak: false,     // era true — desabilitado
  idleSecondsToSpeak: 120,        // era 5
  allowButtonTrigger: false
}
```

**Biblioteca:** `@ricky0123/vad-web` — Silero VAD v5 empacotado como WASM.
A biblioteca é bundlada diretamente no `main-nu7uwxNJ.js` e `vad.worklet.bundle.min.js`.

### Backend Python (desabilitado — `vad_model: null`)

Em `conf.yaml` linhas 456–466:
```yaml
vad_config:
  vad_model: null   # ← DESABILITADO

  silero_vad:
    orig_sr: 16000
    target_sr: 16000
    prob_threshold: 0.4       # threshold neural (0.4 = moderado)
    db_threshold: 60          # threshold de volume (int16 scale)
    required_hits: 3          # ~96ms para confirmar fala
    required_misses: 24       # ~768ms de silêncio para encerrar
    smoothing_window: 5       # suavização por janela deslizante
```

Para habilitar: mudar `vad_model: null` → `vad_model: 'silero_vad'`

**Dependências necessárias (NÃO instaladas):**
- `silero-vad` — NÃO instalado
- `torchaudio` — NÃO instalado
- `torch` — ✅ já instalado (2.10.0+cpu)

---

## Como o VAD frontend funciona (vad.worklet.bundle.min.js)

1. `AudioWorkletProcessor` captura áudio do microfone a 16kHz
2. Reamostrador converte para 512 samples (32ms) por frame
3. Frames enviados ao main thread via `postMessage`
4. Main thread passa para o Silero v5 ONNX → probabilidade de fala
5. Se prob >= `positiveSpeechThreshold/100` → inicia acumulação
6. Se prob < `negativeSpeechThreshold/100` por `redemptionFrames` consecutivos → encerra

Mensagens geradas: `SPEECH_START`, `SPEECH_END`, `VAD_MISFIRE`, `SPEECH_REAL_START`

---

## Problemas observados (histórico da sessão)

| Problema | Causa | Fix aplicado |
|---|---|---|
| `VAD_MISFIRE` em frases curtas | `minSpeechFrames: 3` (288ms mínimo) | `minSpeechFrames: 1` ✅ |
| Fala cortada muito rápido | `redemptionFrames: 35`, `negativeSpeechThreshold: 35` | ambos reduzidos ✅ |
| Dificuldade em detectar voz baixa | `positiveSpeechThreshold: 50` | reduzido para 30 ✅ |
| Proactive speak disparando todo 5s | `localStorage` sobrepondo defaults JS | localStorage limpo + default 120s ✅ |

---

## Sugestões de ajuste (sem alterar agora)

### Frontend (tunagem adicional)
Se ainda houver problemas de corte prematuro:
```javascript
negativeSpeechThreshold: 15    // reduzir mais (atual: 20)
redemptionFrames: 10           // aumentar um pouco (atual: 8)
preSpeechPadFrames: 30         // mais contexto antes da fala (atual: 20)
```

### Backend (se habilitado — requer instalação)
Se barulho de fundo for problema:
```yaml
prob_threshold: 0.3    # aceita fala com menos certeza (atual: 0.4)
db_threshold: 50       # volume mínimo menor (atual: 60)
required_hits: 2       # confirma fala mais rápido (atual: 3)
```

**Nota sobre `db_threshold`:** o valor `60` no código corresponde a `20*log10(rms)` onde
`rms` é na escala int16 (×32767). Isso significa que o sinal deve ter amplitude RMS >= 1000/32767 ≈ 3%.
Para voz baixa, pode ser necessário reduzir para `50` (RMS >= 316/32767 ≈ 1%).

---

## Fluxo atual do pipeline de voz

```
Microfone (browser)
    │
    ▼
AudioWorklet (16kHz, 32ms frames)
    │
    ▼
Silero VAD v5 (ONNX/WASM no browser)  ← ATIVO ✅
    │ speech detected
    ▼
Buffer de áudio acumulado (WAV)
    │
    ▼
WebSocket → backend Python
    │
    ▼
faster-whisper (CPU, large-v3-turbo, pt)
    │
    ▼
Texto transcrito
    │
    ▼
Ollama (llama3.2:3b)  ← [voice_bridge futura entrada aqui]
    │
    ▼
edge_tts (pt-BR-FranciscaNeural)
    │
    ▼
Backend Silero VAD  ← DESABILITADO (interrupção quando Javis fala)
    │
    ▼
Browser (fala)
```
