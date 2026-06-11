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

## Resultado do /doctor e /mcp

> **PENDENTE** — necessário reiniciar o Claude Code para aplicar a mudança no MCP.
> Após reiniciar, rode `/doctor` e `/mcp` e atualize este arquivo com os resultados.

---

## Próximo Passo

1. Fechar o Claude Code completamente.
2. Confirmar que a porta 3111 ainda está ativa (o serviço agentmemory deve estar rodando como Task do Windows).
3. Abrir o Claude Code novamente na pasta `javis`.
4. Rodar `/doctor` — esperado: 0 setup issues.
5. Rodar `/mcp` — esperado: agentmemory aparece como conectado.
6. Atualizar este STATUS.md com os resultados.
