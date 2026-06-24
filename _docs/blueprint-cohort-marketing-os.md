# Blueprint: COHORT Marketing → OS de projetos do Javis

> Análise estrutural do PDF "COHORT_MARKETING" (board único estilo Miro,
> 14339×11918px, 304 imagens, ~10k de texto posicional). Extraído via PyMuPDF.
> Data: 2026-06-23. Fonte bruta da extração: `cohort_blocks.txt` (raiz, scratch).

## Lógica central
Organograma de uma empresa de marketing onde **cada cargo é um agente de IA**,
em 3 camadas:
1. **Estratégia (topo):** VOCÊ (orquestrador) + Conselheiros "Clones IA"
   (Hormozi, Jobs, Musk) — decidem e cobram, não executam.
2. **Execução (meio):** squads por área, organizados em 5 estágios (AULA 01–05).
3. **Dados/Decisão (base):** Painel de Receita + Ritual Semanal (Escalar/Manter/Matar).

Fio condutor: **output de um agente = input do próximo** (linha de montagem).

## As 7 áreas (= pipeline)
Pesquisa → Oferta → Funil → Conteúdo → Tráfego → Dados → Painel.

## Schema universal de squad (o achado mais valioso)
Cada agente do board é um CONTRATO:
`{ função (faz) · não-faz (delega) · input · output · ferramentas }`
O **"Não-Faz"** é o mecanismo anti-caos — impede um agente de invadir o
território do outro. ESTE é o padrão a adotar em todo `SKILL.md` do Javis.

## Squads identificados
- Pesquisa: Research Analyst, Competitor, Trend Hunting, Swipe File
- Oferta: The Legends (clones) → OfferBook, ICP (prompt A–G)
- Funil: Arquiteto de Funil, Páginas de Vendas (LP/VSL)
- Conteúdo: Conteúdo orgânico, Criativos
- Tráfego: Media Buyer (Create → Optimize → Scale)
- Dados: Análise de Dados, Leitura do Funil, Análise & Decisão
- Painel: Dashboard de Receita
- Acima: AI Head of Marketing (estratégia/budget/métricas), OPS (processos)

## Métricas que importam (movem receita) vs vaidade
- Importam: Receita, CAC, LTV, ROAS, Payback.
- Vaidade (ignorar): likes, impressões, seguidores, alcance.
- Ritual Semanal (30 min): Escalar (ROAS ≥ meta) / Manter (observar) /
  Matar (cortar o que não paga em 72h). Anti-padrões: decidir sem
  significância; olhar só topo do funil.

## Como vira o OS do Javis
| PDF | Javis hoje | Ação |
|---|---|---|
| VOCÊ orquestrador | Jamba | existe |
| Clones IA / conselheiros | Conclave + 17 agentes da mente | formalizar personas c/ lógica de decisão |
| Contrato faz/não-faz/in/out | SKILL.md | **adotar o schema de squad** |
| Output→Input | pipeline campanha (3 gates) | generalizar p/ todo squad |
| Painel + Ritual | Kanban + HUD | add Painel de Receita + ritual (cron) |
| Métricas receita | telemetria de token/custo | estender p/ CAC/LTV/ROAS por projeto |

## O que NÃO copiar
1. Culto às lendas como marketing (use a técnica, não os ídolos).
2. Stack do PDF (ClickUp/Notion/n8n/Make/Hotmart) — mapear funções p/ stack própria.
3. "Treinar clones" — no Javis capacidade = SKILL.md + cérebro forte
   (ver memória javis-agentes-skill-vs-treino).
4. Geração de criativo em massa automática — conflita com regra "criativo só
   via plugin Adobe/Canva".
5. Formato curso/aula — no Javis é pipeline contínuo, não módulos.
6. Números de exemplo (CAC R$87 etc.) — usar dados reais.

## Vem Passear Jampa = primeiro grafo instanciado
ICP A–G → perfilar turista de Jampa; funil anúncio→WhatsApp→reserva com KPI/etapa;
Painel de Receita consolidando WhatsApp + Google Meu Negócio + anúncios
(CAC por passeio, LTV recorrente, ROAS por campanha); ritual semanal de decisão.

## Próximos passos (virar base própria)
1. Definir schema universal de squad em `_docs/` + aplicar a todo SKILL.md.
2. Modelar o grafo do pipeline como DADO (arquivo declarativo squads + arestas).
3. Instanciar a VP como primeiro grafo.
4. Painel de Receita por projeto (estender telemetria atual).
5. Ritual Semanal como cron (humano aprova no gate).
6. Conselheiros como personas do Conclave com lógica de decisão explícita.
