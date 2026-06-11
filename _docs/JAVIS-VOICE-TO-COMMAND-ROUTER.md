# Javis — Voice-to-Command Router

Data: 2026-06-11 (atualizado: 2026-06-11)
Status: Fase 1 — dry-run ativo, bypass de LLM para comandos, execução não liberada

---

## 1. Como a voz vira comando (estado atual)

```
Usuário fala "Javis, abre o youtube"
    │
    ▼
faster-whisper (CPU, pt)    ← Open-LLM-VTuber porta 12393
    │ transcrição: "Javis, abre o youtube"
    ▼
javis_voice_bridge_hook.py  ← _ferramentas/voz-sandbox/ (~12ms)
    │ _strip_wake_word()     ← remove "Javis," → "abre o youtube"
    ▼
voice_bridge.classify_voice()
    │ command_router.route() → intent=abrir_youtube, risk=low
    │ logger.log(source="voice", dry_run=True)
    ▼
single_conversation.py (bypass de LLM)
    ├── intent == comando? SIM → SentenceOutput(canned_text) → edge_tts
    └── intent == conversa/desconhecido? → Ollama → edge_tts
```

**Fase 1 (atual):**
- Hook classifica e loga (dry_run=True, nunca executa)
- Comandos bypassam o Ollama — resposta canned via TTS (~3–10s economizados)
- Wake words reconhecidas: Javis, Jarvis, Javes, Diabes, Diaves, Chaves

**Fase 2 (futura):** ações com `risk_level: low` e `requires_approval: false` executam.  
**Fase 3 (futura):** ações com `requires_approval: true` exigem confirmação antes de executar.

---

## 2. Por que a primeira fase é dry-run

- Voz é ambígua. "apaga isso" pode não significar deletar — mas o Command Router trata como `acao_perigosa`.
- O pipeline de transcrição (faster-whisper em CPU) pode cometer erros em palavras curtas ou sotaque.
- É mais seguro observar os logs antes de liberar execução.
- Murillo precisa validar que o roteamento está correto para seu vocabulário real antes de conectar a execução.

---

## 3. Como testar manualmente

```powershell
# Testar via voice_bridge diretamente
cd _apps/javis-local-interface
python backend/voice_bridge.py "abre o youtube"
python backend/voice_bridge.py "Javis, status do sistema"
python backend/voice_bridge.py "apaga meus arquivos"

# Testar o hook (mede o tempo)
cd _ferramentas/voz-sandbox
python javis_voice_bridge_hook.py "Javis, abre o youtube"
python javis_voice_bridge_hook.py "apaga meus arquivos"

# Ver o log gerado
type _apps\javis-local-interface\logs\actions.jsonl
```

**Saída esperada:**
```json
{
  "source": "voice",
  "transcript": "abre o youtube",
  "intent": "abrir_youtube",
  "risk_level": "low",
  "requires_approval": false,
  "action": "open_url",
  "dry_run": true,
  "would_execute": true,
  "reason": "palavra-chave 'youtube' detectada"
}
```

---

## 4. O que pode ser liberado depois

Quando dry_run for desativado (Fase 2), ações elegíveis para execução automática por voz:

| Intent | Ação | Motivo |
|--------|------|--------|
| `abrir_youtube` | `open_url` | Só abre URL, sem efeito colateral |
| `tocar_musica` | `open_url` | Só abre URL |
| `abrir_openwebui` | `open_url` | Só abre URL local |
| `abrir_navegador` | `open_browser` | Reversível |
| `status_sistema` | `check_status` | Só lê, não escreve |
| `registrar_ideia` | `write_file` | Escreve em `_ideias/` — baixo risco |
| `conversa` | `llm_chat` | Redireciona ao LLM |

**Condição para liberar:** Murillo validar os logs e aprovar explicitamente.

---

## 5. O que continua proibido por voz (sempre)

- `acao_perigosa`: deletar, formatar, instalar, `rm -rf`, `git push`, etc. → **sempre bloqueado, para sempre**
- `abrir_terminal`: requer aprovação humana explícita — impossível por voz na Fase 2
- Shell arbitrário: fora da whitelist de `actions.py` — nunca executado
- Qualquer ação fora do Javis (`C:\Users\noteacer\Desktop\javis`)

---

## 6. Fluxo futuro completo

