# Checkpoint — antes da integração voice hook

Data: 2026-06-10

---

## Estado dos testes

- `test_command_router.py`: 27/27 ✅
- `test_voice_bridge.py`: 21/21 ✅
- Total: **48/48 passando**

---

## git status

Repositório sem commits. Todos os arquivos são untracked (??).
Estado limpo — sem staged, sem unstaged.

---

## Arquivos relevantes

| Arquivo | Estado |
|---|---|
| `_apps/javis-local-interface/backend/command_router.py` | ✅ estável (27/27) |
| `_apps/javis-local-interface/backend/voice_bridge.py` | ✅ estável (21/21), dry_run=True |
| `_apps/javis-local-interface/backend/logger.py` | ✅ aceita extra={} |
| `_apps/javis-local-interface/logs/actions.jsonl` | destino dos logs de voz |
| `_ferramentas/voz-sandbox/src/open_llm_vtuber/conversations/single_conversation.py` | alvo de modificação mínima (linha 84) |

---

## Ponto de integração identificado

**Arquivo:** `_ferramentas/voz-sandbox/src/open_llm_vtuber/conversations/single_conversation.py`  
**Linha:** 84  
**Código atual:**
```python
logger.info(f"User input: {input_text}")
```

Aqui `input_text` contém o texto transcrito pelo faster-whisper.  
O hook será inserido APÓS esta linha.

---

## O que será criado

**`_ferramentas/voz-sandbox/javis_voice_bridge_hook.py`**
- Recebe texto transcrito
- Chama `voice_bridge.classify_voice()` via import direto
- Nunca trava o servidor (try/except total)
- Sempre dry_run=True
- Loga em `_apps/javis-local-interface/logs/actions.jsonl`

---

## Restrições ativas

- NÃO instalar silero-vad
- NÃO instalar torchaudio
- NÃO habilitar backend VAD
- NÃO liberar execução por voz
- NÃO mudar dry_run para false
- NÃO mexer no Open WebUI
- NÃO mexer no Docker
- NÃO alterar Ollama
- NÃO reativar MCP/tools no Open-LLM-VTuber
- NÃO fazer commit
- NÃO fazer push
- NÃO apagar arquivos
