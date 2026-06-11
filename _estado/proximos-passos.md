# Próximos Passos — Javis

**Atualizado:** 2026-06-11
**Responsável:** Claude Code — Auditor de Economia de Tokens

---

## ✅ Prioridade 1 — Protocolo de sessão (CONCLUÍDO 2026-06-11)

- [x] Criar `_sessoes/` e usar `_skills/abrir-sessao.md` no início de cada sessão
- [x] Usar `_skills/fechar-sessao.md` ao final de cada sessão
- [x] Registrar economia de tokens em `_logs/token-economy.md` ao fechar

**Resultado:** 1ª sessão completa com protocolo abrir/fechar em 2026-06-11.

---

## Prioridade 1 — Frontend (pequeno)

- [ ] Adicionar `abrir_projeto` em `frontend/app.js` (RULES, RISK, MESSAGES)
- [ ] 3 linhas de mudança — baixo risco

---

## Prioridade 3 — Voz (APROVAÇÃO NECESSÁRIA)

- [ ] Fase 2: liberar execução real de 9 intents seguros por voz
- [ ] dry_run=True → dry_run=False após Murillo validar os logs
- [ ] Status atual: já implementado em single_conversation.py, só aguarda aprovação

---

## Prioridade 4 — Headroom (APROVAÇÃO NECESSÁRIA)

- [ ] Workaround: `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install headroom-ai`
- [ ] Aguardando aprovação de Murillo desde 2026-06-10

---

## Backlog

- [ ] git init dentro de javis/ para isolamento do repositório do usuário
- [ ] `_memoria/murillo.md` com contexto completo (existe mas pode ser expandido)
- [ ] Definir primeiro projeto ativo em `_projetos/`
- [ ] Integrar voz-sandbox ao Javis (hoje está separado em `_ferramentas/`)
