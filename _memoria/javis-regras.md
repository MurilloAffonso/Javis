---
tags: [memoria, regras, segurança, javis]
---

# Regras Críticas do Javis

> Estas regras se aplicam a qualquer agente ou Claude Code trabalhando neste projeto.

## Regras NUNCA violar

1. **`dry_run=True`** — jamais mudar para `False` em `voice_bridge.py`
2. **NÃO fazer `git commit`** sem aprovação explícita de [[murillo]]
3. **NÃO fazer `git push`** sem ordem explícita
4. **NÃO instalar pacotes** sem explicar o impacto antes
5. **NÃO mexer no Open WebUI** ou Docker sem aprovação
6. **NÃO alterar `frontend/app.js`** sem aprovação
7. **Trabalhar SOMENTE** dentro de `C:\Users\noteacer\Desktop\javis`

## Regras de operação

- Usar `ctx_read` / `ctx_shell` / `ctx_search` sempre (nunca Read/Bash/Grep nativos)
- Preferir edições cirúrgicas (`Edit`) a reescritas completas (`Write`)
- Ler arquivo completo com `ctx_read(path, "full")` ANTES de qualquer edição
- Registrar decisões técnicas em `_logs/YYYY-MM-DD_nome.md`

## Preferências de Murillo

- Respostas diretas, sem enrolação, sem introduções longas
- Sempre com próximo passo concreto
- Curto por padrão — mais detalhes só quando pedido
- Simplicidade acima de completude

---
Relacionado: [[murillo]] · [[javis-arquitetura]] · [[javis-protocolo]] · [[JAVIS-CEREBRO]]
