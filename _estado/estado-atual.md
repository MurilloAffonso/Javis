# Estado Atual — Javis

**Atualizado:** 2026-06-11 (sessão intent-consistency-audit)
**Responsável pela última atualização:** Claude Code — Auditoria de Consistência de Intents

---

## Stack ativa

| Ferramenta | Status | Evidência |
|-----------|--------|-----------|
| LeanCTX v3.7.5 | ✅ ATIVO | 1.0M tokens salvos, 79.7% compressão, $2.73 USD |
| CodeGraph | ✅ ATIVO | 13 arquivos, 177 nós, 315 arestas indexados |
| AgentMemory | ✅ instalado | MCP configurado, em uso |
| Open WebUI | ✅ rodando | localhost:3000 (Docker) |
| Ollama + llama3.2:3b | ✅ rodando | porta 11434 |
| voz-sandbox (Open-LLM-VTuber) | ⏸ separado | porta 12393, não integrado ao Javis |
| Headroom | ❌ não instalado | falhou por incompatibilidade Python 3.14 + PyO3 |

---

## Módulos do Javis Local Interface

| Módulo | Status |
|--------|--------|
| backend/command_router.py | ✅ 13 intents, testado |
| backend/voice_bridge.py | ✅ dry_run=True, 5 test files passando |
| backend/actions.py | ✅ whitelist de 9 ações seguras |
| backend/logger.py | ✅ rotação diária JSONL |
| frontend/app.js | ✅ 12/13 intents (falta abrir_projeto) |
| tests/ | ✅ 189 checks, 0 falhas |

---

## Sessões recentes

- 2026-06-10: Setup inicial, LeanCTX, Open WebUI, 6 modelos configurados
- 2026-06-11: 5 fases de auditoria (gitignore, actions, logs, intents, token economy)
- 2026-06-11: Sessão abrir-sessao/fechar-sessao — 1ª sessão com protocolo completo. Auditoria de intents: 13/13 consistentes, 189/189 testes OK.

---

## O que está pendente (ver proximos-passos.md)

- `abrir_projeto` ausente no frontend/app.js (RULES, RISK, MESSAGES)
- Headroom aguardando aprovação de Murillo
- Fase 2 de voz (execução real) aguardando aprovação de Murillo