```
Open-LLM-VTuber (porta 12393)
    │
    ├── [STT] faster-whisper (CPU, int8, pt)
    │         └── texto transcrito
    │                  │
    │                  ▼
    │         voice_bridge.py
    │                  │
    │                  ▼
    │         command_router.route(texto)
    │                  │
    │         ┌────────┴────────────────┐
    │         │                         │
    │    risk: low                 risk: critical
    │    requires_approval: false  (acao_perigosa)
    │         │                         │
    │    Fase 2: executa          sempre bloqueado
    │    actions.execute()              │
    │         │                         │
    │    logger.log(source="voice")  logger.log(approved=False)
    │         │
    │    (resultado + log → frontend / terminal)
    │
    └── [LLM] Ollama (llama3.2:3b) ← intent: conversa
              │
         [TTS] edge_tts pt-BR-FranciscaNeural
              │
         usuário ouve a resposta
```

**Integração já ativa** em `single_conversation.py` (linha 97+):
```python
# Após transcrição:
hook_result = _javis_hook.process(input_text) if _javis_hook else None

# LLM bypass para comandos:
_bypass = hook_result and hook_result.get("intent") not in ("conversa", "desconhecido")

if _bypass:
    canned = "Modo teste: eu executaria '...'. Execução por voz ainda não liberada."
    bypass_output = SentenceOutput(DisplayText(text=canned), tts_text=canned, actions=Actions())
    full_response = await process_agent_output(output=bypass_output, ...)  # TTS direto
else:
    # fluxo normal via Ollama
    agent_output_stream = context.agent_engine.chat(batch_input)
    ...
```

**Logs de latência** disponíveis em tempo real no terminal do servidor:
```
[javis] intent=abrir_youtube risk=low hook_dt=12ms
[javis] bypass_tts_dt=1800ms
[javis] tts_queue_dt=1950ms
[javis] total_dt=7200ms
```

---

## 7. Consistência de intents

O sistema tem **três fontes** que declaram intents. Uma fonte é autoritativa; as outras devem refletir ela.

| Fonte | Papel | Autoritativa? |
|-------|-------|---------------|
| `backend/command_router.py` — `RISK_MAP` + `ACTION_MAP` | lógica real de roteamento | **SIM** |
| `config/commands.yaml` | documentação para humanos | não — deve espelhar o backend |
| `frontend/app.js` — `RISK` + `RULES` + `MESSAGES` | UI de exibição | não — deve espelhar o backend |

### Intents atuais (13)

`acao_perigosa`, `abrir_javis`, `abrir_navegador`, `abrir_openwebui`, `abrir_projeto`,
`abrir_terminal`, `abrir_vscode`, `abrir_youtube`, `conversa`, `desconhecido`,
`registrar_ideia`, `status_sistema`, `tocar_musica`

### Como detectar divergências

O teste `tests/test_intent_consistency.py` compara `RISK_MAP` e `ACTION_MAP` do backend
contra o YAML campo a campo (`risk_level`, `requires_approval`, `action`).
Qualquer divergência gera FAIL e bloqueia o merge.

```powershell
cd _apps/javis-local-interface
python tests/test_intent_consistency.py
```

### Divergência atual conhecida — frontend

`abrir_projeto` está no backend e no YAML mas **ausente** em `frontend/app.js`
(não aparece em `RULES`, `RISK` nem `MESSAGES`). O frontend usa `MESSAGES["desconhecido"]`
como fallback para esse intent. Será corrigido em etapa futura; não bloqueia execução por voz.

### Regra de manutenção

Ao adicionar um novo intent:
1. Adicionar em `command_router.py` — `RULES`, `RISK_MAP`, `ACTION_MAP`, `_reason()`
2. Atualizar `config/commands.yaml` com `risk_level`, `requires_approval`, `action`
3. Rodar `test_intent_consistency.py` — deve passar antes de qualquer commit

---

## Arquivos relacionados

- `backend/voice_bridge.py` — ponte de voz (dry-run)
- `backend/command_router.py` — classificador de intenção (fonte de verdade)
- `backend/actions.py` — executor de ações (whitelist)
- `backend/logger.py` — JSONL logger com rotação diária
- `config/commands.yaml` — documentação dos intents (espelha o backend)
- `logs/actions-YYYY-MM-DD.jsonl` — histórico diário de classificações
- `tests/test_intent_consistency.py` — guarda consistência backend ↔ YAML
- `_ferramentas/voz-sandbox/` — Open-LLM-VTuber (ainda separado)
- `_ferramentas/voz/STATUS.md` — status do sandbox de voz
