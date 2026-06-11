# Checkpoint — antes da análise do Silero VAD

Data: 2026-06-11

---

## git status --short

Repositório sem commits. Todos os arquivos são untracked (??).
Nenhuma alteração staged ou unstaged — estado limpo.

---

## Estado atual da voz

### Open-LLM-VTuber v1.2.1
- Sandbox em: `_ferramentas/voz-sandbox/`
- Porta: http://localhost:12393
- STT: faster-whisper large-v3-turbo (CPU, int8, pt)
- TTS: edge_tts pt-BR-FranciscaNeural
- LLM: Ollama llama3.2:3b
- **Pipeline validado:** voz → transcrição → LLM → fala (4 bugs corrigidos)
- **VAD:** frontend JavaScript (vad.js Silero v5) — parâmetros ajustados na sessão de debug
- **Backend VAD:** desabilitado
- **MCP/tools:** desabilitado (`use_mcpp: False`)
- **Proactive speak:** desabilitado (idleSecondsToSpeak: 120)

### voice_bridge.py
- Em `_apps/javis-local-interface/backend/voice_bridge.py`
- Modo: `dry_run = True` — classifica e loga, não executa
- 21/21 testes passando

### Testes gerais
- `tests/test_command_router.py`: 27/27
- `tests/test_voice_bridge.py`: 21/21
- Total: 48/48

---

## Pendência atual

**Conectar transcrição real do Open-LLM-VTuber ao voice_bridge.py em dry-run.**

Sequência pendente:
1. Usar sandbox de voz com falas reais
2. Testar voice_bridge com as mesmas frases manualmente
3. Revisar `logs/actions.jsonl` — confirmar intents corretos
4. Aprovação de Murillo → liberar execução low risk
5. Integrar `single_conversation.py` com voice_bridge

---

## Objetivo desta análise (Silero VAD)

Analisar o repositório snakers4/silero-vad e decidir:
1. Como pode melhorar a captação de voz do Javis
2. Se o VAD atual (vad.js frontend) está configurado de forma ótima
3. Qual é o plano de integração seguro sem quebrar o sandbox

**Restrições:**
- Não instalar nada sem aprovação
- Não alterar o sandbox de voz agora
- Não fazer commit nem push
