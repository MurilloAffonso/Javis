# Estudo — Board "Encontro 1" (FigJam): Operação de marketing/vendas por agentes

> Lido direto do board do Figma (modo visualização, sem login) navegando e dando
> zoom em cada coluna. Fonte: figma.com/board/CaMQd6pvtHXOh1DnV07jiq (Encontro 1).
> Metodologia = decomposição em tarefas atômicas (estilo EiOS/AIOX que o senhor
> estudou): cada "agente" é um processo com **Input → Output**, fronteiras claras
> (**O que faz / Não faz**) e **Ferramentas** definidas. Nada de agente que faz tudo.

## Visão geral

O board é um **mapa de uma agência de marketing/vendas rodada por IA**, dividido em
4 módulos (as "AULAS" + um módulo de Dados), totalizando **12 agentes** que se
alimentam em cadeia. O fluxo geral:

```
PESQUISA → CONSTRUÇÃO (funil/página/criativo) → TRÁFEGO → DADOS/DECISÃO
 (descobre o   (monta a oferta e as peças)      (roda     (lê resultado e
  que funciona)                                  anúncios)  decide o próximo passo)
```

A regra de ouro do board: **cada agente tem Input e Output explícitos e um "Não faz"**
— ele entrega pro próximo e NÃO invade a função do outro (ex.: quem cria campanha
"não escreve copy, pede pra COPY"; quem lê dados "não define estratégia").

---

## MÓDULO 1 — PESQUISA (AULA 01) · verde
*Descobrir o que já funciona no mercado antes de criar qualquer coisa.*

| Agente | Input | Output | O que faz | Não faz | Ferramentas |
|---|---|---|---|---|---|
| **Competitor Analysis** | Briefing criativo | Peça pronta (imagem/vídeo) | Monitora concorrentes · mapeia anúncios ativos | Criar conteúdo · rodar campanha | Apify, Claude |
| **Trend Hunting** | 2+ variações | Vencedor identificado | Identifica tendências · mapeia formatos que viralizam · alerta oportunidades de timing | — | Claude, Twitter/X |
| **Swipe File** | Criativos winners encontrados | Swipe file organizado → alimenta COPY e Media Buyer | Salva criativos vencedores · organiza por categoria · alimenta COPY | Copiar diretamente | Figma |

---

## MÓDULO 2 — CONSTRUÇÃO: FUNIL / VENDAS / CRIATIVOS (AULA 02) · bege
*Transformar a pesquisa em oferta: jornada, página de venda e peças.*

| Agente | Input | Output | O que faz | Não faz | Ferramentas |
|---|---|---|---|---|---|
| **Funil** | Briefing de campanha + oferta | Funil mapeado (etapas + metas por etapa) | Desenha a jornada (topo→fundo) · define etapas, gatilhos e CTAs · estabelece KPI por etapa | Escreve copy · sobe campanha | Figma |
| **Páginas de Vendas** | Funil definido + copy aprovada | Página no ar (LP / sales page) | Constrói LP e sales page · aplica o design system · configura pixel e tracking | Escreve a copy · roda tráfego | Figma, Vercel, Claude, Pinterest |
| **Criativos** | Briefing criativo + swipe file | Peça pronta (imagem) → alimenta o Media Buyer | Gera variações de criativo · adapta por plataforma · alimenta o Media Buyer | Define verba/escala · roda campanha | Claude Design |

---

## MÓDULO 3 — TRÁFEGO (AULA 03) · azul
*Colocar dinheiro nos anúncios, otimizar e escalar o que dá retorno.*

| Agente | Input | Output | O que faz | Não faz | Ferramentas |
|---|---|---|---|---|---|
| **Create Campaign** | Briefing + budget | Campanha configurada | Cria a estrutura de campanha | Criar arte (pede pra COPY) · escrever copy (pede pra COPY) | Meta Ads, Google Ads, TikTok Ads |
| **Optimize Ads** | Métricas de campanha | Ajustes implementados | Analisa métricas diariamente · ajusta públicos · pausa o que não funciona · testa variações | Não sobe campanha | Ads Manager, Sheets |
| **Scale Winners** | Ads com ROAS > meta | Budget redistribuído | Aumenta budget do que funciona · expande públicos · replica estruturas vencedoras | Aprovar aumento de budget sozinho (pede ao Head) | Ads Manager |

