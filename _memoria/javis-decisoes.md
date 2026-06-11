---
tags: [memoria, decisoes, historico, javis]
---

# Decisões Técnicas — Histórico

## dry_run=True (permanente)
**Decisão:** Manter `dry_run=True` no `voice_bridge.py` indefinidamente até aprovação explícita de Murillo.
**Por quê:** Segurança — evita execução acidental de comandos por voz em produção.
**Quando mudar:** Só quando Murillo disser explicitamente "libera execução por voz".

## Git: repo standalone em `Desktop/javis`
**Decisão:** `git init` dentro de `javis/` em vez de usar o repo pai (`C:\Users\noteacer`).
**Por quê:** Repositório dedicado no GitHub (`MurilloAffonso/Javis`) — separação limpa.
**Commit inicial:** `cc42b2a` — 92 arquivos.

## Parser manual de YAML em test_intent_consistency.py
**Decisão:** Parser linha a linha em vez de `import yaml`.
**Por quê:** PyYAML não está instalado e instalar pacotes requer aprovação.
**Impacto:** Funciona para a estrutura específica do `commands.yaml`. Não é genérico.

## LeanCTX como camada obrigatória
**Decisão:** Todas as leituras/buscas/shell passam por `ctx_*` — nunca nativos.
**Por quê:** 79.7% de compressão, $2.74 economizado desde o início.

## AgentMemory: cmd wrapper no Windows
**Decisão:** `.claude.json` usa `"command": "cmd", "args": ["/c", "npx", ...]`.
**Por quê:** Claude Code no Windows não resolve `.cmd` direto via spawner.

## Obsidian vault = pasta javis
**Decisão:** A pasta `Desktop/javis` É o vault do Obsidian.
**Por quê:** Tudo em um só lugar — cofre, código, docs, memória.
**ID do vault:** `bb1949e8cebbaf9a`

---
Relacionado: [[javis-arquitetura]] · [[javis-ferramentas]] · [[javis-regras]] · [[JAVIS-CEREBRO]]
