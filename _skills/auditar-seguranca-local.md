# auditar-seguranca-local

## Objetivo

Revisar periodicamente se as proteções do Javis Local Interface ainda estão funcionando: Command Router bloqueando ações perigosas, logs sendo gerados, dry-run ativo, whitelist de ações correta.

## Quando usar

- Antes de liberar execução por voz (sair do dry-run)
- Depois de qualquer mudança no `command_router.py` ou `actions.py`
- Quando novos comandos foram adicionados ao sistema
- Mensalmente, como checagem de rotina
- Quando Murillo suspeitar de comportamento inesperado

## Quando não usar

- Verificações de produção em sistemas externos (Open WebUI, Ollama) — este é só para o Local Interface
- Durante mudanças em andamento — auditar depois que a mudança estiver estável

## Entrada esperada

- Nenhuma entrada necessária — o script de testes cobre tudo
- Opcionalmente: lista de novos comandos a validar

## Processo

1. Rodar `python _apps/javis-local-interface/tests/test_command_router.py`
2. Rodar `python _apps/javis-local-interface/tests/test_voice_bridge.py`
3. Verificar que `logs/actions.jsonl` está sendo escrito
4. Confirmar que `acao_perigosa` continua bloqueada
5. Confirmar que `dry_run: true` no voice_bridge
6. Verificar whitelist em `actions.py` — sem shell arbitrário
7. Verificar que `SAFE_INTENTS` no voice_bridge não inclui `acao_perigosa` ou `abrir_terminal`

## Saída esperada

```
=== Auditoria de Segurança — Javis Local Interface ===
[PASS] command_router bloqueia acao_perigosa
[PASS] voice_bridge.dry_run = True
[PASS] logger grava JSONL corretamente
[PASS] actions.py sem shell arbitrário
[PASS] whitelist SAFE_INTENTS correta
[PASS] N/N testes passando
Status: SEGURO ✅
```

## Riscos

- Falha silenciosa no logger → ações sem registro → impossível auditar depois
- `acao_perigosa` removida da lista de blocked por engano
- dry_run alterado para False sem aprovação de Murillo

## Regra de aprovação

- Auditoria não requer aprovação — é somente leitura
- Qualquer correção encontrada requer aprovação antes de aplicar

## Regra de log

- Salvar resultado da auditoria em `_logs/auditoria-YYYY-MM-DD.md`
- Se encontrar problema: escalar para Murillo antes de qualquer mudança

## Exemplo bom

```
Murillo: "antes de liberar execução por voz, audita o sistema"
Javis: [roda testes, verifica dry_run, verifica whitelist]
Resultado: todos os checks passando, seguro para prosseguir
```

## Exemplo ruim

```
Murillo: "pode liberar execução por voz"
Javis: [altera dry_run diretamente sem auditar]
→ ERRADO — nunca pular a auditoria antes de mudança de fase
```
