# AgentMemory — Status de Configuração

**Data:** 2026-06-10
**Versão agentmemory CLI:** 0.9.27
**Versão iii:** 0.11.2

---

## Diagnóstico

### MCP com problema
**agentmemory**

### Causa provável
O Claude Code no Windows não consegue executar comandos `.cmd` (como `npx.cmd`) diretamente quando o campo `"command"` aponta para `npx`. O spawner do Claude Code precisa do wrapper `cmd.exe /c` para resolver arquivos `.cmd` no PATH.

Comparação: o MCP `playwright` no mesmo `.claude.json` já usava `"command": "cmd"` com `"/c", "npx"` — padrão correto. O `agentmemory` estava sem esse wrapper.

### Portas verificadas (2026-06-10)
| Porta | Serviço         | Status        |
|-------|-----------------|---------------|
| 3111  | agentmemory API | **ATIVA** (IPv4 ok) |
| 3113  | agentmemory dashboard | **ATIVA** (IPv4 ok) |

> Nota: `Test-NetConnection` reporta warning de IPv6 (::1) mas retorna `True` via IPv4 — comportamento normal no Windows.

### .claude.json
- JSON válido: **SIM**
- Backup criado em: `~/.claude.json.backup-javis`

---

## Correção Aplicada

Antes:
```json
"agentmemory": {
  "command": "npx",
  "args": ["-y", "@agentmemory/mcp"],
  ...
}
```

Depois:
```json
"agentmemory": {
  "command": "cmd",
  "args": ["/c", "npx", "-y", "@agentmemory/mcp"],
  ...
}
```

`AGENTMEMORY_URL` permanece apontando para `http://localhost:3111`.

---

## Resultado (2026-06-11)

**STATUS: OPERACIONAL**

- MCP conectado e respondendo (memory_save, memory_recall, ferramentas completas ativas)
- Tarefa agendada: `AgentMemory - Javis` (Windows Task Scheduler)
- Processo: `iii` — reiniciar via task scheduler se travar
- Porta 3111: API ativa
- Porta 3113: Dashboard em http://localhost:3113

### Se o processo iii travar (timeout):
```powershell
Stop-Process -Name iii -Force
Start-ScheduledTask -TaskName "AgentMemory - Javis"
```

---

## Vault Javis (2026-06-11)

8 memórias salvas cobrindo:
- Arquitetura e stack do projeto
- Regras críticas (dry_run, git, escopo)
- Protocolo de sessão (abrir/fechar)
- Ferramentas MCP ativas (lean-ctx, codegraph, playwright)
- Estado dos testes (189/189 passando)
- Próximos passos
- Git/GitHub: https://github.com/MurilloAffonso/Javis.git
- Obsidian vault (ID: 03722e6d2a77c12e)
