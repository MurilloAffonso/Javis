# Repositórios Avaliados — Atualização v2
Data: 2026-06-10

> Complementa `repositorios-avaliados.md` (v1). Foco desta atualização: análise profunda do isair/jarvis.

---

## isair/jarvis

**Repositório:** https://github.com/isair/jarvis  
**Stars:** ~1.2k | **Forks:** 212 | **Última release:** v1.34.1 (2026-05-07)  
**Commits:** 391 — desenvolvimento ativo  
**Licença:** Uso pessoal gratuito; comercial requer contato  
**Linguagem:** Python 98.6%  
**Status:** 🟡 Referência de arquitetura — não instalar ainda

---

### O que faz

Assistente de voz 100% local e offline para desktop. Pipeline:

```
Microfone → Whisper (STT) → Intent Judge (LLM pequeno) →
Tool Router (embedding/LLM) → Planner → Chat Model (Ollama) →
MCP Tools → Piper TTS / Chatterbox
```

Não tem interface web. É voice-only (issue #35 aberto para texto). Roda como app desktop (`.exe` no Windows).

---

### Recursos e alinhamento com a visão do Javis

#### Voz
- ✅ Wake word "Jarvis" funciona em qualquer posição na frase (não precisa ser o início)
- ✅ Whisper multilíngue — suporta português
- ✅ Piper TTS (padrão) ou Chatterbox
- ✅ Echo detection — filtra o próprio áudio gerado
- ✅ Interrupção por comando "stop"
- ✅ Thresholds configuráveis: `whisper_min_confidence: 0.3`, `whisper_no_speech_threshold: 0.5`
- ⚠️ Issue #348: `PaErrorCode -9999` no Windows v1.33.0 (microfone falha em abrir)

#### Memória
- ✅ Histórico ilimitado com busca semântica
- ✅ Knowledge graph que se auto-organiza por tópico
- ✅ Memory Viewer GUI (navegação do diário)
- ✅ Redação automática de informações sensíveis antes de persistir (emails, tokens, senhas)
- ✅ Memory digest para modelos pequenos (comprime contexto automaticamente)
- ⚠️ "Deflection narration" — modelos pequenos às vezes registram próprios falhos no diário

#### MCP / Tools
- ✅ Built-in: web search (DDG → Brave → Wikipedia), OCR screenshot, clima, arquivos, nutrição, geolocalização local
- ✅ MCPs ilimitadas (Home Assistant, GitHub, Slack, bancos, etc.)
- ✅ Tool routing inteligente por embedding — evita degradação de contexto com muitas tools
- ✅ Estratégias: `llm` (padrão), `keyword`, `embedding`, `all`
- ✅ Tool discovery: agente pode expandir toolset dinamicamente mid-reply

#### Ditado offline
- ✅ Hotkey global: `Ctrl+Win` (Windows), `Ctrl+Option` (macOS), `Ctrl+Alt` (Linux)
- ✅ Compartilha modelo Whisper já em VRAM — zero overhead extra
- ✅ Cole universal via Ctrl+V em qualquer app
- ✅ Modo hands-free (duplo-tap para gravar continuamente)
- ✅ Remove filler words (ativável): "um", "uh", "tipo"
- ✅ Dicionário customizável para jargão/nomes próprios
- ✅ Histórico navegável
- **Esta feature é equivalente ao WisprFlow comercial — gratuita e offline**

#### Controle do computador / Chrome
- ✅ OCR de screenshot integrado (leitura de tela)
- ✅ Controle do Chrome via MCP
- ✅ Automação de browser (ex: "Abrir YouTube")
- ✅ Execução de tarefas com base em resultado de tool
- ❌ Sem API REST ou interface web programática

---

### Compatibilidade Windows

| Aspecto | Status |
|---------|--------|
| Instalação | ✅ `.exe` pronto, ZIP + extrai + executa |
| CUDA opcional | ✅ instalador separado para aceleração |
| Desenvolvimento primário | ⚠️ macOS arm64 — Windows pode atrasar |
| Issue PaErrorCode -9999 | ⚠️ Microfone falha em alguns Windows (#348) |
| AMD GPU (DirectML) | ⚠️ Solicitado mas não implementado (#340) |
| Crash reports recentes | ⚠️ #458, #422, #415, #401, #354 — crashes em Windows |

**Conclusão Windows:** Funciona, mas com ressalvas. O desenvolvedor principal usa macOS.

---

### Requisitos de VRAM

| Modelo padrão | VRAM mínima |
|---------------|-------------|
| `gemma4:e2b` (padrão) | **8GB VRAM** |
| `gemma4:e4b` (qualidade) | 16GB VRAM |
| `gpt-oss:20b` (high-end) | 24GB VRAM |
| Whisper Tiny/Base | +1GB |
| Whisper Large V3 Turbo | +6GB |

**Problema crítico:** Nossa máquina roda `llama3.2:3b` (2GB) e `phi3:mini` (2.2GB) via Ollama — provavelmente **não tem 8GB VRAM livre** para `gemma4:e2b`. Modelos menores podem ser testados, mas degradam a qualidade.

---

### Riscos técnicos

1. **VRAM insuficiente** — o modelo padrão exige 8GB, nossa máquina provavelmente não tem
2. **Windows secundário** — macOS é plataforma principal; bugs Windows podem demorar a ser corrigidos
3. **Crash reports ativos** — múltiplos crashes reportados em Mai-Jun 2026
4. **Voice-only** — sem interface de texto hoje (issue #35 aberto)
5. **Whisper em CPU** — sem CUDA, transcrição será lenta (5-15s por frase, igual nosso sandbox atual)
6. **PaErrorCode -9999** — bug específico Windows no microfone, pode afetar setup

---

### Riscos de privacidade

**Positivos:**
- Zero conectividade com nuvem (verificável via `netstat`)
- Redação automática de dados sensíveis antes de salvar
- GeoIP usa banco local MaxMind (sem API externa)
- Dados em `~/.local/share/jarvis` (controlável)

**Neutros / monitorar:**
- Fallback de IP detection usa query DNS para OpenDNS — sai à internet uma vez
- Web search usa DuckDuckGo → Brave (conexão externa quando tools estão ativas)

**Conclusão privacidade:** ✅ Adequado para uso pessoal. Mais rigoroso que a maioria.

---

### Licença

- **Uso pessoal:** Gratuito indefinidamente
- **Uso comercial:** Requer contato com o autor
- ✅ Projeto Javis é uso pessoal — sem restrições

---

### Conflitos com stack atual

| Conflito potencial | Análise |
|---|---|
| Open WebUI | ✅ Sem conflito — isair/jarvis não tem interface web |
| AgentMemory | ✅ Sem conflito — arquiteturas paralelas, podem coexistir |
| Open-LLM-VTuber | ✅ Sem conflito — propósitos distintos (voz desktop vs VTuber web) |
| Ollama | ✅ Sem conflito — usa o mesmo Ollama local |
| LeanCTX / CodeGraph | ✅ Sem conflito — ferramentas de Claude Code, não do assistente |

---

### O que vale copiar como padrão

1. **Wake word em qualquer posição** — não exige frase começando com "Javis"
2. **Tool routing por embedding** — filtra tools por relevância, evita context rot
3. **Memory digest** — comprime contexto longo para modelos pequenos
4. **Redação automática de sensíveis** — padrão de segurança pré-persistência
5. **Ditado com remoção de filler words** — `Ctrl+Win` cola em qualquer app
6. **Echo detection** — ignora próprio áudio gerado pelo TTS
7. **Estratégia de thresholds Whisper** — `min_confidence` + `no_speech_threshold` juntos

---

### O que NÃO instalar agora

- O app completo `Jarvis.exe` — exige 8GB VRAM que provavelmente não temos
- Modelos `gemma4:*` — fora da capacidade atual da máquina
- Piper TTS — edge_tts já funciona e não precisa de modelos locais
- Nada até validar VRAM disponível

---

## Decisão Final

**Classificação: D) Referência de arquitetura** (primário) + **C) Sandbox futuro** (condicionado a VRAM)

Não substituir nada do stack atual. isair/jarvis é a referência mais completa encontrada para a visão de voz offline do Javis, mas:
- Requer VRAM que precisamos confirmar
- Windows não é plataforma primária do desenvolvedor
- Crashes ativos em 2026

**Ver plano de sandbox abaixo.**

---

## Tabela comparativa

| Critério | isair/jarvis | Open-LLM-VTuber (sandbox) | Javis atual |
|---|---|---|---|
| **Interface** | Desktop app (voice-only) | Web (localhost) com avatar | Open WebUI (web) |
| **Wake word** | ✅ Em qualquer posição | ❌ Não tem | ❌ Não tem |
| **STT** | Whisper (offline) | faster-whisper (offline) | N/A |
| **TTS** | Piper / Chatterbox (offline) | edge_tts (online!) | N/A |
| **Memória** | ✅ Knowledge graph ilimitado | ❌ Sem memória persistente | ✅ AgentMemory |
| **Ditado offline** | ✅ Hotkey global, qualquer app | ❌ Não tem | ❌ Não tem |
| **MCP / tools** | ✅ Router inteligente, ilimitado | ❌ Loop com llama3.2:3b | ✅ Claude Code |
| **Controle Chrome** | ✅ Via MCP | ❌ | ❌ |
| **OCR tela** | ✅ Built-in | ❌ | ❌ |
| **Avatar Live2D** | ❌ | ✅ | ❌ |
| **Privacidade** | ✅ 100% local | ✅ Local (TTS faz req externa) | ✅ Local |
| **VRAM mínima** | ⚠️ 8GB | ~0 extra (usa Ollama) | ~0 |
| **Windows** | ⚠️ Secundário | ✅ Funciona | ✅ Funciona |
| **Licença** | Personal free | MIT | N/A |
| **Estabilidade** | ⚠️ Crashes ativos | ⚠️ Bugs conhecidos | ✅ Estável |

---

## Plano seguro de sandbox

**Pré-condição obrigatória:** confirmar VRAM disponível
```
! nvidia-smi --query-gpu=memory.free,memory.total --format=csv
```
Se < 8GB livre → isair/jarvis não roda com modelo padrão.

**Se VRAM ok:**
1. Baixar `Jarvis-Windows-x64.zip` da release v1.34.1
2. Extrair em `C:\Users\noteacer\Desktop\javis\_ferramentas\isair-jarvis-sandbox\`
3. NÃO executar ainda — revisar `config.json` antes
4. Configurar para usar Ollama em `localhost:11434`
5. Usar modelo menor se VRAM limitada (testar com `llama3.2:3b` primeiro)
6. Testar SOMENTE ditado offline (`Ctrl+Win`) antes de ativar voice assistant completo
7. Registrar resultado em `_ferramentas/voz/STATUS.md`

**Se VRAM insuficiente:**
- Usar como referência de código (clonar, ler, não rodar)
- Copiar padrões de: wake word, tool routing, memory digest para o nosso stack

---

## Arquivos do projeto a atualizar

- ✅ `_ferramentas/repositorios-avaliados-v2.md` — este arquivo
- ✅ `_ferramentas/voz/STATUS.md` — seção isair/jarvis adicionada
- [ ] `_memoria/murillo.md` — registrar que Murillo tem interesse em ditado offline e wake word
- [ ] `_projetos/javis-v0.md` — atualizar roadmap com ditado offline e wake word como próxima fase de voz

---

## Pré-check de hardware para isair/jarvis

Data: 2026-06-10

| Parâmetro | Valor |
|-----------|-------|
| GPU | NVIDIA GeForce GTX 1650 |
| VRAM total | 4096 MiB (4 GB) |
| VRAM livre | 1461 MiB (~1.4 GB) |
| CUDA (driver) | 13.2 — disponível |
| Processo usando GPU | `llama-server.exe` (Ollama) — ativo |

**Requisito mínimo do isair/jarvis:** 8 GB VRAM (`gemma4:e2b`)  
**VRAM disponível:** ~1.4 GB livre (4 GB total)

### Decisão: não instalar agora

A máquina tem menos da metade da VRAM mínima exigida. Mesmo com modelo menor (`llama3.2:3b`), Whisper large-v3-turbo precisaria de ~3 GB adicionais — excede a capacidade total da GTX 1650 com Ollama ativo.

**Status:** Referência de arquitetura — não instalar, não clonar.
