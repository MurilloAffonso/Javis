# Auditoria R4 — Closeout do R3

Data: 2026-07-09
Branch: `hardening/r3-closeout`

## O que foi fechado

- `approvals.consume()` deixou de depender de `db.execute()` misturar `lastrowid` com `rowcount`.
- `db.execute_rowcount()` passou a ser o caminho explícito para updates que precisam de contagem real de linhas afetadas.
- O gate de aprovação persistida agora trata consumo com `>= 1`, reduzindo a fragilidade de replay por retorno ambíguo.

## Impacto

- Não muda o contrato do gate.
- Não altera o schema.
- Não adiciona dependência.
- Mantém TTL e single-use já implementados no R3.

## Validação esperada

- `python -m py_compile _apps/javis-local-interface/backend/*.py`
- pytest focado nos testes de approval do R3

