# Gestão de Processos — Vem Passear Jampa
### Fluxograma de marketing/conteúdo, estilo quadro Monday (raias por função)

> Espelhado no Fluxograma "Gestão Processos FAST" (ver `_outbox/fluxograma-analise-marketing.md`),
> mas adaptado à operação REAL da Vem Passear: você (Murillo) é o dono/aprovador, os agentes
> **Nova** (criativa) e **Midas** (tráfego) são os "Heads", e o **Quadro Kanban do Javis** faz o
> papel do Monday. Fonte dos papéis e etapas: `linha-editorial.md` (seção 5 e 8).

---

## Legenda

```
  ▶  handover obrigatório (só passa depois da conferência)
 [G] GATE de aprovação do Murillo (humano no loop — só você libera)
 [C] Conferência interna (marca / informação sensível) — reprovado VOLTA, não pula
  ↺  loop de aprendizado (alimenta o próximo briefing)
```

Regra de ouro (igual ao FAST): **nada pula de raia sem passar por uma conferência ou gate.**
Reprovado volta pra raia anterior pra correção, dentro do próprio Quadro.

---

## O quadro (fluxo da esquerda → direita)

```
┌─ RAIA 0 ────────┐   ┌─ RAIA 1 ────────┐   ┌─ RAIA 2 ────────┐   ┌─ RAIA 3 ────────┐   ┌─ RAIA 4 ────────┐   ┌─ RAIA 5 ────────┐
│ BRIEFING        │   │ CONTEÚDO/PAUTA  │   │ ROTEIRO & COPY  │   │ PRODUÇÃO VISUAL │   │ TRÁFEGO/CONVERS.│   │ DISTRIBUIÇÃO    │
│ (Murillo+dados) │ ▶ │ (Nova)          │ ▶ │ (Nova + Midas)  │ ▶ │ (Design)        │ ▶ │ (Midas)         │ ▶ │ (publicar)      │
│                 │   │                 │   │                 │   │                 │   │                 │   │                 │
│ • maré da sem.  │   │ • 10-15 pautas  │   │ • gancho 3s     │   │ • carrossel     │   │ • CTA WhatsApp  │   │ • agendar       │
│ • agenda saídas │   │ • pilar de cada │   │ • roteiro/cena  │   │   (Canva)       │   │ • palavra-chave │   │   (Meta Suite)  │
│ • vagas reais   │   │ • objetivo:     │   │ • texto de tela │   │ • Reel (CapCut) │   │   MARÉ/COMBO    │   │ • Reel/Story    │
│ • fotos novas   │   │   alcance/venda │   │ • legenda + CTA │   │ • gerar_        │   │ • marcar p/     │   │   no momento    │
│ • combos OK     │   │ • formato       │   │ • hashtags      │   │   carrossel.py  │   │   impulsionar   │   │   real          │
│                 │   │                 │   │                 │   │                 │   │                 │   │                 │
│                 │   │   [G] Murillo   │   │   [C] info      │   │   [C] marca /   │   │   [G] Murillo   │   │                 │
│                 │   │   aprova pauta  │   │   sensível:     │   │   Design System │   │   aprova FINAL  │   │                 │
│                 │   │   (maré/vaga/   │   │   maré/preço/   │   │   (cor/fonte/   │   │   (checklist)   │   │                 │
│                 │   │   prioridade)   │   │   vaga conferida│   │   limpeza)      │   │                 │   │                 │
└─────────────────┘   └────────┬────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘   └────────┬────────┘
                               │ reprovado ↺ ajusta                  reprovado ↺ corrige a arte                          │
                               └──────────────                       e volta, sem ir pra Copy                            │
                                                                                                                          ▼
                              ↺ ─────────────────────── RAIA 6: APRENDIZADO (Midas mede) ──────────────────────────────── ↺
                                 Reels: retenção 3s · salvamentos · cliques WhatsApp · reservas → vira briefing da próxima semana
```

---

## Detalhe por raia (quem faz, o quê, com qual arquivo)

