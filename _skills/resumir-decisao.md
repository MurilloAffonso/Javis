# resumir-decisao

## Objetivo

Registrar decisões importantes de Murillo de forma estruturada para memória futura. Decisões bem registradas evitam retrabalho, explicam o contexto para o futuro e constroem uma base de aprendizado pessoal.

## Quando usar

- Murillo tomou uma decisão importante e quer registrar.
- Murillo diz "decidimos isso", "escolhi seguir por esse caminho", "não vou mais fazer X".
- Uma conversa longa chegou a uma conclusão e precisa ser cristalizada.
- Murillo quer garantir que o Javis "lembre" de uma escolha para sessões futuras.
- Antes de fechar uma sessão de planejamento.

## Entrada esperada

- Descrição da decisão em qualquer formato.
- Contexto da conversa que levou à decisão (opcional).
- Alternativas que foram consideradas (opcional).
- Consequências percebidas (opcional).

## Processo

1. Extrair a decisão central em 1 frase clara.
2. Identificar o motivo principal da decisão.
3. Registrar o contexto mínimo para que o registro faça sentido no futuro.
4. Listar as consequências diretas (o que muda por causa dessa decisão).
5. Definir a próxima ação que a decisão implica.
6. Registrar a data.
7. **Não repetir a conversa inteira — só o essencial para entender a decisão.**

## Saída esperada

Registro estruturado com 6 campos. Deve fazer sentido lido isoladamente, semanas depois, sem contexto da conversa original.

## Regras de economia de tokens

- Não repetir argumentos do processo de decisão — só o resultado.
- Contexto: máximo 2 linhas — o suficiente para entender sem precisar da conversa.
- Consequências: listar somente as que mudam algo concreto.
- Próxima ação: 1 linha específica.
- Se não houver próxima ação clara, escrever "nenhuma ação imediata necessária".
- Salvar em `_memoria/decisoes/` ou `_logs/`.

## Template de resposta

```
📌 DECISÃO REGISTRADA

Decisão: [o que foi decidido em 1 frase afirmativa]
Motivo: [por que essa escolha foi feita — 1-2 linhas]
Contexto: [situação que levou à decisão — máximo 2 linhas]
Consequências:
- [o que muda]
- [o que para de ser feito]
Próxima ação: [ação concreta que a decisão implica]
Data: [YYYY-MM-DD]

Arquivo sugerido: _memoria/decisoes/[YYYY-MM-DD]-[slug-da-decisao].md
```
