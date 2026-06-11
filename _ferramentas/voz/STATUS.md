# Status do Sandbox de Voz — Javis
Data: 2026-06-10

## Stack ativa
- Open-LLM-VTuber v1.2.1
- Porta: http://localhost:12393
- STT: faster-whisper large-v3-turbo (pt)
- TTS: edge_tts — pt-BR-FranciscaNeural
- LLM: Ollama llama3.2:3b
- VAD: frontend (vad.js Silero v5) + backend desabilitado

## Diagnóstico inicial (19:17-19:19)
- ✅ Servidor subiu sem erros críticos
- ✅ WebSocket aceito, Live2D mao_pro carregado
- ✅ faster-whisper carregado (modelo baixado ~800MB)
- ✅ edge_tts inicializado
- ⚠️ MCP `time` falhou na 1ª tentativa → reconectou na 2ª (não crítico)
- ❌ VAD do frontend rejeitou áudio como "too brief" antes de enviar ao backend
- ✅ "thinking/speaking" apareceu em tentativa posterior (ciclo parcialmente funcional)

## Problema identificado: vadMisfire
- Origem: `frontend/assets/main-nu7uwxNJ.js` — função `VADProvider`
- Parâmetros estavam muito restritivos para português falado naturalmente
- Configuração anterior (defaults hardcoded):
  ```
  positiveSpeechThreshold: 50  → 0.50 (limiar alto de detecção)
  negativeSpeechThreshold: 35  → 0.35
  redemptionFrames: 35         → janela grande de "resgate"
  minSpeechFrames: 3           → mínimo de ~288ms de fala (hardcoded na lib)
  ```

## Ajuste aplicado (2026-06-10)
Arquivo: `frontend/assets/main-nu7uwxNJ.js`

### Mudança 1 — DEFAULT_VAD_SETTINGS
```diff
- DEFAULT_VAD_SETTINGS={positiveSpeechThreshold:50,negativeSpeechThreshold:35,redemptionFrames:35}
+ DEFAULT_VAD_SETTINGS={positiveSpeechThreshold:30,negativeSpeechThreshold:20,redemptionFrames:8}
```
- `positiveSpeechThreshold: 50 → 30` — detecta fala com menor confiança (mais sensível)
- `negativeSpeechThreshold: 35 → 20` — prolonga o segmento de fala (menos falsos fins)
- `redemptionFrames: 35 → 8` — janela de recuperação menor, ciclo mais ágil

### Mudança 2 — minSpeechFrames na inicialização do MicVAD
```diff
- dist.MicVAD.new({model:"v5",preSpeechPadFrames:20,...
+ dist.MicVAD.new({model:"v5",preSpeechPadFrames:20,minSpeechFrames:1,...
```
- `minSpeechFrames: 3 → 1` — aceita frases a partir de ~96ms (antes exigia ~288ms)
- Esta é a correção **principal** — o `vadMisfire` era disparado por frases curtas

## Nota sobre localStorage
Se o browser já tiver `vadSettings` salvo em localStorage, os novos defaults não
serão usados automaticamente. Para forçar: abra DevTools → Application → Local Storage
→ localhost:12393 → delete a chave `vadSettings` → recarregue a página.

## Diagnóstico sessão de debug (2026-06-10 ~19:24)

### Bug 1 — Loop MCP (travamento em "Thinking...")
- **Sintoma:** Texto digitado ("oi") fica preso em "Thinking..." por minutos
- **Causa raiz:** `use_mcpp: True` + `llama3.2:3b` → model entra em loop infinito de tool calls
  - 4+ chamadas consecutivas ao DuckDuckGo para query "oi"
  - `llama3.2:3b` não tem capacidade de raciocinar quando parar de chamar tools
- **Evidência no log:** linhas 507–592 — 4 rounds de `search` sem nunca responder
- **Fix aplicado:** `use_mcpp: False`, `mcp_enabled_servers: []`

### Bug 2 — faster-whisper sem CUDA (ASR falha em voz)
- **Sintoma:** Entrada de voz falha com RuntimeError
- **Causa raiz:** `device: 'auto'` → tenta CUDA → `cublas64_12.dll not found`
  - Máquina não tem CUDA 12 instalado
