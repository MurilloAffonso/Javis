# Plano de Integração — Silero VAD no Javis

Data: 2026-06-11

---

## Contexto

O Open-LLM-VTuber **já tem** implementação Python do Silero VAD (`silero.py`).
O frontend **já usa** Silero VAD v5 (ONNX/WASM via `@ricky0123/vad-web`).
Ambas as camadas estão documentadas em `_ferramentas/voz/VAD-ATUAL-OPEN-LLM-VTUBER.md`.

---

## Opção A — Ajustar VAD atual sem instalar nada

**O que faz:** refinar os parâmetros do VAD frontend JavaScript que já está funcionando,
com base nos benchmarks do repositório Silero VAD e nos problemas observados em uso real.

**Arquivos afetados:**
- `frontend/assets/main-nu7uwxNJ.js` — ajuste dos thresholds (edit cirúrgico)

**Parâmetros candidatos a ajuste:**
```javascript
// Se ainda houver corte prematuro ou misfire:
negativeSpeechThreshold: 15   // (atual: 20 — reduzir mais)
redemptionFrames: 10          // (atual: 8 — aumentar levemente)
preSpeechPadFrames: 30        // (atual: 20 — mais contexto antes da fala)
```

**Quando ajustar:** somente se Murillo reportar que a voz ainda está sendo cortada ou rejeitada
após uso real do sandbox.

**Instalação necessária:** ❌ Nenhuma

**Mexe no sandbox:** mínimo — só o arquivo JS minificado (já foi editado antes com sucesso)

**Dificuldade:** baixa

**Risco:** baixo — o VAD já foi ajustado antes sem quebrar o pipeline

**Vale agora?** ✅ **Sim** — dependendo do feedback de uso real.

---

## Opção B — Habilitar backend Silero VAD Python (interrupção de voz)

**O que faz:** mudar `vad_model: null` → `vad_model: 'silero_vad'` no `conf.yaml`.
Isso ativa a detecção de voz no lado do servidor Python — usada principalmente para
**interrupção**: quando Murillo começa a falar enquanto o Javis ainda está respondendo em áudio.

**Arquivos afetados:**
- `conf.yaml` — 1 linha: `vad_model: null` → `vad_model: 'silero_vad'`
- Não toca nenhum arquivo Python

**Instalação necessária:** ✅ Requer aprovação de Murillo
```powershell
# Dentro do voz-sandbox:
uv add silero-vad
uv add torchaudio  # ou silero-vad[onnx-cpu] para versão sem torchaudio
```

**Tamanho do download:**
- `silero-vad`: ~2MB (modelo JIT)
- `torchaudio` (CPU): ~100-200MB
- Alternativa ONNX: `onnxruntime` (~50MB, sem torchaudio)

**Mexe no sandbox:** sim — instala pacotes no venv do voz-sandbox

**Dificuldade:** média — instalação em Windows pode ter problemas com torchaudio

**Risco:** médio
- Se `torchaudio` não instalar: silero.py falha silenciosamente ou trava o servidor
- Se `db_threshold: 60` for alto demais para a voz de Murillo: backend nunca detecta fala → interrupção não funciona
- Dois filtros em série (browser + Python) podem ser mais restritivos

**Vale agora?** ⏸ **Depois** — só após validar o pipeline atual com uso real e verificar
se a interrupção de voz é realmente necessária para o workflow de Murillo.

**Pré-requisito:** rodar `uv add silero-vad torchaudio` com aprovação explícita de Murillo.

---

## Opção C — Pipeline próprio: microfone → Silero VAD Python → Whisper → voice_bridge

**O que faz:** substituir o Open-LLM-VTuber por um pipeline Python construído do zero:
```
pyaudio → chunks de áudio
    │
    ▼
Silero VAD Python (silero-vad)
    │ fala detectada
    ▼
faster-whisper (já funcionando)
    │
    ▼
voice_bridge.py (já funcionando)
    │
    ▼
Command Router → actions → log
    │ (se conversa)
    ▼
Ollama via API direta
    │
    ▼
edge_tts → pyaudio
```

**Arquivos afetados:** novos arquivos em `_apps/` ou `_ferramentas/voz/`

**Instalação necessária:**
- `silero-vad` + `torchaudio` (ou `onnxruntime`)
- `pyaudio` (captura de microfone) — difícil no Windows sem portaudio
- Alternativa: `sounddevice` (mais fácil no Windows)

**Mexe no sandbox:** não toca o sandbox existente — pipeline paralelo novo

**Dificuldade:** alta — captura de microfone em Python no Windows tem armadilhas

**Risco:** alto para agora
- pyaudio/sounddevice no Windows requer compilação ou binários específicos
- Pipeline de áudio em tempo real é complexo (buffers, latência, threading)
- Substitui funcionalidade madura (Open-LLM-VTuber) por código novo não testado

**Vale agora?** ❌ **Não** — futuro quando o Javis estiver maduro o suficiente para
ter pipeline de voz próprio, desacoplado do Open-LLM-VTuber.

---

## Recomendação para Murillo

### Agora (sem instalar nada)

1. **Usar o sandbox atual** (Open-LLM-VTuber) com as configurações atuais do VAD frontend
2. **Observar** se há problemas de corte de fala ou misfire em uso real
3. **Se houver corte prematuro:** aplicar Opção A — ajustar thresholds do JS

### Próximo passo (com aprovação de instalação)

4. **Opção B (instalar silero-vad):** somente se a interrupção de voz for necessária
   - Aprovação de Murillo → `uv add silero-vad`
   - Testar: rodar sandbox, verificar se `conf.yaml → vad_model: 'silero_vad'` não quebra
   - Ajustar `db_threshold` conforme o volume da voz de Murillo

### Futuro (não agora)

5. **Opção C:** quando o Javis tiver seu próprio pipeline de voz desacoplado do VTuber

---

## Sequência recomendada (alinha com preferência de Murillo)

```
Fase 1: Ajustar VAD frontend se necessário (Opção A)
  ↓
Fase 2: Usar sandbox + voice_bridge dry-run — observar logs reais
  ↓
Fase 3: Aprovar instalação silero-vad → ativar backend VAD (Opção B)
  ↓
Fase 4 (futuro): Pipeline próprio com Silero + Whisper + voice_bridge (Opção C)
```

Esta sequência está alinhada com a preferência declarada de Murillo:
> 1. Primeiro ajustar VAD atual.
> 2. Depois testar Silero isolado.
> 3. Só depois integrar no pipeline próprio.
