# Pipeline de Gestão de Marketing (Conteúdo → Design → Tráfego)

> Extraído do fluxograma da agência FAST (`Downloads/estudo/Fluxograma .pdf`),
> removendo as partes de contrato/financeiro/comercial. Fica só a parte de
> **como gerir** um cliente/projeto depois que ele já entrou: quem faz o quê,
> em que ordem, e onde estão os portões de aprovação. Pensado para virar
> missão real no `_data/codex_backlog.md` (cada etapa = uma seção, cada passo
> = uma task `- [ ]`).

## Por que isso interessa pro Javis

O Javis já tem 2+ projetos de conteúdo rodando (Vem Passear Jampa, Cérebro
Jampa) sem um fluxo formal — as tarefas do backlog hoje são soltas, sem
estágio nem aprovação. Esse pipeline dá uma estrutura de **3 estágios com
portão de aprovação entre eles**, que é o que faltava.

## Os 3 estágios

### 1. Conteúdo (planejamento)
- Responsável sobe as informações do cliente/marca (briefing, referências,
  linha editorial) — equivalente ao que já existe em
  `_projetos/cerebro-jampa/linha-editorial.md`.
- Equipe/agente faz o planejamento e pesquisa de conteúdo (pauta).
- Pauta vai para aprovação (do cliente, ou do "head" do projeto — no caso do
  Javis, Murillo).
  - **Reprovado** → reunião/ajuste de alinhamento, volta pro planejamento.
  - **Aprovado** → segue pro estágio 2.

### 2. Design (produção visual)
- Responsável estuda o perfil/marca e distribui pro agente/pessoa certa
  (ex: gerador de carrossel, Adobe).
- Produção das peças.
- Conferência interna (1ª revisão) — se reprovado, volta pra produção.
- 2ª conferência (aprovação final) — quem aprova confere consistência com a
  marca antes de liberar.
- Aprovado → segue pro estágio 3 (ou direto pra publicação, se não houver
  tráfego pago envolvido).

### 3. Tráfego / Distribuição (quando aplicável)
- Define quem roda a distribuição (agente de tráfego, ou publicação direta
  em redes/WhatsApp).
- Briefing de criativos + referências specíficas pra essa etapa.
- Prazo definido pra retorno das artes finais (no fluxograma original: até
  7 dias — ajustável).
- Campanha/publicação roda.
- Monitoramento contínuo (métricas, engajamento).

## Portões de aprovação (não pular)

| Portão | Entre | Critério |
|---|---|---|
| P1 | Conteúdo → Design | Pauta aprovada por quem decide a linha editorial |
| P2 | Design (interna) | Peça bate com Design System/Brandbook do projeto |
| P3 | Design → Tráfego | Aprovação final antes de publicar/rodar campanha |

Sem aprovação no portão, a tarefa **não avança de coluna** — isso já mapeia
1:1 com o Quadro Kanban do Javis (`pending`/`running`/`done`): cada portão é
um ponto onde a tarefa só pode virar `done` se alguém (ou um agente revisor)
confirmar o critério acima.

## Como ativar isso como missão real

Pra rodar de verdade, copiar o bloco abaixo pro `_data/codex_backlog.md`
(uma seção nova = uma missão nova, aparece automático no Quadro):

```markdown
## Pipeline Marketing — <nome do projeto>
- [ ] Planejar pauta de conteúdo pra <projeto>, com base na linha editorial existente
- [ ] Aprovar pauta (revisão humana — Murillo)
- [ ] Produzir peças visuais da pauta aprovada
- [ ] Revisão interna das peças (consistência de marca)
- [ ] Aprovação final antes de publicar/distribuir
- [ ] Publicar/distribuir e monitorar resultado
```

Cada `- [ ]` vira um node arrastável no Quadro. Os portões de aprovação ficam
explícitos como tasks próprias (não escondidos dentro de uma task maior) —
assim dá pra ver no board exatamente onde uma pauta está travada esperando
aprovação, em vez de só "em andamento".

## Próximo passo (se Murillo quiser)

- Adaptar pro projeto que estiver mais ativo agora (Vem Passear Jampa) e
  testar um ciclo completo real.
- No Quadro: diferenciar visualmente uma task de "aprovação" das demais
  (hoje todo node é igual) — fica fácil saber que aquele card específico é
  um portão, não uma execução.
