# Auditoria R3 — TTL + single-use em approvals

Data: 2026-07-09  
Branch: `hardening/r3-approval-ttl-singleuse`

## Objetivo

Fechar replay do gate de aprovação:

- cada approval humano aprovado libera uma única execução;
- a aprovação expira por tempo;
- o consumidor do gate continua sendo `gate.py::require_persisted_approval`.

## Mudança de schema

Campo aditivo em `approvals`:

```text
consumed_at TEXT
```

Migração:

- `CREATE TABLE` continua idempotente para bancos novos;
- bancos antigos recebem `ALTER TABLE approvals ADD COLUMN consumed_at TEXT`.

## TTL

Env de controle:

```text
JAVES_APPROVAL_TTL_MIN
JAVIS_APPROVAL_TTL_MIN
```

Regra:

- se `JAVES_APPROVAL_TTL_MIN` existir, ele vence;
- caso contrario, usa `JAVIS_APPROVAL_TTL_MIN`;
- sem valor valido, o default interno e `60` minutos.

Base de expiracao:

- `decided_at` se existir;
- caso contrario, `updated_at`.

## Single-use

Comportamento:

- `valid_for_action()` rejeita approvals com `consumed_at` preenchido;
- `require_persisted_approval()` consome o approval ao liberar a primeira vez;
- se `consume()` falhar, a resposta volta como `approval_required` com `approval_status=consumed`;
- se o approval expirar ao ser consultado, o status e promovido para `expired` de forma aditiva, sem sweeper.

Escolha de design:

- consumo no momento da aprovacao;
- falha fechada por padrão;
- mais simples para evitar replay e condicoes de corrida.

## Testes

- `test_approval_single_use.py`
- `test_approval_ttl.py`
- a bateria R1/R2 continua verde.

## Pendencias R4

- rotacao/UX do token local;
- dashboard de approvals com TTL visivel;
- endurecimento das rotas amplas de chat/voice/agents/train/browser.
