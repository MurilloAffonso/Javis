# criar-plano-semanal

## Objetivo

Transformar o que está na cabeça de Murillo (ideias abertas, projetos em andamento, compromissos da semana) em um plano semanal claro e leve — não um calendário, mas uma sequência de foco. O objetivo é começar a semana sabendo o que importa, sem precisar repensar isso toda manhã.

## Quando usar

- Murillo diz "faz meu plano da semana", "o que faço essa semana", "me ajuda a organizar a semana".
- Início de semana (segunda ou domingo à noite).
- Depois de uma semana caótica, para retomar o fio.
- Quando há muitos projetos em paralelo e nenhuma clareza de sequência.

## Entrada esperada

Qualquer combinação de:
- Lista de tarefas, projetos ou ideias abertas (formatada ou não).
- Contexto da semana: energia disponível, compromissos fixos, prazos.
- Apenas "faz meu plano" — nesse caso usar o que está em `_projetos/` e `_ideias/`.
- Quantidade de dias disponíveis (padrão: 5, Seg–Sex).

## Processo

1. Mapear o que está em aberto (projetos em `_projetos/`, ideias em `_ideias/`, itens mencionados pelo Murillo).
2. Identificar o **foco principal da semana** — 1 projeto ou tema que deve avançar mais.
3. Selecionar no máximo 3 prioridades semanais totais (foco + 2 secundários).
4. Distribuir 1 ação por dia (Seg–Sex) — sem sobrecarga, sem dias vazios.
5. Listar explicitamente o que **não entra** essa semana.
6. **Não alocar horários** — só sequência e foco por dia.
7. **Não incluir tudo** — o plano deve ter espaço para imprevistos.

## Saída esperada

Template fixo abaixo. Sem introdução, sem conclusão, sem perguntas de confirmação.

## Regras de economia de tokens

- Máximo de 15 linhas na saída.
- Ações por dia: 1 frase específica, não uma lista.
- "Não fazer" é obrigatório — sem essa seção o plano não tem fronteiras.
- Não repetir o contexto dado por Murillo — só o plano.
- Não oferecer versão alternativa do plano.
- Não perguntar se quer expandir algum dia.

## Template de resposta

```
📅 PLANO SEMANAL — [Semana de DD/MM]

Contexto: [1 linha — o que define essa semana]
Foco principal: [projeto ou tema dominante]

Prioridades:
1. [mais importante]
2. [segundo]
3. [terceiro — opcional]

Dias:
Seg: [ação concreta]
Ter: [ação concreta]
Qua: [ação concreta]
Qui: [ação concreta]
Sex: [ação concreta ou revisão semanal]

Deixar para depois: [o que não cabe essa semana — 1 linha]
Não fazer: [o que Murillo vai querer fazer mas não deve — 1 linha]
```
