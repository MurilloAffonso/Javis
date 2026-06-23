# Estado Atual — Javis

**Atualizado:** 2026-06-23 (rota Gemini free + TTS local Piper na cascata)
**Testes:** 138 passing em `_apps/javis-local-interface/` (`python -m pytest tests/ -q`)

> Histórico detalhado de sessões: ver `_logs/` datados e o `git log`. Este arquivo
> é só o **snapshot atual** — mantido curto de propósito.

---

## O que o Javis É

Assistente pessoal/operacional do Murillo (persona "Jamba", mordomo PT-BR), com
chat + voz, orquestração de tarefas e um pipeline de campanha com aprovação humana.
Roda local (FastAPI em `localhost:8000`), Windows.

## O que está PRONTO e TESTADO (a base que funciona)

| Bloco | Estado |
|-------|--------|
| **Cascata multi-cérebro** (`agent.py`) | ✅ Claude assinatura → OpenAI → Claude API → Gemini → OpenRouter, com telemetria de token e custo sanitizada |
| **command_router** | ✅ 13 intents, fast-path por palavra-chave (sem LLM = instantâneo) |
| **Tool-use** (`agent.py`) | ✅ ~20 ferramentas; gating + prompt caching + compactação de histórico |
| **Pipeline de campanha** | ✅ 3 gates de aprovação humana (Pauta→Estúdio→Distribuição), SQLite + Journey Log + digest |
| **Motor de execução** (`brain_switch.py`) | ✅ troca Claude/Codex, persistido em `brain_ativo.json` |
| **Voz** (`voice_bridge.py`) | ✅ executando (dry_run=False), faster-whisper ASR local + wake word "Jamba" |
| **TTS** (`/tts`, `tts_local.py`) | ✅ Piper local (pt_BR-faber-medium, grátis, sem rede) padrão; fallback OpenAI pago só se Piper faltar/falhar. Ack/streaming de voz em tempo real continua no OpenAI (latência já calibrada) |
| **RAG** (`knowledge.py`) | ✅ indexa .md das pastas de conhecimento, tool `buscar_conhecimento` |
| **Frontend** | ✅ Quadro Kanban (estilo Plane) + CONVERSA + painel HUD |
| **Integrações** | ✅ Telegram ativo; YouTube/weather degradam sem key |

## Frentes (ver `proximos-passos.md`)

Decisão 22/06: **UMA frente ativa por vez.** Fechadas: **rota Gemini free na
cascata** (23/06) e **TTS local Piper** (23/06). Frente ativa: livre, aguardando
escolha. Parqueado (não disputa foco): OpenRouter deep, Hermes, treinamento/redes,
criativo.
