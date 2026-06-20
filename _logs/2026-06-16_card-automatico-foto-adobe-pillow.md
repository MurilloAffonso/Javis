# Decisão: Pipeline automático de card sobre foto (Adobe + Pillow)

**Data:** 2026-06-16

## O que foi decidido
Pipeline 100% automático pra transformar foto da pasta `_FOTOS-AQUI` em post pronto, sem passo manual:
1. Upload da foto local pro Adobe via upload programático (init→PUT→finalize) — contorna o seletor `asset_add_file` que NÃO renderiza no modo remoto (/rc).
2. Adobe processa: `image_generative_expand` (céu/mar p/ 4:5) + `image_apply_auto_tone` + `image_crop_and_resize` (1080x1350).
3. `gerar_card_foto.py` (Pillow) carimba headline/subline/CTA sobre a foto, mantendo identidade visual (Montserrat ExtraBold + Inter, cyan #00d4ff / dourado).

## Por quê
Murillo pediu automação total — entregar o criativo completo (card + estratégia) sem ele tocar em nada. As ferramentas Adobe processam foto muito bem mas não têm "texto sobre minha foto"; o overlay fica no Pillow, sobre o asset já tratado pelo Adobe (respeita o pipeline foto→plugin→criativo).

## Alternativas consideradas
- Express templates: usariam fundo próprio, não a foto do cliente. Descartado.
- Seletor `asset_add_file`: trava no modo remoto. Descartado p/ upload.
- InDesign layout: exigiria doc-fonte, mais frágil. Descartado.

## Próximo passo
- Acentos no tag pill ("JOÃO") — cosmético, opcional.
- Generalizar `gerar_card_foto.py` p/ aceitar headline/CTA por parâmetro e virar gerador diário.