- **Evidência no log:** linha 597–619 — `RuntimeError: Library cublas64_12.dll is not found`
- **Fix aplicado:** `device: 'cpu'`

### edge_tts isolado
- ✅ Funcionou perfeitamente: `pt-BR-FranciscaNeural`, 23040 bytes gerados
- Não é o gargalo

### Ollama direto
- ✅ Responde corretamente fora da interface

## Correções aplicadas em conf.yaml (2026-06-10)

```diff
# Bug 1 — MCP desabilitado
- use_mcpp: True
- mcp_enabled_servers: ["time", "ddg-search"]
+ use_mcpp: False
+ mcp_enabled_servers: []

# Bug 2 — faster-whisper forçado para CPU
- device: 'auto'
+ device: 'cpu'
```

## Status geral — VALIDADO ✅ (2026-06-10 22:40)

| Check | Status |
|---|---|
| Texto → Ollama → resposta | ✅ |
| Microfone → faster-whisper (CPU, pt) | ✅ |
| Ollama → resposta em português | ✅ |
| edge_tts → fala pt-BR-FranciscaNeural | ✅ |
| Proactive speak desabilitado | ✅ |
| Chat history limpo | ✅ |
| AssertionError WebSocket race condition | ✅ corrigido |

Pipeline completo funcionando: **voz → transcrição → LLM → fala**

---

## isair/jarvis — Decisão final (2026-06-10)

**Hardware verificado:** GTX 1650 — 4 GB VRAM total, ~1.4 GB livre (Ollama ativo)  
**Requisito mínimo do isair/jarvis:** 8 GB VRAM  
**Decisão: não instalar neste hardware.**

isair/jarvis permanece como **referência de arquitetura** para:
- Wake word em qualquer posição na frase
- Ditado offline com `Ctrl+Win` (qualquer app)
- Piper TTS (offline, sem dependência de internet)
- Memory digest (compressão de contexto para modelos pequenos)
- Tool routing por embedding (evita loop como o nosso bug 1)
- Privacy hardening (redação automática de dados sensíveis)

**Análise completa:** `_ferramentas/repositorios-avaliados-v2.md`

---

## Prioridades atuais do sandbox de voz

1. **Estabilizar Open-LLM-VTuber** — pipeline validado ✅ (voz → transcrição → LLM → fala)
2. **Manter Whisper em CPU** — `device: 'cpu'`, GTX 1650 não tem VRAM para rodar em GPU junto com Ollama
3. **MCP/tools desligados** — `use_mcpp: False`, `mcp_enabled_servers: []` — não reativar com llama3.2:3b
4. **Busca web desligada por padrão** — modelos pequenos não sabem quando parar de buscar

## Integração com Command Router — status

**voice_bridge.py criado em:** `_apps/javis-local-interface/backend/voice_bridge.py`  
**Modo atual:** dry_run = True (classifica e loga, não executa nada)  
**Documentação:** `_docs/JAVIS-VOICE-TO-COMMAND-ROUTER.md`

### O que está funcionando
- [x] Transcrição de voz (faster-whisper, CPU, pt)
- [x] Resposta em texto e áudio (Ollama + edge_tts)
- [x] voice_bridge classifica intenção de texto transcrito
- [x] Comandos perigosos bloqueados (`acao_perigosa` → `would_execute: false`)
- [x] Tudo logado em `logs/actions.jsonl` com `source: "voice"`

### PIPELINE COMPLETO — dry_run VALIDADO ✅ (2026-06-11)

**Integração:** `single_conversation.py` importa `voice_bridge` diretamente via pathlib  
**Modo:** sempre dry_run=True, nunca executa ações

#### Fluxo atual (validado em teste real)
```
voz → faster-whisper (small, CPU) → input_text (~3–4s)
   → voice_bridge.classify_voice(input_text)   ← ~0ms (wake word + Command Router)
       → _strip_wake_word()                    ← remove saudação + wake word
       → _is_hallucination()                   ← bloqueia lista do prompt (≥5 keywords)
       → command_router.route()
       → logger.log(source="voice")  → actions.jsonl
       ↓
   note == blocked_hallucination?
      SIM → "Não entendi."  → edge_tts        ← sem Ollama
   intent == comando?
      SIM → canned_text     → edge_tts        ← sem Ollama (~0ms LLM)
      NÃO → Ollama          → edge_tts        ← fluxo original
```

