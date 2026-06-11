# quality-gate

## Objetivo

Antes de considerar uma tarefa concluída, verificar se o código/configuração atende critérios mínimos de qualidade: testes passando, sem erros silenciosos, logs funcionando, comportamento seguro preservado.

## Quando usar

- Ao finalizar qualquer módulo Python do Javis Local Interface
- Antes de apresentar resultado de uma ETAPA a Murillo
- Antes de pedir aprovação para integrar algo novo
- Quando Murillo pergunta "está pronto?"

## Quando não usar

- Para arquivos de documentação ou Markdown — não requer gate técnico
- Para skills — revisão manual é suficiente
- Correções de 1 linha óbvias

## Checklist de qualidade (Python — Javis Local Interface)

### 1. Sem erros de importação
```bash
python -c "import command_router, actions, logger, voice_bridge"
```
Deve importar sem erro.

### 2. Testes passando
```bash
python _apps/javis-local-interface/tests/test_command_router.py
python _apps/javis-local-interface/tests/test_voice_bridge.py
```
Todos devem passar: N/N.

### 3. Sem erros silenciosos
- Todo `except` tem `logger.log()` ou re-raise — sem `pass` nu
- Nenhuma ação perigosa passa pelo filtro

### 4. Logs funcionando
```bash
python backend/voice_bridge.py "abre o youtube"
# Verificar que actions.jsonl recebeu a entrada
```

### 5. dry_run preservado
- `voice_bridge.py` ainda tem `dry_run: True`
- Nenhuma ação foi removida da lista de BLOCKED_INTENTS sem aprovação

### 6. Whitelist intacta
- `actions.py` não tem chamada a `subprocess` com input do usuário
- Nenhum `eval()` ou `exec()` adicionado

## Saída esperada

```
=== Quality Gate — [módulo/tarefa] ===
[PASS] importação sem erro
[PASS] N/N testes
[PASS] sem erros silenciosos (except com log)
[PASS] logs JSONL funcionando
[PASS] dry_run: True preservado
[PASS] whitelist sem shell arbitrário
Status: APROVADO ✅ / REPROVADO ❌ (detalhe)
```

## Riscos

- Marcar "pronto" sem rodar o gate → bugs chegam à integração
- Gate muito complexo → ninguém usa → inútil
- Gate ignorado por pressão de tempo → acumula débito técnico

## Regra de aprovação

- Gate pode ser rodado sem aprovação
- Se reprovado: corrigir o problema antes de pedir aprovação de Murillo

## Regra de log

- Resultado do gate em `_logs/quality-gate-YYYY-MM-DD_[tarefa].md` (opcional para tarefas pequenas)
- Obrigatório para gates antes de integração

## Exemplo bom

```
Javis: [termina de escrever voice_bridge.py]
Javis: [roda quality gate — todos os checks passam]
Javis: "Quality gate aprovado. voice_bridge pronto."
```

## Exemplo ruim

```
Javis: [termina de escrever voice_bridge.py]
Javis: "Pronto! voice_bridge criado."
→ ERRADO — sem verificar se importa, se testa, se loga
```
