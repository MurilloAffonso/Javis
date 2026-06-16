# Template: Carrossel Diário Instagram — Vem Passear Jampa
# Fonte: Modelo_Tarefa_Carrossel.docx (adaptado)

## CONFIGURAÇÕES FIXAS (não alterar)

- **Nicho:** TURISMO LOCAL — João Pessoa/PB — piscinas naturais, passeios de barco, litoral norte
- **Horário da task:** 07:00 (antes do pico de busca de turistas)
- **Instagram:** @vempassearjampa
- **WhatsApp CTA:** wa.me/5583XXXXXXXX (completar com número real)
- **Proporção:** 4:5 vertical (1080x1350px)
- **Cards por carrossel:** 7 (capa + 5 conteúdo + CTA)

## PALETA DE CORES (identidade Vem Passear)

- Fundo: `#0a1628` (azul profundo do mar)
- Acento primário: `#00d4ff` (azul turquesa das piscinas)
- Acento secundário: `#f59e0b` (dourado do pôr do sol)
- Texto principal: `#ffffff`
- Texto secundário: `#94a3b8`

## TIPOGRAFIA

- Títulos: Montserrat ExtraBold (Google Fonts) — impacto e modernidade
- Corpo: Inter Regular — legibilidade
- Fallback: Arial Bold (avisar se não carregar a fonte premium)

## SUBTEMAS ROTATIVOS (variar a cada dia, nunca repetir 2 dias seguidos)

1. Piscinas naturais do Seixas (horários, maré, o que ver)
2. Piscinas do Picãozinho (travessia, peixinhos, família)
3. Litoral Norte (praias, surf, Barra do Camaratuba)
4. Combo Duplo (Seixas + Picãozinho no mesmo dia)
5. Dicas práticas (o que levar, roupa, crianças, câmera)
6. Bastidores (equipe, barco, guia, madrugada)
7. Prova social (depoimento adaptado, avaliação, foto de cliente)

## ROTAÇÃO DE ABORDAGENS (nunca repetir o mesmo formato 2 dias seguidos)

1. **TENDÊNCIA** — conectar com algo em alta no turismo/João Pessoa agora
   - Ex: "Alta temporada chegando — como garantir sua vaga nas piscinas"
   - Ex: "João Pessoa apareceu no [ranking/matéria recente] — e os passeios?"

2. **TUTORIAL** — passo a passo que entrega valor imediato
   - Ex: "Como escolher o melhor horário para as piscinas naturais em 3 passos"
   - Ex: "O que fazer nos 2 primeiros dias em João Pessoa (do zero)"

3. **CURIOSIDADE** — fato pouco conhecido, dado concreto, história local
   - Ex: "Por que as piscinas naturais só existem em João Pessoa?"
   - Ex: "A maré que formou as piscinas leva [X] anos para acontecer"

## ESTRUTURA DOS CARDS

- **Card 1 (CAPA):** Gancho forte + título grande + subtítulo de apoio + cor de acento no destaque
- **Cards 2–6 (CONTEÚDO):** Número do tópico em acento, título, parágrafo 3-4 linhas, 3 bullets
- **Card 7 (CTA):** Frase de virada + botão preenchido (CTA rotativo: "MANDA 'MARÉ' NO WHATS" / "RESERVE SEU PASSEIO" / "FALA COM A GENTE")
- **Rodapé em todos:** `@vempassearjampa`

## REGRAS DE CONTEÚDO (da linha-editorial.md)

- Tom: local, caloroso, direto — "vem com a gente", "olha esse mar"
- Nunca prometer "água cristalina todos os dias" — depende da maré
- Pelo menos 1 dado concreto (preço real, distância, horário)
- Frases curtas, densidade > volume
- Urgência real: vagas limitadas, maré boa, alta temporada
- Hashtags (sempre no legenda.txt): misturar local + nicho + trending

## ENTREGÁVEL (por execução)

```
outputs/carrossel-vempassear-AAAA-MM-DD/
  card_01.png
  card_02.png
  card_03.png
  card_04.png
  card_05.png
  card_06.png
  card_07.png
  legenda.txt
  meta.json  (abordagem, subtema, fontes da pesquisa de tendência)
```

## TÉCNICO

- Python 3 + Pillow 12.x (já instalado)
- Baixar fontes: Montserrat ExtraBold + Inter Regular do Google Fonts
- Salvar fontes em: `_projetos/cerebro-jampa/assets/fonts/`
- Se fonte não carregar: avisar no terminal e usar Arial Bold
- Script principal: `_projetos/cerebro-jampa/gerar_carrossel.py`
- Executar: `python _projetos/cerebro-jampa/gerar_carrossel.py`

## LEGENDA (legenda.txt)

3–5 linhas instigantes sobre o tema do dia
Pergunta no final para estimular comentário
5–8 hashtags específicas de João Pessoa + turismo
CTA para WhatsApp no final

---
Referência: linha-editorial.md | seo-plano.md | Modelo_Tarefa_Carrossel.docx
