# Análise: Hermes Agent (Nous Research) × Javis

> **SUPERADO** — este documento é a análise teórica de ANTES do teste lado a
> lado. O resultado real, com prova (logs, trace, achados técnicos), está em
> `_logs/2026-06-23_hermes-veredito.md` — **é esse o documento que vale**.
> Este arquivo fica só como histórico de como a decisão foi montada.

**Data:** 2026-06-23
**Objetivo:** registrar a análise (que só existia em conversa) pra decidir, com
base, entre **minerar / adotar / descartar** o Hermes. Decisão de Murillo: testar
lado a lado primeiro. Detalhe do teste: `_logs/2026-06-23_hermes-veredito.md`
(a escrever após o tour).

---

## O que é o Hermes Agent

Agente autônomo open-source da Nous Research (lançado fev/2026). Chegou a **#1 no
OpenRouter** em todas as categorias. Resumo técnico:

- **Python 82%** + frontend TS. **Licença MIT.**
- Instala no **Windows nativo** (PowerShell one-liner, sem admin, isolado em
  `~/.hermes`; provisiona Python 3.11, Node, ffmpeg, git portátil).
- **App standalone (CLI/TUI), NÃO biblioteca** — roda separado; não se embute no
  Javis como módulo.
- Provedores: OpenRouter, Gemini, OpenAI, Anthropic, Ollama, etc. via
  `hermes model`. Config em `~/.hermes/config.yaml`, keys em `~/.hermes/.env`.
  Caminho grátis sem o Portal pago.

## Componentes (a "estrutura")

- **Agent loop** com tool-calling + compressão de contexto.
- **Skills system** — memória procedural; cria skill sozinho após tarefa complexa;
  compatível com agentskills.io.
- **Memória** — persistente, FTS5 full-text, sumarização por LLM, modelagem de
  usuário (Honcho) que aprofunda o perfil entre sessões.
- **Messaging gateway** — Telegram, Discord, Slack, WhatsApp, Signal (20+).
- **6 backends de terminal isolados** (local, Docker, SSH, Singularity, Modal, Daytona).
- **Cron** em linguagem natural; **40+ ferramentas** (web, código, arquivos...).

## Hermes × Javis (o que cada um tem)

| Capacidade | Hermes | Javis hoje |
|---|---|---|
| Memória persistente + skills que aprende | ✅ pronto | parcial (RAG + memória, sem auto-skill) |
| Gateway multi-plataforma | ✅ 20+ | só Telegram (`telegram_bridge.py`) |
| Multi-modelo / cascata | ✅ gerenciado | ✅ próprio (Claude→OpenAI→API→OpenRouter) |
| Subagentes isolados (sandbox real) | ✅ 6 backends | Conclave/squad, sem sandbox |
| Cron / automações | ✅ | reminders + rotina matinal |
| **Persona Jamba (PT-BR, mordomo)** | ❌ | ✅ **só do Javis** |
| **Pipeline campanha VP (3 gates)** | ❌ | ✅ **só do Javis** |
| **Integração Cérebro Jampa** | ❌ | ✅ **só do Javis** |

## A leitura

O Hermes resolve, pronto e mantido, a **encanação genérica de agente** que o Javis
reconstrói à mão. Mas **não tem a alma do Javis** (persona, pipeline VP, negócio).
Conclusão de arquitetura: Hermes = **chassi**; Javis = **carroceria + alma**.

## Os 3 níveis de compromisso

1. **Minerar** (risco 0, MIT) — copiar padrões (skill-learning, gateway) pro código
   do Javis aos poucos.
2. **Rodar lado a lado** (~1 tarde) — instalar, apontar pros free, sentir na prática.
   ← **escolhido agora.**
3. **Adotar como substrato** — Javis vira skin (persona + pipeline) sobre o Hermes.
   Grande; só decidir DEPOIS de (2).

## Por que testar antes de decidir

Não dá pra adotar algo que você não rodou. O tour (multi-modelo, memória/skills,
gateway, maturidade) dá a decisão informada. Custo do tour: **US$0** (provedores
free). Javis fica intacto durante tudo.
