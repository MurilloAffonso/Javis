# LeanCTX — Status

Data: 2026-06-10

## Instalação

- Versão: 3.7.5
- Instalação: global via npm (C:\Users\noteacer\AppData\Roaming\npm\lean-ctx.cmd)
- MCP configurado: sim (em C:\Users\noteacer\.claude.json)
- SKILL.md instalado: sim (para Claude Code)

## Doctor — 25/26 checks

Passou:
- lean-ctx in PATH ✅
- versão ✅
- data dir ✅
- stats.json ✅
- Shell allowlist (201 commands) ✅
- MCP config (Claude Code) ✅
- SKILL.md ✅
- Session state ativo (root: javis) ✅

Aviso menor (não crítico):
- Shell aliases: lean-ctx não está no PowerShell profile
  (cosmético — não afeta funcionamento)

## Gain (2026-06-10)

- Tokens salvos: 924K
- Compressão: 88%
- USD economizado: $2.38
- Score: 52/100 (Lv3 Architect)

## Modo de Uso

Claude Code + LeanCTX é o modo padrão.
Claude usa ctx_read, ctx_search, ctx_shell, ctx_tree automaticamente.

Comandos:
```bash
lean-ctx --version    # verificar versão
lean-ctx doctor       # diagnóstico completo
lean-ctx gain --deep  # análise de economia
```