### RAIA 0 — BRIEFING DA SEMANA · responsável: **Murillo + dados reais**
- **Entra:** calendário de maré, agenda de saídas, vagas, fotos recentes (`imagens/_FOTOS-AQUI/`), combos autorizados.
- **Sai:** tema da semana + mix de pilares + lista de posts por dia.
- **Humano no loop:** você confirma agenda, vagas e prioridades (nada de pauta sobre maré/vaga que não existe).

### RAIA 1 — CONTEÚDO / PAUTA · responsável: **Nova (criativa)**
- Gera 10-15 pautas a partir do **Banco de 30 ideias** e dos **6 pilares** (`linha-editorial.md` §1 e §7).
- Define pilar, objetivo (alcance/confiança/dúvida/venda) e formato (Reel/carrossel/story).
- Salva a pauta escolhida em `posts/pauta-semana.md`.
- **[G] GATE 1 — Murillo aprova a pauta.** Regra editorial: a cada 10 posts, no máx. 2 de venda direta.
  Reprovado ↺ Nova ajusta antes de ir pro roteiro.

### RAIA 2 — ROTEIRO & COPY · responsável: **Nova + Midas**
- Nova entrega: gancho dos 3s, roteiro por cena, texto de tela, legenda, CTA, hashtags, sugestão de capa.
- Midas entrega: CTA alternativo de WhatsApp + palavra-chave de atendimento (MARÉ/COMBO/SEIXAS/LITORAL).
- **[C] Conferência de info sensível:** maré, preço, horário e vaga conferidos (não prometer o que depende do clima).

### RAIA 3 — PRODUÇÃO VISUAL · responsável: **Design**
- Carrossel/capas no **Canva**; Reels/trends/depoimentos no **CapCut**; peça premium no **Adobe Express**; ajuste de campo no **InShot**.
- Atalho automatizado: `gerar_carrossel.py` com as fotos de `imagens/_FOTOS-AQUI/` → peças em `outputs/`.
- Nome de arquivo padrão: `YYYY-MM-DD_pilar_passeio_formato_tema` (`linha-editorial.md` §8).
- **[C] Conferência de marca:** cor/fonte/Design System, arte limpa (sem poluir). Reprovado ↺ corrige a arte e volta — **não avança pra Tráfego**.

### RAIA 4 — TRÁFEGO / CONVERSÃO · responsável: **Midas**
- Define CTA final, segmentação de impulsionamento e marca os posts com potencial de anúncio.
- **[G] GATE 2 — Murillo aprova o pacote final (peça + copy) pelo CHECKLIST de aprovação:**
  maré confere? vaga existe? CTA aponta pro canal certo? cliente autorizou imagem? legenda sem promessa exagerada? Reel com gancho nos 3s?
  Reprovado ↺ volta pra Design ou Copy conforme o erro.

### RAIA 5 — DISTRIBUIÇÃO · responsável: **Murillo / Javis**
- Agendar pelo **Meta Business Suite** quando der; Reels com áudio/trend e Stories de bastidor publicados no momento real.
- Registrar o que foi publicado (data, formato, link) em `posts/pauta-semana.md`.

### RAIA 6 — APRENDIZADO ↺ · responsável: **Midas mede, Murillo valida**
- Métricas por conteúdo: retenção 3s, salvamentos, compartilhamentos, **cliques no WhatsApp, reservas fechadas**.
- Ritual semanal: Midas aponta os 3 melhores → Nova transforma vencedores em variações → você diz quais trouxeram cliente real.
- **Isso vira o briefing da próxima semana** (fecha o ciclo).

---

## Como isso vive no Javis (não é só papel)

- Este fluxo já é a missão **"Pipeline Marketing — Vem Passear Jampa"** no Quadro Kanban (`_data/codex_backlog.md`),
  com os 2 gates de aprovação que só você marca.
- As raias batem com os agentes da "Mente" (view Mente do Javis): Conteúdo↔criação, Design↔produção, Tráfego↔conversão.
- Próximo passo natural: rodar a RAIA 1 de verdade (Nova propõe as 3 pautas da semana lendo a linha editorial).
