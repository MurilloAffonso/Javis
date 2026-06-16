# Próximos Passos — Javis

**Atualizado:** 2026-06-13
**Responsável:** Claude Code

---

## ✅ Prioridade 1 — Protocolo de sessão (CONCLUÍDO 2026-06-11)

- [x] Criar `_sessoes/` e usar `_skills/abrir-sessao.md` no início de cada sessão
- [x] Usar `_skills/fechar-sessao.md` ao final de cada sessão
- [x] Registrar economia de tokens em `_logs/token-economy.md` ao fechar

**Resultado:** 1ª sessão completa com protocolo abrir/fechar em 2026-06-11.

---

## ✅ Prioridade 1 — Frontend (CONCLUÍDO 2026-06-12)

- [x] Botão rápido `📂 projeto` adicionado em `frontend/index.html` → dispara `abrir_projeto`
- [x] frontend agora cobre 13/13 intents do backend

---

## ✅ Prioridade 3 — Voz Fase 2 (CONCLUÍDO 2026-06-13)

- [x] dry_run=False ativado em voice_bridge.py
- [x] 9 intents seguros executam via _brain() em tempo real
- [x] Logs agora registram `status: executed` ao invés de `dry_run_only`

---

## ✅ Prioridade 4 — Headroom (CONCLUÍDO 2026-06-13)

- [x] headroom-ai 0.24.0 instalado (compilado com Rust via winget)
- [x] `headroom.exe` disponível em `AppData\Roaming\Python\Python314\Scripts`
- [x] Scripts adicionados ao PATH do usuário

---

## Backlog

- [ ] git init dentro de javis/ para isolamento do repositório do usuário
- [x] `_memoria/murillo.md` expandido — negócio, setup, estilo de decisão (2026-06-13)
- [x] `_memoria/perfil.json` — 10 fatos pré-carregados para o agente (2026-06-13)
- [ ] Definir primeiro projeto ativo em `_projetos/`
- [x] Integrar voz-sandbox ao Javis — avatar usa `/v1/chat/completions` (2026-06-13)
