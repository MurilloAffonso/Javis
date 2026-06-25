# JAVIS — Sistema completo (Command Center + Chat + Backend)

Visão geral do que foi construído. Inspirado na lógica do AIOS Core Platform,
sem copiar identidade. Tudo em Python + frontend estático; **não usa Dify**.

## Arquitetura (2 camadas + 1 cérebro)

```
┌ Chat (Chainlit, :8001) ────────────┐   ┌ Command Center (estático, servido em :8000/command-center) ┐
│ conversa, voz, upload, modos,      │   │ Chat por agente, World isométrico, Tarefas/Workflows,       │
│ projeto ativo, telemetria, gate    │   │ Painel (dashboards), Config (Memórias/Scripts), Atividade    │
└──────────────┬─────────────────────┘   └──────────────┬───────────────────────────────────────────────┘
               │  ambos falam com o mesmo cérebro        │  fetch read-only /ui/* + /chat + /approvals + /tts
               └───────────────► server.py (FastAPI, :8000) ──► _brain()  ◄── orquestra TODOS os projetos
```

- **`_brain()`** (server.py): núcleo único de decisão. Cascata: atalho local →
  conclave → agente (tool-use) → cérebro principal. Intocado nesta evolução.
- **Camada read-only de UI:** `ui_state.py` (projetos/squads/agentes/skills/scripts +
  KPIs reais da VP + status real de projeto externo) e `telemetry_adapter.py`
  (status, tokens estimados, eventos, brain — lê o log JSONL + SQLite).

## Rodar (tudo no venv 3.11 — Python 3.14 global quebra anyio)

```powershell
cd _apps/javis-local-interface
# Backend + Command Center (:8000)
cd backend; ..\.venv_chainlit\Scripts\python.exe -c "import uvicorn; uvicorn.run('server:app',host='127.0.0.1',port=8000,reload=False)"
# Chat (:8001) — outro terminal
.\.venv_chainlit\Scripts\python.exe -m chainlit run app_ui.py -w --port 8001
```
- Command Center: http://localhost:8000/command-center/
- Chat: http://localhost:8001

## Telas do Command Center
- **Chat** — por agente, com Habilidades em % e **comando de voz** (🎙️ grava →
  /transcribe → _brain → /tts fala a resposta com Piper local).
- **World** — mapa isométrico de setores/agentes; torre pulsa quando há agente
  executando; clicar abre o chat do agente.
- **Tarefas** — orquestrador (demanda → /chat), lista de workflows, grafo de fluxo.
- **Painel** — dashboards por projeto; Vem Passear com **KPIs reais** de `_data/vp_*.json`.
- **Config** — Memórias (knowledge por agente), **Scripts** (44 do backend), etc.
- **Atividade** (direita) — Status LLM, Uso de Tokens, Agente Selecionado, Métricas
  (intent/brain/tools/risk), **Aprovações reais** (decide no backend).
- **Busca global** (topo) — filtra agentes/squads/skills/scripts no canvas.

## Endpoints read-only de UI (aditivos no server.py)
`/ui/state` · `/ui/projects` · `/ui/squads/{proj}` · `/ui/agents` · `/ui/skills`
· `/ui/scripts` · `/ui/project/{id}` · `/ui/telemetry`
Aprovações: `/approvals/pending` · `/approvals/{id}/decide`
Voz: `/transcribe` · `/tts` · `/chat`

## Segurança (preservada)
Whitelist + `risk_level` do `command_router` intactos. Ação **crítica** é bloqueada;
**risco médio** vira **aprovação humana** (Gate no Command Center). Sem git
automático, sem shell arbitrário, sem deleção.

## Dados (registries)
`data/ui/*.json` (projetos, squads, agentes, skills, scripts) + `data/projects/vempassear.json`
(manifesto/dashboards). Gerados/curados; o backend serve a versão viva via `ui_state`.

> Decisões e histórico do build: `_logs/2026-06-24_command-center-fases.md` e
> `_logs/2026-06-25_overnight-progress.md`.
