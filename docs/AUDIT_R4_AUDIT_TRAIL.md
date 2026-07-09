# Auditoria R4 — audit trail de approvals

Data: 2026-07-09
Branch: `hardening/r4-audit-trail`

## Decisão

Toda liberação bem-sucedida via `require_persisted_approval()` passa a gerar uma linha em `action_logs`.

## Conteúdo do log

- `source="gate"`
- `intent=<action>`
- `agent=<requested_by>`
- `message` com `approval_id`, `route`, `project_id` e `result=approved`
- `status="approved"`
- `approved=True`

## O que não entra no log

- token local;
- segredos;
- payload bruto sensível.

## Propriedade

- append-only;
- gerado só quando a aprovação é consumida com sucesso;
- replay bloqueado não gera nova linha.

