# testar-antes-de-integrar

## Objetivo

Garantir que um módulo novo funciona isoladamente antes de conectá-lo a outro sistema — evitando que bugs de integração se misturem com bugs de implementação.

## Quando usar

- Antes de conectar `voice_bridge.py` ao Open-LLM-VTuber
- Antes de adicionar um novo intent ao Command Router
- Antes de adicionar nova ação à whitelist de `actions.py`
- Antes de conectar o frontend ao backend via FastAPI
- Antes de qualquer integração com sandbox de voz

## Quando não usar

- Mudanças de documentação que não tocam código
- Criação de skill que não afeta código funcional
- Adição de keyword ao Command Router (pode testar inline, sem script)

## Entrada esperada

- Nome do módulo/função a ser testado
- Casos de teste a cobrir (happy path + casos de erro)
- Saída esperada para cada caso

## Processo de verificação (inspirado em ECC verification-loop)

### Fase 1 — Testes unitários
```bash
python _apps/javis-local-interface/tests/test_[modulo].py
```
Todos os testes devem passar antes de continuar.

### Fase 2 — Teste de integração manual
```bash
# Exemplo para voice_bridge:
python backend/voice_bridge.py "abre o youtube"
python backend/voice_bridge.py "apaga meus arquivos"
```
Verificar JSON de saída e entrada no JSONL.

### Fase 3 — Verificar logs
```bash
# Confirmar que o log foi gerado corretamente
cat logs/actions.jsonl | python -c "import sys,json; [print(json.loads(l)) for l in sys.stdin]"
```

### Fase 4 — Aprovação antes de integrar
Somente após as 3 fases acima, apresentar resultado a Murillo e pedir aprovação para integração.

## Saída esperada

```
=== Pré-integração: [nome do módulo] ===
Fase 1 — Testes unitários: [N/N passando]
Fase 2 — Teste manual: [ok/falha]
Fase 3 — Logs: [gerados corretamente / problema: X]
Status: PRONTO PARA INTEGRAR ✅ / NÃO PRONTO ❌
```

## Riscos

- Integrar antes de testar isoladamente → bugs misturados, difícil de depurar
- Testes passando mas teste manual falhando → falso positivo
- Log não gerado → operação sem rastreabilidade

## Regra de aprovação

- Testes passando: Javis pode executar sem aprovação
- Integrar com outro sistema: requer aprovação de Murillo

## Regra de log

- Resultado de cada fase salvo em `_logs/pre-integracao-YYYY-MM-DD_[modulo].md`
- Qualquer falha documentada antes de escalar

## Exemplo bom

```
Murillo: "conecta o voice_bridge ao Open-LLM-VTuber"
Javis: [roda testes, testa manualmente, verifica logs]
[todas as fases passando]
Javis: "Pronto para integrar. Posso prosseguir?"
Murillo: "sim"
[integração feita]
```

## Exemplo ruim

```
Murillo: "conecta o voice_bridge"
Javis: [edita single_conversation.py sem testar primeiro]
→ ERRADO — integração sem verificação prévia
```
