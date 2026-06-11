# Checkpoint — Antes do Hardening do .gitignore

**Data/hora:** 2026-06-11 03:39 (horário local)
**Responsável:** Claude Code — Guardião de Versionamento Seguro
**Fase:** Pré-primeiro-commit do repositório Javis

---

## Objetivo

Blindar o `.gitignore` do Javis antes do primeiro commit, garantindo que logs de voz,
transcrições, estado do AgentMemory, clones de terceiros, caches, modelos e dados
sensíveis nunca sejam versionados acidentalmente.

---

## git status --short (subtree javis/) antes da mudança

```
?? ./
```

(Toda a pasta `javis/` aparece como um único item untracked — nenhum arquivo foi
commitado ainda. O repositório raiz está em `C:\Users\noteacer`.)

---

## Itens identificados como sensíveis ou desnecessários

| Categoria | Caminho |
|---|---|
| Clone terceiro (próprio .git) | `_ferramentas/voz-sandbox/` |
| Clone referência (próprio .git) | `_referencias/ECC/` |
| Clone referência (próprio .git) | `_referencias/silero-vad/` |
| Estado AgentMemory | `data/state_store.db/` |
| Dados Open WebUI | `open-webui-data/` (webui.db, vector_db, cache) |
| Logs de voz | `_apps/javis-local-interface/logs/` |
| Logs voz-sandbox | `_ferramentas/voz-sandbox/logs/` |
| Console logs Playwright | `.playwright-mcp/*.log` |
| Cache ASR/modelos | `_ferramentas/voz-sandbox/cache/`, `models/` |
| Virtualenv | `_ferramentas/voz-sandbox/.venv/` |
| Pycache | `_apps/javis-local-interface/backend/__pycache__/`, outros |
| CodeGraph index | `.codegraph/` (já estava no .gitignore) |

---

## .gitignore antes do hardening

```
node_modules/
__pycache__/
*.pyc
.env
.env.local
_logs/*.tmp
.DS_Store
*.log

# CodeGraph index (gerado localmente, não commitar)
.codegraph/

# Open WebUI — dados persistentes, cache, banco e possíveis segredos
open-webui-data/
```

---

## Confirmações obrigatórias

- [ ] Nenhum arquivo será apagado — apenas `.gitignore` será modificado
- [ ] Nenhum `git add` será executado
- [ ] Nenhum `git commit` será executado
- [ ] Nenhum `git push` será executado
- [ ] Nenhum `git clean` será executado
- [ ] Open WebUI não será tocado
- [ ] Docker não será tocado
- [ ] Execução por voz não será alterada
- [ ] dry_run não será alterado
- [ ] Nada será instalado

**Status:** ✅ CONFIRMADO — operação é exclusivamente edição de .gitignore + validação
