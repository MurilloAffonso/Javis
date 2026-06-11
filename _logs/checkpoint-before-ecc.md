# Checkpoint — antes de incorporar padrões do ECC

Data: 2026-06-11  
Hora: início da sessão

---

## git status --short

Repositório sem commits. Todos os arquivos estão como untracked (??).
Nenhuma alteração staged ou unstaged — estado limpo para mudanças planejadas.

---

## Estado atual do projeto

### Infraestrutura rodando
- **Open WebUI** — http://localhost:3000 (Docker, porta 3000)
- **Ollama** — llama3.2:3b + phi3:mini, GPU GTX 1650 (4 GB VRAM)
- **AgentMemory** — MCP configurado em ~/.claude.json, Task Scheduler ativo
- **LeanCTX** — MCP server ativo, economiza tokens nos reads/shells
- **CodeGraph** — inicializado em .codegraph/, índice local

### Sandbox de voz
- **Open-LLM-VTuber v1.2.1** — `_ferramentas/voz-sandbox/`, porta 12393
- STT: faster-whisper large-v3-turbo (CPU, pt, int8)
- TTS: edge_tts pt-BR-FranciscaNeural
- LLM: Ollama llama3.2:3b
- Status: pipeline validado (4 bugs corrigidos), MCP desabilitado, proactive speak desligado
- **NÃO alterar agora**

### Javis Local Interface v0
- CLI funcional: `python _apps/javis-local-interface/backend/main.py`
- Command Router: 10/10 testes passando (incluindo bloqueio de acao_perigosa)
- Voice Bridge: dry-run ativo, classifica e loga sem executar
- Logger: JSONL em `_apps/javis-local-interface/logs/actions.jsonl`
- Frontend estático: `_apps/javis-local-interface/frontend/index.html`

---

## Arquivos principais existentes

```
javis/
├── AGENTS.md                              ← regras para agentes
├── CLAUDE.md                              ← regras para Claude Code
├── README.md                              ← visão geral do projeto
├── docker-compose.yml                     ← Open WebUI (não alterar)
├── _apps/
│   └── javis-local-interface/
│       ├── README.md
│       ├── backend/
│       │   ├── command_router.py          ← classificador de intenção (10/10 testes)
│       │   ├── actions.py                 ← executor de ações (whitelist)
│       │   ├── logger.py                  ← JSONL logger (source: cli/frontend/voice)
│       │   ├── main.py                    ← CLI v0
│       │   └── voice_bridge.py            ← dry-run bridge (5/5 testes)
│       ├── config/commands.yaml
│       ├── frontend/{index.html,style.css,app.js}
│       └── logs/actions.jsonl
├── _docs/
│   ├── JAVIS-LOCAL-INTERFACE-ROADMAP.md
│   └── JAVIS-VOICE-TO-COMMAND-ROUTER.md
├── _ferramentas/
│   ├── agentmemory/STATUS.md
│   ├── headroom/STATUS.md
│   ├── leanctx/STATUS.md
│   ├── repositorios-avaliados.md
│   ├── repositorios-avaliados-v2.md       ← análise isair/jarvis (não instalar)
│   └── voz/STATUS.md                      ← status do sandbox + próximo passo de voz
├── _logs/
│   ├── 2026-06-10_open-webui-setup.md
│   ├── 2026-06-10_setup-inicial.md
│   ├── openwebui-config-after.md
│   └── openwebui-config-before.md
├── _memoria/murillo.md
├── _projetos/javis-v0.md
├── _prompts/
│   ├── system-openwebui-javis.md
│   └── modelos-openwebui/{6 modelos especializados}
└── _skills/
    ├── abrir-projeto.md
    ├── analisar-arquivo.md
    ├── capturar-ideia.md
    ├── comando-de-voz-local.md
    ├── criar-plano-semanal.md
    ├── executar-com-aprovacao.md
    ├── planejar-proximo-passo.md
    ├── registrar-log.md
    ├── resumir-decisao.md
    ├── revisar-plano.md
    ├── transformar-em-projeto.md
    └── voz-para-comando.md
```

Total: 12 skills, 5 arquivos de backend, 2 docs técnicos, 4 logs.

---

## Pendências atuais

1. **Pendência principal (em andamento):**  
   Conectar transcrição real do Open-LLM-VTuber ao voice_bridge.py em dry-run,
   revisar logs reais antes de liberar execução para risk_level: low.

2. Headroom: aguardando compatibilidade Python 3.14 / PyO3.
3. isair/jarvis: não instalar (GTX 1650, 4GB VRAM insuficientes).
4. v1 da Local Interface: servir frontend via FastAPI (aprovação pendente).
5. Primeiro projeto ativo em `_projetos/`.

---

## Próximo passo que estava em andamento antes do ECC

**Conectar transcrição real do Open-LLM-VTuber ao voice_bridge.py em dry-run
e revisar logs antes de liberar execução low risk.**

Detalhes em: `_ferramentas/voz/STATUS.md` e `_docs/JAVIS-VOICE-TO-COMMAND-ROUTER.md`

Sequência:
1. Usar sandbox de voz normalmente (falar comandos reais)
2. Testar `voice_bridge.py` com as frases que Murillo costuma dizer
3. Revisar `logs/actions.jsonl` — confirmar intents corretos
4. Aprovar explicitamente: "liberar execução para risk_level: low"
5. Modificar `voice_bridge.py` para executar ações seguras
6. Integrar ao `single_conversation.py` do Open-LLM-VTuber

---

## Objetivo desta sessão (ECC)

Usar o repositório ECC (https://github.com/affaan-m/ECC) como biblioteca de padrões,
skills, rules e boas práticas — sem instalar o ECC, sem rodar seus scripts.

**Não perde o ponto:** ao terminar o trabalho com ECC, voltar à pendência de voz acima.
