# 🗺️ ROADMAP — Evolução Vem Passear Jampa + Javis

**Versão:** rascunho p/ aprovação · **Data:** 2026-06-16 · **Status:** ⏳ aguardando aprovação do Murillo (não construir nada antes)

> Prioridade definida por Murillo: **Fase 1 (WhatsApp)** + **Fase 2 (Higgsfield/site)** primeiro. **Fase 3 (Javis auto-evolutivo)** fica estruturada aqui, mas construída por último.

---

## 🎯 Princípio de execução
Uma frente por vez, entregue redonda → Murillo aprova → commit → roda → próxima.
Nada de "ativar tudo de uma vez". Cada fase tem um **entregável testável**.

---

## 🥇 FASE 1 — Motor de conversão no WhatsApp (OpenWA)
**Objetivo:** quando alguém manda "PISCINAS", o sistema responde na hora, qualifica e captura o lead — sem você fazer manual.

### O que entra
- Subir o **OpenWA** (NestJS/Docker) localmente → depois em hosting.
- Webhook: mensagem recebida → Javis decide resposta.
- Fluxo de auto-resposta por palavra-chave (PISCINAS, COMBO, MARÉ, LITORAL — as mesmas dos posts).
- Captura de lead (nome + data da viagem) num arquivo/planilha.

### ⚠️ Risco que você PRECISA decidir antes (sou obrigado a alertar)
O OpenWA usa WhatsApp **não-oficial** (automação do WhatsApp Web). **Risco real de banir o número.** Dois caminhos:
- **A) OpenWA (não-oficial):** grátis, rápido de subir, mas pode tomar ban → use um **número secundário**, nunca o principal do negócio.
- **B) WhatsApp Business Cloud API (Meta, oficial):** não bane, mas exige cadastro Meta, número dedicado e tem custo por conversa.
- **Recomendação:** começar com **A em número secundário** pra validar o fluxo barato; migrar pra B quando o volume justificar.

### Infra / custo
- Docker (✅ já tem) · número WhatsApp secundário · hosting (VPS ~R$30–50/mês) quando sair do localhost.

### Entregável testável
Mando "PISCINAS" pro número de teste → recebo resposta automática certa → lead aparece no arquivo.

### Pergunta aberta
1. Tem um número secundário pra dedicar ao bot? (não usar o principal)

---

## 🥈 FASE 2 — Higgsfield + facelift do site
**Objetivo:** gastar os créditos do Higgsfield (perecíveis) gerando vídeos cinematográficos dos passeios e deixar o `vempassearjampa.com` mais moderno/tech.

### O que entra
- Selecionar 3–5 fotos fortes (catamarã, piscinas, pôr do sol) → Higgsfield image-to-video (presets de câmera aérea/zoom).
- Hero do site com vídeo de fundo + CTA WhatsApp (amarra com a Fase 1).
- Padronizar visual (mesma identidade dos criativos: cyan/dourado, Montserrat).

### ⚠️ Bloqueio técnico a resolver primeiro
Não achei o site no projeto local. Preciso saber **onde/como o `vempassearjampa.com` é feito** (Wix? Webflow? WordPress? código próprio?). Isso define se eu consigo editar direto ou se entrego os vídeos/assets pra você subir.

### Infra / custo
- Créditos Higgsfield (✅ já tem) · acesso/credenciais do site.

### Entregável testável
Site abre com vídeo cinematográfico no topo + botão "PISCINAS no WhatsApp" funcionando.

### Perguntas abertas
2. O `vempassearjampa.com` é feito em quê? Tenho acesso de edição?
3. Quantos créditos Higgsfield você tem hoje (pra dimensionar quantos vídeos)?

---

## 🥉 FASE 3 — Javis que aprende sozinho (estruturar agora, construir depois)
**Objetivo:** Javis vira um sistema que se aprimora — junta estudos/ideias, resume, e fica mais inteligente com o tempo.

### Arquitetura proposta (só desenho, sem build agora)
- **Pasta `_ideias/` e `_estudos/`** → você despeja ideias/links/PDFs.
- **Rotina ociosa:** quando o Javis não está em tarefa, ele processa essa pasta (resume, indexa, cataloga).
- **NotebookLM:** você joga material lá, ele resume; a gente puxa o resumo de volta pra base de conhecimento (`_memoria/`).
- **Seção de treinamento na interface:** view dedicada no javis-local-interface pra ver o que ele aprendeu.
- Reaproveita o que já existe: `_memoria/`, LeanCTX, os agentes em `_apps/javis-local-interface/backend/agents/`.

### Por que por último
Maior escopo e risco, e depende das Fases 1–2 estarem rodando pra valer a pena. Estruturado aqui pra não perder a visão.

### Perguntas abertas
4. NotebookLM tem API/automação ou seria manual (você cola o resumo)? (hoje é majoritariamente manual)

---

## 📋 Resumo das perguntas que destravam o build
| # | Pergunta | Trava qual fase |
|---|----------|-----------------|
| 1 | Número secundário pro bot WhatsApp? | Fase 1 |
| 2 | Site é feito em quê + tenho acesso? | Fase 2 |
| 3 | Quantos créditos Higgsfield? | Fase 2 |
| 4 | NotebookLM: API ou manual? | Fase 3 |

## ▶️ Próximo passo
Você revisa este roadmap, responde as 4 perguntas (ou as que souber) e diz **"aprovado, começa pela Fase 1"** (ou a que preferir). Aí eu construo só aquela fase, te mostro, e você comita.
