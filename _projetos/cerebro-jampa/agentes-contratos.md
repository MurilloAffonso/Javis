# Contratos dos Agentes — Vem Passear Jampa

> Padrão adotado do board "Encontro 1" (ver `_outbox/estudo-board-encontro1.md`):
> cada agente é uma **tarefa atômica** com **Input → Output**, **fronteira clara**
> (O que faz / Não faz) e **Ferramentas**. Adaptado da operação de infoproduto do
> board pra realidade da Vem Passear: turismo/serviço local, conversão por
> **WhatsApp** (não sales page/checkout), produto = passeio.
>
> **Revisão 20/06 (decisões do Murillo):** operação enxuta → **5 agentes**
> (consolidados, não os 7 iniciais); WhatsApp **prepara o rascunho, o Murillo
> envia** (não responde sozinho); Olheiro **mantido leve** (só inspiração, sem
> copiar concorrente).
>
> Alinhado com a `linha-editorial.md` (papéis Nova/Midas/Murillo), o `Fluxo VP`
> da interface e a missão "Pipeline Marketing" do Quadro. Regra de ouro:
> **nada de agente que faz tudo; cada um entrega pro próximo e respeita o "Não faz".**

Esteira geral (5 agentes):
```
OLHEIRO → NOVA (conteúdo) → ESTÚDIO (arte) → MIDAS (distribui + WhatsApp) → ANALISTA (dados)
 (o que    (pauta + copy)    (carrossel/Reel)  (publica/impulsiona/rascunho)   (o que deu certo)
  cola)
```
Humano no topo: **Murillo** aprova oferta, maré/vaga, preço, uso de imagem (os Gates)
e **dá o envio final** das respostas de WhatsApp.

---

## 1) OLHEIRO · inteligência (leve)
- **Input:** semana atual + pilares da linha editorial
- **Output:** 3-5 referências/tendências da semana (formatos, áudios, ganchos) → entrega pra Nova
- **O que faz:** capta trends/áudios de turismo que estão bombando · aponta formatos que estão performando · traz inspiração (não cópia)
- **Não faz:** copiar concorrente · criar conteúdo da marca · publicar · responder cliente
- **Ferramentas:** Instagram/TikTok (busca), `pesquisar_redes` do Javis
- **Nota:** mantido LEVE de propósito — a linha editorial evita "cara de agência genérica"; ele serve de fagulha, a voz é sempre própria da Vem Passear.

---

## 2) NOVA · conteúdo (pauta + copy)
*Diretora criativa — junta o planejamento e a escrita num agente só.*
- **Input:** briefing do Murillo (maré, agenda de saídas, vagas, fotos novas) + referências do Olheiro
- **Output:** `posts/pauta-semana.md` completo — 3+ posts com dia, pilar, formato, gancho, **legenda final + CTA + hashtags** e material visual necessário
- **O que faz:** escolhe os pilares da semana (proporção da linha editorial, máx. 2 de venda a cada 10) · cria gancho 3s e formato · escreve a copy no tom caloroso/local · usa os CTAs padrão (MARÉ/COMBO/SEIXAS)
- **Não faz:** produzir a arte · publicar · inventar preço/horário/maré · prometer vaga sem o Murillo confirmar
- **Ferramentas:** `linha-editorial.md` (pilares, banco de 30 ideias, estrutura de legenda/hashtags), Claude (assinatura)
- **Gate depois dela:** Murillo aprova a pauta+copy (Gate 1)

---

## 3) ESTÚDIO · criativos
- **Input:** pauta aprovada + copy + fotos de `imagens/_FOTOS-AQUI/`
- **Output:** peças prontas em `outputs/` (carrossel/card/Reel)
- **O que faz:** gera as artes (`gerar_carrossel.py`/Canva/Claude Design) · adapta por formato · aplica a identidade visual da marca
- **Não faz:** definir verba · publicar · alterar a copy aprovada
- **Ferramentas:** `gerar_carrossel.py`, `gerar_card_foto.py`, Canva, Claude Design
- **Conferência depois dele:** consistência de marca (Design System) antes de avançar

---

## 4) MIDAS · distribuição & conversão (inclui WhatsApp)
*Tráfego e conversão — publica, impulsiona e PREPARA o atendimento (você envia).*
- **Input:** peças + copy finais aprovadas (Gate 2) · e mensagens recebidas no WhatsApp
- **Output:** posts publicados/agendados + marcação do que impulsionar + **rascunhos de resposta de WhatsApp prontos pro Murillo enviar**
- **O que faz:** agenda/publica nos canais · marca posts com potencial de anúncio e sugere segmentação · monta a resposta do WhatsApp usando os templates (primeiro contato, maré/horário, preço, reserva, pós-passeio)
- **Não faz:** **enviar a resposta sozinho** (o Murillo dá o envio final) · inventar disponibilidade/preço (confirma com o Murillo) · aprovar verba sozinho · criar arte/copy
- **Ferramentas:** Meta Business Suite, Meta Ads, `posts/templates-whatsapp.md`, WhatsApp
- **Regra de segurança:** toda resposta com preço, maré, vaga ou data vai como RASCUNHO pro Murillo conferir antes de enviar.

---

## 5) ANALISTA · resultado (dados)
*A lacuna que o board nos mostrou — hoje manual, candidato nº 1 a automatizar.*
- **Input:** métricas da semana (alcance, salvamentos, cliques no WhatsApp, reservas)
- **Output:** decisão da semana (o que repetir, o que cortar) registrada em `pauta-semana.md` → vira o briefing da semana seguinte
- **O que faz:** lê o desempenho de cada post · aponta os 3 que mais geraram WhatsApp/reserva · recomenda o que a Nova deve repetir/variar
- **Não faz:** inventar número · publicar · decidir a estratégia sozinho (entrega pro Murillo decidir)
- **Ferramentas:** Instagram Insights, planilha simples, Claude

---

## Como isso amarra tudo

| Camada | Onde vive | Status |
|---|---|---|
| Visual (raias) | view **Fluxo VP** na interface | ✅ feito |
| Tarefas (kanban) | missão **Pipeline Marketing** no Quadro | ✅ Raia 1 rodada |
| **Contratos (este arquivo)** | `agentes-contratos.md` | ✅ revisado (5 agentes) |
| Personas no backend | `agents/specialized.py` (genéricas de software) | ⚠️ ainda não refletem Nova/Midas/etc. |

**Próximo passo possível:** transformar estes 5 contratos em personas reais no backend
(cada agente com seu Input/Output/Não faz no system prompt), pra orquestração de
verdade chamar "Nova", "Estúdio", "Midas" etc. — e a interface mostrar exatamente
quem faz o quê.
