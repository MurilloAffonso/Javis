# Voz — corte de latência (Frente 3) — 17/06

## O que foi decidido

Baixar `required_misses` do Silero VAD de **24 para 12** em
`_ferramentas/voz-sandbox/conf.yaml` (`character_config.vad_config.silero_vad`).

Cada janela do VAD = 32ms (512 samples / 16000 Hz). `required_misses` é quantas
janelas consecutivas de silêncio o sistema exige antes de decidir que a fala
terminou e começar a processar (ASR → LLM → TTS).

- Antes: 24 × 32ms = **768ms** de espera fixa em toda interação.
- Agora: 12 × 32ms = **~384ms**. Corta ~0,4s de latência por interação.

## Por quê

Frente 3 = afinar voz (latência, exatidão, wake word). A latência tinha uma causa
raiz concreta e barata de corrigir: o tempo de silêncio pra fechar a fala estava
em 768ms. ASR já estava otimizado (faster_whisper small/int8/cpu, pt, prompt
mínimo) numa sessão anterior — não havia gordura óbvia ali.

## Alternativas consideradas

- Trocar modelo de ASR: descartado por ora — `small` já equilibra velocidade x
  exatidão em CPU; trocar arrisca regredir exatidão.
- Wake word ("Hey Javis"): NÃO existe no Open-LLM-VTuber (fluxo é push-to-talk +
  VAD). É feature nova (precisa motor de keyword-spotting tipo openWakeWord rodando
  contínuo antes do Whisper). Fica como próximo item da Frente 3, a decidir.

## Verificação

`python -c "import yaml; ..."` → YAML válido, required_misses=12, espera ~0.384s.
Teste auditivo ao vivo pendente (Murillo): reiniciar servidor de voz, falar com
pausas naturais. Se cortar a fala no meio de pausa curta, subir p/ 16 (~512ms).

## Próximo passo

1. Murillo testa o novo tempo ao vivo e dá feedback (rápido o bastante? corta no
   meio?).
2. Decidir se vale implementar wake word de verdade (openWakeWord) — mais trabalho.

**Sem commit/push — Murillo revisa e decide o que comita.**
