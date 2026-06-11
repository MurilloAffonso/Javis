# Recomendação ASR — Latência de Voz

Data: 2026-06-11

---

## Modelo atual (após troca — 2026-06-11)

```yaml
faster_whisper:
  model_path: 'small'   # ← TROCADO de large-v3-turbo
  device: 'cpu'
  compute_type: 'int8'
  language: 'pt'
```

**Modelo anterior:** `large-v3-turbo` (~800MB, 4–10s/transcrição em CPU)  
**Modelo atual:** `small` (~150MB, 0.8–2s/transcrição em CPU)  
**Ganho esperado:** ~80% de redução na latência de transcrição

## Latência estimada em CPU (i5/i7 sem GPU)

| Modelo         | Tamanho | Latência ~1s de fala (CPU) | Qualidade pt-BR |
|----------------|---------|---------------------------|-----------------|
| large-v3-turbo | ~800MB  | **4–10s**                 | Excelente       |
| medium         | ~300MB  | 2–5s                      | Muito boa       |
| small          | ~150MB  | **0.8–2s**                | Boa             |
| base           | ~75MB   | **0.3–0.8s**              | Aceitável       |
| tiny           | ~40MB   | 0.1–0.3s                  | Fraca           |

## Análise do fluxo de voz atual

```
VAD (browser)         ~0–500ms    dependente de silêncio detectado
faster-whisper CPU    ~4–10s  ← GARGALO PRINCIPAL (large-v3-turbo)
Ollama llama3.2:3b    ~3–15s  ← GARGALO 2 (mas pode ser bypassado para comandos)
edge_tts              ~1–3s   dependente de rede
javis_hook            ~12ms   negligível
```

## Problema identificado

Para **comandos de voz curtos** ("abre o youtube", "toca música", "status"),
`large-v3-turbo` é superdimensionado — o texto já é simples e curto.

O Ollama era o segundo gargalo, mas **já foi eliminado** para comandos com o bypass
de LLM implementado em `single_conversation.py`. Para comandos, a latência agora é:

```
VAD + ASR + TTS (bypass) → sem Ollama
```

Isso reduz ~3–15s de Ollama para ~0ms para todos os intents de comando.

## Recomendação

### Para comandos curtos (sem alterar agora — requer aprovação)

Trocar `large-v3-turbo` → `small`:

```yaml
# conf.yaml — proposta (NÃO alterar sem aprovação de Murillo)
faster_whisper:
  model_path: 'small'   # era large-v3-turbo
  device: 'cpu'
  compute_type: 'int8'
  language: 'pt'
```

**Ganho esperado:** 4–10s → 0.8–2s por transcrição (redução de ~80%).  
**Risco:** small é menos preciso para sotaques e frases complexas.  
**Mitigação:** comandos são curtos e têm keywords específicas — small é suficiente.

### Para conversação (manter large-v3-turbo ou medium)

Se Murillo quiser qualidade máxima de transcrição para conversa longa:
- Manter `large-v3-turbo` para conversas
- Usar `small` apenas para comandos (exigiria lógica de troca dinâmica — mais complexo)

### Recomendação prática

Testar `small` primeiro:
1. Troca simples: 1 linha no `conf.yaml`
2. Se a qualidade de transcrição for aceitável para uso diário → manter `small`
3. Se houver erros de transcrição em frases complexas → voltar para `medium`

## Ordem de aprovação sugerida

1. ✅ **Bypass de LLM para comandos** — JÁ IMPLEMENTADO (maior ganho imediato)
2. ⏸ **Trocar ASR para `small`** — aguarda aprovação de Murillo
3. ⏸ **Trocar ASR para `medium`** — alternativa conservadora se `small` falhar

## O que NÃO fazer

- NÃO trocar para `tiny` — qualidade insuficiente para português
- NÃO usar `base` — margem de erro alta para português falado naturalmente
- NÃO instalar torchaudio para Silero VAD backend — não é o gargalo
- NÃO alterar sem aprovação de Murillo
