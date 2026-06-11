# transformar-em-projeto

## Objetivo

Transformar uma ideia com potencial em um projeto simples, estruturado e executável. O resultado não é um plano detalhado — é a versão mínima que permite começar com clareza.

## Quando usar

- Murillo quer avançar com uma ideia já capturada.
- Murillo diz "quero levar isso a sério", "como eu começaria isso?", "me ajuda a estruturar".
- Uma ideia em `_ideias/` foi marcada como destino "Projeto".
- Murillo quer saber se algo vale o esforço antes de investir tempo.

## Entrada esperada

- Um resumo da ideia ou o arquivo de ideia capturada.
- Contexto opcional: prazo, recursos disponíveis, restrições.
- Pode ser fragmentado — o Javis organiza.

## Processo

1. Confirmar o objetivo central do projeto em 1 frase.
2. Definir o resultado esperado de forma mensurável ou observável.
3. Propor a primeira versão possível (MVP mínimo).
4. Listar os recursos necessários (tempo, dinheiro, ferramentas, pessoas).
5. Identificar os 2-3 principais riscos.
6. Definir os próximos 3 passos ordenados por dependência.
7. **Não expandir além do necessário para começar.**

## Saída esperada

Estrutura clara de projeto com 7 campos. Sem texto introdutório. Sem histórico da conversa repetido.

## Regras de economia de tokens

- Não resumir o que Murillo já disse — ir direto à estrutura.
- Riscos: máximo 3, somente os reais.
- Próximos passos: máximo 3, ordem importa.
- Não sugerir ferramentas sem que Murillo pergunte.
- Não expandir o MVP — a expansão vem depois, com a skill `planejar-proximo-passo`.

## Template de resposta

```
🚀 PROJETO: [Nome do Projeto]

Objetivo: [o que resolve ou cria em 1 frase]
Resultado esperado: [o que existirá quando estiver pronto]
Primeira versão possível: [descrição do MVP mínimo]

Recursos necessários:
- [recurso 1]
- [recurso 2]

Riscos:
- [risco 1]
- [risco 2]

Próximos 3 passos:
1. [passo — quem faz — quanto tempo]
2. [passo — quem faz — quanto tempo]
3. [passo — quem faz — quanto tempo]

Arquivo: _projetos/[slug-do-projeto].md
```
