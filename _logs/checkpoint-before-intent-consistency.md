# Checkpoint — Antes do Teste de Consistência de Intents

**Data/hora:** 2026-06-11 04:06 (horário local)
**Responsável:** Claude Code — Auditor de Consistência de Intents
**Fase:** Criar teste de consistência backend ↔ YAML antes de liberar execução real por voz

---

## Objetivo

Detectar divergências entre:
1. `backend/command_router.py` — lógica real
2. `config/commands.yaml` — documentação/config
3. `frontend/app.js` — interface (auditado, não modificado nesta etapa)

Esta etapa cria apenas um **teste de consistência**. Não altera a arquitetura de roteamento.

---

## git status --short (subtree javis/)

```
?? ./
```

---

## Auditoria rápida (resultado completo na ETAPA 2 do relatório)

### Backend vs YAML — sem divergência ✅
Todos os 13 intents presentes em ambos com `risk_level`, `requires_approval` e `action` idênticos.

### Frontend vs Backend — divergência encontrada ⚠️
`abrir_projeto` está no backend e no YAML mas **ausente** no `frontend/app.js`:
- Não aparece em RULES
- Não aparece no RISK map
- Não aparece em MESSAGES

→ Frontend continuará usando `MESSAGES["desconhecido"]` como fallback (comportamento atual).
→ Será corrigido em etapa futura.
→ app.js não será alterado nesta etapa.

---

## Confirmações obrigatórias

- ✅ Apenas teste de consistência — nenhuma lógica de roteamento será alterada
- ✅ `dry_run=True` continuará hardcoded em `voice_bridge.py` — NÃO será alterado
- ✅ Nenhuma execução real por voz será liberada
- ✅ `frontend/app.js` não será alterado nesta etapa
- ✅ Nenhum `git add` / `git commit` / `git push` será executado
- ✅ Nada será instalado
