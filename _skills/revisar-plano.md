# revisar-plano

## Objetivo

Revisar um plano antes de executar para evitar retrabalho, gasto desnecessário, excesso de ferramentas e decisões precipitadas. Um plano revisado economiza mais tempo do que um plano executado errado.

## Quando usar

- Murillo está prestes a começar algo e quer uma segunda opinião rápida.
- Murillo diz "faz sentido esse plano?", "tem algo errado aqui?", "o que pode dar problema?".
- Um projeto foi estruturado com `transformar-em-projeto` e vai ser executado.
- Murillo quer evitar repetir um erro que já aconteceu antes.
- Antes de investir tempo, dinheiro ou energia em algo.

## Entrada esperada

- Plano em qualquer formato (bullet points, texto, arquivo de projeto).
- Contexto do objetivo final.
- Restrições conhecidas (tempo, orçamento, ferramentas disponíveis).
- Opcional: histórico de tentativas anteriores.

## Processo

1. Ler o plano uma vez sem interromper.
2. Identificar o que está claro e bem definido.
3. Identificar pontos ambíguos, suposições não verificadas ou lacunas.
4. Avaliar riscos reais (não riscos hipotéticos).
5. Sugerir simplificações onde o plano está mais complexo do que precisa.
6. Emitir uma recomendação direta: executar, ajustar ou repensar.
7. **Não reescrever o plano inteiro — apontar mudanças cirúrgicas.**

## Saída esperada

Revisão estruturada em 5 campos mais uma decisão final. Sem repetir o plano inteiro.

## Quando não usar

- Plano com menos de 3 passos e risco zero — executar direto
- Murillo só quer começar e não pediu revisão — não impor o processo
- Revisão já foi feita e Murillo aprovou — não revisar de novo sem motivo

## Riscos

- Revisar o mesmo plano repetidamente cria paralisia, não qualidade
- Identificar riscos hipotéticos demais → ruído sem valor
- Recomendar "repensar" sem motivo sólido → desestimula Murillo

## Regra de aprovação

- Não requer aprovação para revisar — é uma consulta
- Não executar nada durante a revisão — só analisar e recomendar

## Regra de log

- Não requer log obrigatório — é análise, não ação
- Registrar em `_logs/` somente se a decisão for significativa (ADR)

## Exemplo bom

```
Murillo: "faz sentido eu criar um FastAPI agora para a Local Interface?"
Javis: [revisa o plano, aponta que v0 CLI ainda não foi validado com uso real]
Decisão recomendada: ajustar primeiro — validar CLI antes de adicionar servidor
```

## Exemplo ruim

```
Murillo: "faz sentido?"
Javis: [reescreve o plano inteiro com 20 novos passos]
→ ERRADO — revisão deve ser cirúrgica, não uma reescrita
```

## Regras de economia de tokens

- Não reproduzir o plano de entrada na resposta.
- "O que está bom" deve ser 1-3 itens apenas.
- Riscos: somente os que podem realmente travar a execução.
- Simplificações: máximo 3 sugestões.
- Decisão final deve ser uma linha clara: executar / ajustar primeiro / repensar.
- Não pedir confirmação — emitir a recomendação.

## Template de resposta

```
🔍 REVISÃO DO PLANO

✅ O que está bom:
- [item]
- [item]

⚠️ O que está confuso ou incompleto:
- [ponto]

🚨 Riscos reais:
- [risco 1]
- [risco 2]

✂️ O que simplificar:
- [sugestão cirúrgica]

📌 Decisão recomendada: [executar / ajustar primeiro / repensar]
Motivo em 1 linha: [justificativa direta]
```
