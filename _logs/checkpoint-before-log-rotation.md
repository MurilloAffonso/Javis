# Checkpoint — Antes da Rotação de Logs

**Data/hora:** 2026-06-11 04:00 (horário local)
**Responsável:** Claude Code — Auditor de Logs Operacionais
**Fase:** Melhoria de logging antes de liberar execução real por voz

---

## Objetivo

1. Implementar rotação diária: `logs/actions.jsonl` → `logs/actions-YYYY-MM-DD.jsonl`
2. Adicionar campos de auditoria ausentes: `note`, `normalized_text`, `confidence`, `latency_ms`
3. Criar skill `revisar-logs-de-voz.md`
4. Criar `tests/test_logger.py`

---

## git status --short (subtree javis/)

```
?? ./
```

(Toda pasta `javis/` sem commits — git root em `C:\Users\noteacer`)

---

## Estado atual do logger

- **Arquivo:** `backend/logger.py`
- **Log gerado em:** `logs/actions.jsonl` (arquivo único, sem rotação)
- **Campos atuais:** `timestamp`, `source`, `user_text`, `intent`, `risk_level`,
  `requires_approval`, `approved`, `action_result`, `message`, `error`, `duration_ms`
- **Campos ausentes:** `note`, `normalized_text`, `confidence`, `dry_run` (explícito),
  `would_execute` (explícito), `latency_ms` (renomear duration_ms)
- **Problema:** `note` existe no resultado do voice_bridge mas NÃO é passado ao logger

---

## Arquivos que serão modificados

| Arquivo | Mudança |
|---|---|
| `backend/logger.py` | Rotação diária + campos explícitos |
| `backend/voice_bridge.py` | Passar `note` no extra dict das chamadas ao logger |
| `tests/test_voice_bridge.py` | Atualizar `test_log_gerado` para `actions-*.jsonl` |
| `tests/test_logger.py` | Criado do zero |
| `_skills/revisar-logs-de-voz.md` | Criado do zero |

---

## Confirmações obrigatórias

- ✅ Nenhum log existente será apagado — rotação só altera o NOME dos novos arquivos
- ✅ `dry_run=True` continuará hardcoded em `voice_bridge.py` — NÃO será alterado
- ✅ Nenhuma execução real por voz será liberada
- ✅ Nenhum `git add` / `git commit` / `git push` será executado
- ✅ Open WebUI e Docker não serão tocados
- ✅ Nada será instalado
