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

- [x] git init dentro de javis/ para isolamento do repositório do usuário (já é repositório próprio, raiz em `C:/Users/noteacer/Desktop/javis`, confirmado 2026-06-17)
- [x] `_memoria/murillo.md` expandido — negócio, setup, estilo de decisão (2026-06-13)
- [x] `_memoria/perfil.json` — 10 fatos pré-carregados para o agente (2026-06-13)
- [x] Definir primeiro projeto ativo em `_projetos/` — Cérebro Jampa conectado como projeto externo real via `project_registry.py` (2026-06-17)
- [x] Integrar voz-sandbox ao Javis — avatar usa `/v1/chat/completions` (2026-06-13)

---

## ✅ Madrugada 16→17/06 — orquestração noturna autônoma (CONCLUÍDO 2026-06-17)

Detalhe completo em `_logs/2026-06-17_orquestracao-noturna.md`. Resumo:
- Backlog do Codex (`codex_backlog.md`): 100% concluído, 5/5 itens.
- Quadro de orquestramento (`/missions`): 5/5 missões em 100% (Conteúdo,
  Interface, SEO, Esquadrão de Estudo, Projetos Externos).
- Esquadrão de estudo (`_treinamento/`): de 0 pra 7 resumos reais escritos
  (repos com README/descrição lida via `gh api`); vídeos seguem manuais
  via NotebookLM (sem conteúdo pra resumir honestamente).
- 3 melhorias de UX/acessibilidade em `app.js`/`style.css`, testadas via
  Playwright.
- Suíte de testes (`tests/`): 54/54 passando após todas as mudanças.

## Pendências em aberto (para o Javis saber e cobrar)

- [ ] ElevenLabs — decidir profundidade da integração e plugar `ELEVENLABS_API_KEY`
- [ ] Figma — apontar workspace/arquivo para o Codex montar o board
- [ ] Resumir os ~18 vídeos do esquadrão de estudo (transcript já funciona, rodar 1-2 por vez pra não bater rate-limit do YouTube)
- [ ] Frente 3 — afinar voz (wake word, latência, exatidão do ASR)
- [ ] Frente 2+ — interface mais proativa além da saudação (feed do que o orquestrador fez)
