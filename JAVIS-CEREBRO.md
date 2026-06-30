# 🧠 Javes — Mapa Central

> Assistente pessoal e operacional de Murillo.
> Este arquivo é o ponto de entrada do cofre no Obsidian.

---

## 🏗️ Arquitetura

- [[README]] — visão geral do projeto
- [[AGENTS]] — regras para agentes AI
- [[CLAUDE]] — regras para Claude Code

---

## 📦 Interface Local

- [[_apps/javis-local-interface/README]]
- [[_apps/javis-local-interface/backend/command_router]] — 13 intents, roteamento por keyword
- [[_apps/javis-local-interface/backend/voice_bridge]] — pipeline de voz, dry_run=True
- [[_apps/javis-local-interface/backend/actions]] — whitelist de ações seguras
- [[_apps/javis-local-interface/backend/logger]] — JSONL diário
- [[_apps/javis-local-interface/config/commands]] — documentação dos intents

---

## 📖 Documentação

- [[_docs/JAVIS-VOICE-TO-COMMAND-ROUTER]] — pipeline voz → comando
- [[_docs/JAVIS-LOCAL-INTERFACE-ROADMAP]] — roadmap
- [[_docs/JAVIS-ARQUITETURA-ATUAL]] — arquitetura atual
- [[_docs/JAVIS-ASR-LATENCY-RECOMENDACAO]] — ASR e latência

---

## 🎯 Estado Atual

- [[_estado/estado-atual]] — o que está rodando agora
- [[_estado/proximos-passos]] — o que fazer a seguir

---

## 🛠️ Skills

- [[_skills/abrir-sessao]] — iniciar sessão de trabalho
- [[_skills/fechar-sessao]] — encerrar sessão com registro
- [[_skills/capturar-ideia]] — capturar ideia solta
- [[_skills/planejar-proximo-passo]] — destravar
- [[_skills/checkpoint-antes-de-mudar]] — segurança antes de grandes mudanças
- [[_skills/revisar-logs-de-voz]] — auditar logs de voz

---

## 📋 Sessões

- [[_sessoes/2026-06-11_04h30_intent-consistency-audit]]

---

## 📊 Logs & Economia

- [[_logs/token-economy]] — economia de tokens LeanCTX
- [[_logs/2026-06-11_token-economy-audit]] — auditoria de economia

---

## 🧰 Ferramentas

- [[_ferramentas/leanctx/STATUS]] — LeanCTX (compressão de tokens)
- [[_ferramentas/voz/STATUS]] — sandbox de voz
- [[_ferramentas/agentmemory/STATUS]] — AgentMemory MCP (porta 3111/3113)

---

## 🧠 Memória

- [[_memoria/murillo]] — quem é Murillo, como prefere ser atendido
- [[_memoria/javis-arquitetura]] — stack, módulos, 13 intents
- [[_memoria/javis-regras]] — regras críticas para Claude e agentes
- [[_memoria/javis-ferramentas]] — LeanCTX, AgentMemory, CodeGraph, Obsidian
- [[_memoria/javis-protocolo]] — protocolo de sessão (abrir/fechar)
- [[_memoria/javis-testes]] — 189/189 testes, como rodar
- [[_memoria/javis-decisoes]] — histórico de decisões técnicas

---

## 🐙 GitHub

- Repositório: [MurilloAffonso/Javis](https://github.com/MurilloAffonso/Javis)
- Branch: `master` · Commit inicial: `cc42b2a` (92 arquivos)

---

## 💡 Ideias & Projetos

- [[_projetos/javis-v0]] — projeto atual
- Pasta `_ideias/` — ideias capturadas

---

#javis #cerebro #moc
