# Spec — Hierarquia de Agentes do Javis (board estilo "AI Agents for Sales")

Objetivo: montar no Figma/FigJam um organograma em árvore dos agentes do
Javis, no mesmo estilo visual da referência ("42 AI Agents for Sales"):
cards conectados por linhas, cada card com avatar/emoji, nome, @papel,
uma linha de descrição, tags de skills, ícones de integração e um ponto
de status (verde=online, amarelo=idle, cinza=offline).

Fonte de verdade dos agentes: `_apps/javis-local-interface/frontend/app.js`
(const `GALLERY_AGENTS`). NÃO inventar agentes — usar exatamente estes 11.

## Hierarquia (árvore)

```
                          ┌─────────────────────┐
                          │  🧬 Orion  @master   │   (raiz — orquestrador)
                          │  status: online      │
                          └──────────┬──────────┘
        ┌───────────────┬───────────┼───────────────┬───────────────┐
   ┌────┴────┐     ┌────┴────┐  ┌────┴────┐    ┌────┴────┐
   │👑 Titan │     │📢 Vera  │  │📊 Dara  │    │🔄 Recap │
   │ @cro    │     │ @cmo    │  │@data-eng│    │@followup│
   │ VENDAS  │     │CRIATIVO │  │ DADOS   │    │  OPS    │
   └────┬────┘     └─────────┘  └────┬────┘    └─────────┘
        │ (squad vendas)              │ (squad dados)
   ┌────┼────┬────────┬────────┐  ┌──┼──────┬────────┐
 ┌─┴─┐┌─┴──┐┌┴───┐┌───┴┐    ┌──┴─┐┌┴────┐┌─┴─┐
 │Khan││Phan││Blade││Brief│   │Intel││Prism││Ana│
 │@bdr││@clo││@bdr ││@disc│   │@call││@ins ││@an│
 │-glb││ser ││-en  ││overy│   │-intel│ight ││aly│
 └────┘└────┘└─────┘└─────┘   └─────┘└─────┘└───┘
```

## Mapa exato (id, nome, papel, esquadrão, status, emoji)

Nível 1 (raiz):
- orion — Orion — @master — ops — online — 🧬 — "Orquestra todos os agentes e decisões estratégicas."

Nível 2 (líderes de esquadrão, ligados a Orion):
- titan — Titan — @cro — ops/vendas — online — 👑 — lidera o time de vendas
- vera  — Vera  — @cmo — criativo — idle — 📢 — marca, conteúdo e campanhas
- dara  — Dara  — @data-eng — dados — idle — 📊 — métricas, CRM, dashboards
- recap — Recap — @followup — ops — online — 🔄 — follow-ups de todas as interações

Nível 3 — squad VENDAS (ligados a Titan):
- khan    — Khan    — @bdr-global — online — 📞 — outbound global, prospecção
- phantom — Phantom — @closer     — online — 🎯 — negociação e fechamento
- blade   — Blade   — @bdr-en     — online — ⚔️ — prospecção em inglês
- brief   — Brief   — @discovery  — idle   — 📋 — discovery e briefings

Nível 3 — squad DADOS (ligados a Dara):
- intel — Intel — @call-intel — offline — 🔍 — pesquisa de mercado/concorrência
- prism — Prism — @insight     — idle    — 💎 — dados brutos → insights
- ana   — Ana   — @analyst     — idle    — 📈 — análise de performance

## Estilo dos cards (espelhar a referência)
- Largura ~220px, cantos arredondados, fundo escuro (#1a1a2e ou similar),
  borda sutil. Avatar/emoji no topo-esquerda, nome em negrito, @papel menor.
- Tag do esquadrão (VENDAS/DADOS/CRIATIVO/OPS) com cor por esquadrão.
- Linha de descrição em cinza claro.
- Ponto de status no canto: verde=online, amarelo=idle, cinza=offline.
- Conectores: linhas ortogonais (cotovelo) ligando pai→filhos, como na foto.

## Regras
- NÃO commitar nada. NÃO criar fora do arquivo Figma que o Murillo já deixou
  aberto/conectado — confirmar o arquivo certo antes de desenhar.
- Acentuação correta em português.
