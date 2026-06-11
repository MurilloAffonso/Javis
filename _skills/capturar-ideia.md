# capturar-ideia

## Objetivo

Capturar uma ideia solta de Murillo sem julgamento, organizar em poucas linhas e transformar em registro útil para consulta futura. O objetivo não é desenvolver a ideia agora — é garantir que ela não se perca e que tenha um próximo passo mínimo definido.

## Quando usar

- Murillo manda um pensamento solto, fragmentado ou incompleto.
- Murillo diz "tive uma ideia", "e se fosse possível", "lembra que falei de", "anota isso".
- Murillo está em movimento (andando, dirigindo) e quer registrar rápido.
- Qualquer mensagem que pareça um embrião de algo sem forma ainda.

## Entrada esperada

Texto livre de qualquer tamanho. Pode ser:
- Uma frase solta ("e se eu criasse um app de sons de chuva?")
- Um parágrafo desorganizado com várias ideias misturadas
- Uma pergunta retórica que é na verdade uma ideia disfarçada
- Um link com comentário ("esse negócio aqui, mas diferente")

## Processo

1. Ler a entrada sem tentar expandir.
2. Extrair a ideia central em 1 frase.
3. Classificar em uma categoria (Produto, Negócio, Pessoal, Técnico, Criativo, Outro).
4. Avaliar o possível valor em 1 linha (sem hype, sem pessimismo).
5. Definir o próximo passo mais simples possível.
6. Decidir destino: projeto, tarefa, ou apenas memória.
7. **Não perguntar nada** a menos que a ideia seja completamente incompreensível.

## Saída esperada

Um registro curto e direto com os 6 campos abaixo. Sem introdução, sem conclusão, sem opinião não solicitada.

## Regras de economia de tokens

- Máximo de 6 linhas na saída.
- Não repetir a ideia original — resumir.
- Não pedir confirmação do óbvio.
- Não adicionar contexto de sessões anteriores sem necessidade.
- Perguntar apenas se a ideia for incompreensível.
- Não sugerir expansão imediata — deixar para a skill `transformar-em-projeto`.

## Template de resposta

```
💡 IDEIA CAPTURADA

Resumo: [ideia em 1 frase]
Categoria: [Produto / Negócio / Pessoal / Técnico / Criativo / Outro]
Valor potencial: [1 linha direta]
Próximo passo mínimo: [ação concreta, 15 min ou menos]
Destino: [Projeto / Tarefa / Memória]
Arquivo: _ideias/[slug-da-ideia].md
```