#### Latência medida (teste real 2026-06-11)
| Turno | total_dt | LLM |
|---|---|---|
| "Javis, como é que está o sistema?" | 17s | bypass ✅ |
| "Jarvis, abriu, YouTube." | 14s | bypass ✅ |
| "Net, abre, YouTube." | 10s | bypass ✅ |
| "Jarvis, status." | 11s | bypass ✅ |
| "Tá tudo certo, por aí, Javis." | 10s | bypass ✅ |
| conversa normal | 13–20s | Ollama |

Gargalo restante: TTS síntese edge_tts (~4s, rede Azure) — não otimizável sem trocar engine.

#### Segurança
- `dry_run: true` hard-coded em `voice_bridge.py` — nunca alterado (trilha de auditoria JSONL)
- Execução real em `single_conversation.py`, separada do log de classificação
- `acao_perigosa` → `would_execute: false` + canned = "Bloqueado por segurança." — nunca executa
- `abrir_terminal` → `would_execute: false` (APPROVAL_INTENTS) — nunca executa por voz
- Hallucination do ASR → `blocked_hallucination` + canned = "Não entendi." + sem Ollama
- Import falha silenciosa → `logger.warning(...)` visível no servidor + `_voice_bridge = None`

#### ASR
- **Antes:** `large-v3-turbo` — ~18s por transcrição (CPU)
- **Depois:** `small` — ~3–4s por transcrição (CPU) — redução de ~80%
- **initial_prompt:** `'Javis. YouTube. Open WebUI.'` (mínimo — lista longa causava hallucination)

#### Filtro anti-hallucination (2026-06-11)
- `_HALLUCINATION_WORDS` — 10 termos de comando
- `_HALLUCINATION_THRESHOLD = 5` — bloqueia se ≥5 palavras do set aparecem juntas
- `note="blocked_hallucination"` → bypass imediato, sem Ollama, sem comando executado

#### Testes — 2026-06-11
- `test_command_router.py`: **39/39**
- `test_voice_bridge.py`: **59/59** (8 novos: hallucination filter)
- `test_actions.py`: **9/9** (novo: browser handlers, blocked, status, llm, vscode)
- Total: **107/107**

#### Wake words + saudações reconhecidas
`Javis`, `Jarvis`, `Javes`, `Diabes`, `Diaves`, `Chaves`, `Olá`, `Oi`, `Ei`, `Hey`

#### Execução real — LIBERADA ✅ 2026-06-11 (todos os intents seguros)

| Intent | Ação real | Status |
|---|---|---|
| `abrir_youtube` | `webbrowser.open(youtube.com)` | ✅ ativo |
| `tocar_musica` | `webbrowser.open(youtube/lofi)` | ✅ ativo |
| `status_sistema` | socket check 3000/11434/12393 | ✅ ativo |
| `abrir_openwebui` | `webbrowser.open(localhost:3000)` | ✅ ativo |
| `abrir_navegador` | `webbrowser.open(google.com)` | ✅ ativo |
| `abrir_vscode` | `subprocess.Popen(["code", ...])` | ✅ ativo |
| `abrir_javis` | `os.startfile(JAVIS_ROOT)` | ✅ ativo |
| `abrir_projeto` | `os.startfile(JAVIS_ROOT)` | ✅ ativo |
| `registrar_ideia` | escreve .md em `_ideias/` | ✅ ativo |
| `abrir_terminal` | BLOQUEADO — requer aprovação | 🔒 |
| `acao_perigosa` | BLOQUEADO permanentemente | ⛔ |

**Arquitetura de execução:**
- `voice_bridge.classify_voice()` → classifica + loga JSONL (dry_run=True sempre — auditoria)
- `single_conversation.py` → executa via `actions.execute()` para `_LIVE_INTENTS`
- `status_sistema` → TTS dinâmico: "Sistema ok. N serviços ativos." ou "Atenção: N offline."
