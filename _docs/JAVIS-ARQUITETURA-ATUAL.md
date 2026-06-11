# Javis — Arquitetura Atual

Data: 2026-06-11  
Status: v0 estável — Local Interface funcionando, voice bridge em dry-run

---

## Visão Geral

```
[Murillo]
    │
    ├── Conversa/Texto → Open WebUI (localhost:3000) → Ollama → resposta
    │
    ├── Voz → Open-LLM-VTuber (localhost:12393) → faster-whisper → Ollama → edge_tts → fala
    │
    ├── Comando local → Javis Local Interface CLI → Command Router → Ação/Log
    │
    └── Arquivo → MarkItDown → conteúdo processado pelo Claude
```

---

## Camadas Atuais

### Camada 1 — Conversa (ATIVA ✅)

**Open WebUI** — http://localhost:3000
- Interface de chat com LLM
- Docker Compose (`docker-compose.yml`)
- Dados em `open-webui-data/`
- 6 modelos especializados configurados

**Ollama** — http://localhost:11434
- Modelos: `llama3.2:3b` (2GB), `phi3:mini` (2.2GB)
- GPU: GTX 1650 (4GB VRAM) — suficiente para rodar 1 modelo por vez
- Não alterar sem aprovação

---

### Camada 2 — Voz (SANDBOX ✅ — não conectado ao Command Router)

**Open-LLM-VTuber v1.2.1** — `_ferramentas/voz-sandbox/`
- Porta: http://localhost:12393
- STT: faster-whisper large-v3-turbo (CPU, int8, pt)
- TTS: edge_tts pt-BR-FranciscaNeural
- LLM: Ollama llama3.2:3b
- Status: pipeline validado, MCP desabilitado, proactive speak desligado
- **Para iniciar:** `cd _ferramentas/voz-sandbox && uv run run_server.py`

**voice_bridge.py** — `_apps/javis-local-interface/backend/`
- Recebe texto transcrito, classifica intenção
- Modo: `dry_run = True` — classifica e loga, não executa
- Ainda separado do Open-LLM-VTuber (integração pendente aprovação)

---

### Camada 3 — Interface Local (ATIVA ✅)

**Javis Local Interface v0** — `_apps/javis-local-interface/`

```
backend/
├── command_router.py  ← classifica texto em intents por palavra-chave (sem LLM)
├── actions.py         ← executa ações da whitelist (abrir URL, pasta, status)
├── logger.py          ← JSONL em logs/actions.jsonl (source: cli/frontend/voice)
├── main.py            ← CLI interativo
└── voice_bridge.py    ← dry-run bridge (texto → classificação → log)

tests/
├── test_command_router.py  ← 27/27 testes passando
└── test_voice_bridge.py    ← 21/21 testes passando

frontend/
├── index.html         ← UI estática (abre direto no browser)
├── style.css
└── app.js             ← Command Router reimplementado em JS

config/commands.yaml   ← documentação dos intents
logs/actions.jsonl     ← histórico de todas as ações
```

**Para iniciar o CLI:**
```powershell
cd _apps/javis-local-interface
python backend/main.py
```

---

### Camada 4 — Memória e Contexto (ATIVO ✅)

**AgentMemory** — MCP configurado em `~/.claude.json`
- Servidor Node.js na porta 3111
- Task Scheduler: inicia no login
- Comando: `npx -y @agentmemory/mcp`

**LeanCTX** — MCP server para economia de tokens
- `ctx_read`, `ctx_search`, `ctx_shell`, `ctx_tree`
- Reduz tokens em até 99% em reads/shells

**CodeGraph** — índice de código em `.codegraph/`
- SQLite local, atualizado automaticamente
- Não commitado (`.gitignore`)

---

### Camada 5 — Processamento de Arquivos (ATIVO ✅)

**MarkItDown**
- Converte PDF, Word, Excel, PowerPoint, HTML, CSV → Markdown
- Instalado via `pip install 'markitdown[all]'`
- Skill: `_skills/analisar-arquivo.md`

---

### Camada 6 — Referência e Padrões (REFERÊNCIA APENAS 📚)

**ECC (Everything Claude Code)** — `_referencias/ECC/`
- Clone shallow do repositório affaan-m/ECC
- Usado como biblioteca de padrões, guardrails e skills
- **Não instalado, não rodado, não ativado**
- Análise: `_ferramentas/ecc/ANALISE-ECC-PARA-JAVIS.md`
- Plano: `_ferramentas/ecc/PLANO-DE-IMPORTACAO-SELETIVA.md`

**isair/jarvis** — referência de arquitetura (não instalar)
- GTX 1650 (4GB VRAM) insuficiente (precisa 8GB)
- Análise: `_ferramentas/repositorios-avaliados-v2.md`

---

## O que está ATIVO

| Componente | URL/Porta | Como iniciar |
|---|---|---|
| Open WebUI | http://localhost:3000 | `docker compose up -d` |
| Ollama | http://localhost:11434 | inicia automaticamente |
| AgentMemory | porta 3111 | Task Scheduler (automático no login) |
| LeanCTX | MCP | configurado em `~/.claude.json` |
| Local Interface CLI | — | `python backend/main.py` |
| CodeGraph | local | automático (file watcher) |

---

## O que está em SANDBOX (não conectado ao sistema principal)

| Componente | Status | Restrição |
|---|---|---|
| Open-LLM-VTuber | funcional, porta 12393 | MCP desabilitado, proactive speak off |
| voice_bridge.py | dry_run=True | não executa, só classifica e loga |

---

## O que está BLOQUEADO

| Componente | Motivo |
|---|---|
| Execução por voz | dry_run ativo — aguardando revisão de logs e aprovação |
| isair/jarvis | GTX 1650, 4GB VRAM insuficientes |
| Headroom | incompatibilidade Python 3.14 / PyO3 |
| Plugin system ECC | sobrecomplexidade — não instalar |
| Hooks automáticos | proibidos sem aprovação |

---

## Segurança — Camadas de Proteção

```
[Comando perigoso]
    │
    ▼
Command Router → risk_level: critical → BLOQUEADO ⛔ (nunca executa)
    │
    ▼ (risk_level: medium)
Approval gate → requer "s" explícito → executa ou cancela
    │
    ▼ (risk_level: low)
actions.py whitelist → ação específica → log JSONL
    │
    ▼ (voice)
voice_bridge → dry_run=True → classifica + loga, nunca executa
```

---

## Próximos Passos

1. **Conectar transcrição real ao voice_bridge** — usar Open-LLM-VTuber, observar logs, revisar
2. **Aprovar liberação de execução por voz** — após revisão dos logs dry-run
3. **v1 Local Interface** — FastAPI para servir frontend (aprovação pendente)
4. **Commit inicial** — quando Murillo aprovar
