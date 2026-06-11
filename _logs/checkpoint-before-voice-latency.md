# Checkpoint — antes da otimização de latência de voz

Data: 2026-06-11

---

## git status --short

Repositório sem commits. Todos os arquivos são untracked (??) — estado limpo.

---

## Ponto atual do projeto

| Componente | Estado |
|---|---|
| Command Router | ✅ 27/27 testes |
| voice_bridge.py | ✅ 21/21 testes, dry_run=True |
| javis_voice_bridge_hook.py | ✅ criado, isolado, nunca lança exceção |
| single_conversation.py | ✅ hook conectado (linha 98-100) |
| Pipeline voz | ✅ validado end-to-end |

## Problema identificado

**Voz demorando para responder.** Hipótese: latência não está no hook/voice_bridge
(que é keyword-matching puro), mas nos estágios do pipeline:

```
VAD (browser)           → ~0-500ms (depende do silêncio detectado)
faster-whisper (CPU)    → ~2-8s    ← CANDIDATO #1 (large-v3-turbo em CPU)
Ollama (llama3.2:3b)    → ~3-15s  ← CANDIDATO #2 (especialmente para respostas longas)
edge_tts (online)       → ~1-3s
javis_hook              → <5ms    (keyword matching, sem LLM)
```

## Objetivo

1. Medir latência por etapa com logs de tempo
2. Bypassar Ollama quando o hook identificar um comando local (não conversa)
3. Normalizar wake words (Javis, Jarvis, Javes, Diabes, Diaves, Chaves)
4. Avaliar troca de modelo ASR para comandos (large-v3-turbo → small/base)

## Restrições ativas

- NÃO liberar execução por voz
- NÃO alterar dry_run para false
- NÃO executar actions.py por voz
- NÃO mexer no Open WebUI / Docker / Ollama sem aprovação
- NÃO instalar nada sem aprovação
- NÃO fazer commit nem push
- Manter tudo logado
- Manter comandos perigosos bloqueados
