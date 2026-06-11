# Checkpoint — antes de trocar ASR e melhorar intenções naturais

Data: 2026-06-11

---

## git status --short

Repositório sem commits. Todos os arquivos são untracked (??). Estado limpo.

---

## Problema observado no teste real

```
Transcribing audio input  (00:59:45)
User input: "Olá Javes, como é que tá o sistema?" (01:00:03)
```

- **Tempo de transcrição:** ~18s → confirma que `large-v3-turbo` em CPU é o gargalo
- **llm_dt=2250ms** → frase caiu no Ollama (deveria ir para status_sistema)
- **tts_queue_dt=8827ms**, **total_dt=39046ms**

Causa raiz do roteamento errado:
1. "Olá Javes" não é stripped — wake word não está na posição 0 do texto
2. "como é que tá o sistema?" → "como" está em CONVERSATION_HINTS → cai para "conversa"
3. Nenhum keyword de status_sistema corresponde à frase natural

---

## O que será alterado

| Arquivo | Mudança |
|---|---|
| `conf.yaml` | `large-v3-turbo` → `small` |
| `command_router.py` | Adicionar keywords naturais de status_sistema |
| `voice_bridge.py` | Melhorar strip: remover "Olá/Oi" + wake word no início |
| `single_conversation.py` | Respostas canned por intent (não genéricas) |
| Testes | Cobrir frases naturais com wake word e saudação |

---

## Confirmações de segurança

- ✅ dry_run continuará True (hard-coded em voice_bridge.py)
- ✅ Execução real por voz continuará bloqueada
- ✅ acao_perigosa continuará blocked/would_execute=False
- ✅ Nada será instalado
- ✅ Não será feito commit nem push