---

## MÓDULO 4 — DADOS / DECISÃO · vermelho
*Ler o resultado real, decidir o que mexe na receita e entregar num painel.*

| Agente | Input | Output | O que faz | Não faz | Ferramentas |
|---|---|---|---|---|---|
| **Leitura do Funil** | Fontes de dados (vendas, ads, email, páginas) | Números do funil consolidados (métrica por etapa) | Conecta as fontes · lê as métricas de cada etapa · padroniza e limpa os números | Inventa/estima dado · define a estratégia | Hotmart, Meta Ads, ActiveCampaign |
| **Análise & Decisão** | Números do funil consolidados | Decisões priorizadas (o que mover na receita) | Aponta gargalos e oportunidades · calcula CAC, LTV, ROAS e conversão · recomenda as ações que movem receita | Roda a campanha · escreve copy | Supabase, Claude, Google Sheets |
| **Painel** | Métricas + decisões priorizadas | Painel pronto (dashboard que você lê) | Monta o dashboard visual · atualiza com dados reais · entrega pronto pra usar e decidir | Análise manual repetida | Dashboard (HTML), Cron, Vercel |

---

## Padrões que se repetem (o "como" da metodologia)

1. **Tarefa atômica:** todo agente cabe em 1 cartão com Input/Output. Se não cabe,
   vira 2 agentes. (Ex.: "criar campanha" e "otimizar" e "escalar" são 3, não 1.)
2. **Fronteira explícita ("Não faz"):** evita o agente fazer o trabalho do outro
   e perder foco/qualidade. Quem faz arte não roda tráfego; quem lê dado não decide.
3. **Encadeamento por Output→Input:** a saída de um é a entrada do próximo
   (Swipe File → Criativos → Media Buyer → Dados). É uma esteira.
4. **Humano no topo (Head):** decisões de verba/escala pedem aprovação humana
   (Scale Winners "pede ao Head"). Igual aos GATES do nosso pipeline.
5. **Ferramenta certa por tarefa:** Apify (espionar), Claude/Claude Design (criar),
   Meta/Google/TikTok (rodar), Supabase/Sheets (dados), Vercel (publicar).

---

## Conexão com o Javis (o que isso significa pra nós)

Este board é, na prática, **o projeto do que o Javis quer ser**: uma esteira de
agentes com entrada/saída claras. Mapeando direto:

- **Módulo 1 (Pesquisa)** ↔ agentes Analyst + `buscar_conhecimento` + `pesquisar_redes`.
- **Módulo 2 (Construção)** ↔ a **Nova** + a Raia de Conteúdo/Design do nosso Fluxo VP.
- **Módulo 3 (Tráfego)** ↔ o **Midas** + a Raia de Tráfego.
- **Módulo 4 (Dados)** ↔ é o que o Javis **ainda não tem**: um agente que lê
  métricas reais (vendas/ads) e devolve decisão num painel. **Maior lacuna.**

Diferença honesta: o board é genérico de "agência/infoproduto" (Hotmart,
ActiveCampaign, sales page). A Vem Passear é **turismo/serviço local** — o "produto"
é passeio, a conversão é WhatsApp, não checkout de infoproduto. Então a estrutura
(esteira de agentes atômicos) serve 100%, mas as **etapas e ferramentas mudam**
(ex.: no lugar de "sales page/Hotmart", é "post → WhatsApp → reserva").

## Recomendação de próximo passo
Adotar o padrão **Input/Output/Não faz/Ferramentas** nos nossos agentes (hoje eles
têm persona, mas não têm fronteira/contrato explícito). Isso deixaria a
orquestração tão clara quanto esse board — e fecharia o "quem faz o quê" que o
senhor sente que ainda está confuso na interface.

---
*Ressalva: lido da visualização pública do board; reproduzi o texto dos 12 cartões
com fidelidade. Se algum número/ferramenta específico precisar de conferência, dá
pra reabrir e dar zoom no cartão exato.*
