---
tags: [memoria, arquitetura, javis]
---

# Arquitetura do Javis

## Diretório
`C:\Users\noteacer\Desktop\javis`

## Repositório
[https://github.com/MurilloAffonso/Javis.git](https://github.com/MurilloAffonso/Javis.git)
Branch principal: `master`

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python — command_router, voice_bridge, actions, logger |
| Frontend | HTML + JS (app.js) + CSS |
| Voz | Open-LLM-VTuber (voz-sandbox, `dry_run=True`) |
| LLM | Ollama + Open WebUI |
| Memória | [[javis-ferramentas]] — AgentMemory + Obsidian |
| CI | pytest (189 testes) |

## Módulos principais

- `_apps/javis-local-interface/backend/command_router.py` — 13 intents, roteamento por keyword
- `_apps/javis-local-interface/backend/voice_bridge.py` — pipeline de voz, **dry_run=True**
- `_apps/javis-local-interface/backend/actions.py` — whitelist de ações seguras
- `_apps/javis-local-interface/backend/logger.py` — JSONL diário
- `_apps/javis-local-interface/config/commands.yaml` — espelho dos intents

## 13 Intents de voz

abrir_youtube, abrir_spotify, abrir_projeto, abrir_terminal, abrir_navegador,
tocar_musica, pausar_musica, status_sistema, criar_nota, ler_nota,
executar_script, pesquisar_web, fechar_aplicativo

## Regra crítica

`dry_run=True` no voice_bridge — [[javis-regras]]

---
Relacionado: [[murillo]] · [[javis-regras]] · [[javis-ferramentas]] · [[javis-testes]] · [[JAVIS-CEREBRO]]
