---
tags: [memoria, ferramentas, mcp, javis]
---

# Ferramentas Ativas do Javis

## MCP Servers (todos ativos)

### lean-ctx v3.7.5
- Compressão de contexto — 79.7%, $2.74 economizado
- Ferramentas: `ctx_read`, `ctx_shell`, `ctx_search`, `ctx_tree`, `ctx_edit`
- **Uso obrigatório** em vez de Read/Bash/Grep nativos
- Modos ctx_read: `full`, `signatures`, `diff`, `map`, `lines:N-M`

### AgentMemory v0.9.27
- Porta API: `3111` — Porta dashboard: `3113`
- Processo: `iii` (Task Agendada: `AgentMemory - Javis`)
- Dashboard: http://localhost:3113
- Se travar: `Stop-Process -Name iii -Force` + `Start-ScheduledTask -TaskName "AgentMemory - Javis"`
- Config: `.claude.json` → `cmd /c npx -y @agentmemory/mcp`
- Vault Javis: 8 memórias salvas (arquitetura, regras, protocolo, testes, git…)

### CodeGraph
- 13 arquivos indexados, 177 nós, 315 arestas
- Ferramenta principal: `codegraph_explore` (resposta com código-fonte verbatim)
- Usar ANTES de editar — não durante

### Playwright MCP
- Automação de browser para testes e dashboard
- Usado para verificar AgentMemory dashboard e interagir com UI

## Obsidian (este vault)
- Vault: `C:\Users\noteacer\Desktop\javis`
- ID: `bb1949e8cebbaf9a`
- MOC central: [[JAVIS-CEREBRO]]
- Tema: escuro, accent `#7c3aed`
- Templates em: `_prompts/`

## Pendente / Aguardando aprovação

- **Headroom**: `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install headroom-ai`

---
Relacionado: [[javis-arquitetura]] · [[javis-regras]] · [[javis-protocolo]] · [[JAVIS-CEREBRO]]
