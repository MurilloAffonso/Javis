from __future__ import annotations

"""Carimba o texto de um post (headline + subline + CTA) sobre uma foto ja
processada (ex.: saida do Adobe). Mantem a identidade visual da Vem Passear.

Uso:
    python gerar_card_foto.py <foto_entrada.png> <card_saida.png>
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
FONT_DIR = BASE_DIR / "assets" / "fonts"
EMOJI_FONT = "C:/Windows/Fonts/seguiemj.ttf"

WIDTH = 1080
HEIGHT = 1350
MARGIN = 80
SOCIAL = "@vempassearjampa"

COLORS = {
    "accent": "#00d4ff",
    "gold": "#fbbf24",
    "text": "#ffffff",
    "muted": "#dbeafe",
    "dark": "#0a1628",
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def apply_variation(font: ImageFont.FreeTypeFont, weight: int) -> None:
    try:
        axes = font.get_variation_axes()
    except Exception:
        return
    values: list[int] = []
    for axis in axes:
        raw = axis.get("name", b"")
        name = raw.decode("utf-8", "ignore").lower() if isinstance(raw, bytes) else str(raw).lower()
        default_value = int(axis.get("default", weight))
        min_value = int(axis.get("minimum", default_value))
        max_value = int(axis.get("maximum", default_value))
        if "weight" in name or "wght" in name:
            values.append(max(min(weight, max_value), min_value))
        else:
            values.append(default_value)
    try:
        font.set_variation_by_axes(values)
    except Exception:
        return


def font(file_name: str, size: int, weight: int = 400) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / file_name
    loaded = ImageFont.truetype(str(path), size=size)
    apply_variation(loaded, weight)
    return loaded


def emoji_font(size: int) -> ImageFont.FreeTypeFont | None:
    try:
        return ImageFont.truetype(EMOJI_FONT, size=size)
    except Exception:
        return None


def text_w(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=f)
    return bbox[2] - bbox[0]


def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            cand = f"{current} {word}"
            if text_w(draw, cand, f) <= max_w:
                current = cand
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def fit_font(draw, text, file_name, start, low, max_w, max_lines, weight=800):
    for size in range(start, low - 1, -2):
        cand = font(file_name, size, weight=weight)
        if len(wrap(draw, text, cand, max_w)) <= max_lines:
            return cand
    return font(file_name, low, weight=weight)


def gradient_scrim(img: Image.Image, top: bool, height: int, max_alpha: int) -> None:
    """Aplica um degrade preto translucido (topo ou base) para legibilidade."""
    overlay = Image.new("RGBA", (WIDTH, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(height):
        frac = (height - i) / height if top else i / height
        alpha = int(max_alpha * (frac ** 1.6))
        od.line((0, i, WIDTH, i), fill=(6, 14, 28, alpha))
    y = 0 if top else HEIGHT - height
    base = img.convert("RGBA")
    base.alpha_composite(overlay, (0, y))
    img.paste(base.convert("RGB"))


def draw_tag(draw: ImageDraw.ImageDraw, text: str, cx: int, y: int) -> int:
    f = font("Montserrat-ExtraBold.ttf", 26, weight=700)
    tw = text_w(draw, text, f)
    pad_x, pad_y = 26, 14
    x0 = cx - (tw + pad_x * 2) // 2
    draw.rounded_rectangle(
        (x0, y, x0 + tw + pad_x * 2, y + 40 + pad_y),
        radius=24,
        fill=(10, 22, 41, 220),
        outline=COLORS["accent"],
        width=3,
    )
    draw.text((x0 + pad_x, y + pad_y - 2), text, font=f, fill=COLORS["accent"])
    return y + 40 + pad_y


def draw_centered_lines(draw, lines, f, y, fill, line_gap, stroke=0, stroke_fill=None):
    asc, desc = f.getmetrics()
    lh = asc + desc + line_gap
    for line in lines:
        tw = text_w(draw, line, f)
        x = WIDTH // 2 - tw // 2
        draw.text(
            (x, y), line, font=f, fill=fill,
            stroke_width=stroke, stroke_fill=stroke_fill,
        )
        y += lh
    return y


def build(input_path: Path, output_path: Path) -> None:
    img = Image.open(input_path).convert("RGB")
    if img.size != (WIDTH, HEIGHT):
        img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)

    # Scrims para legibilidade
    gradient_scrim(img, top=True, height=560, max_alpha=190)
    gradient_scrim(img, top=False, height=440, max_alpha=210)

    draw = ImageDraw.Draw(img)
    max_w = WIDTH - MARGIN * 2

    # --- TOPO: tag + headline + subline ---
    y = 66
    y = draw_tag(draw, "PISCINAS NATURAIS · JOAO PESSOA/PB", WIDTH // 2, y)
    y += 40

    headline = "A PARAÍBA TEM UM SEGREDO"
    hf = fit_font(draw, headline, "Montserrat-ExtraBold.ttf", 104, 64, max_w, 2, weight=800)
    hlines = wrap(draw, headline, hf, max_w)
    y = draw_centered_lines(
        draw, hlines, hf, y, COLORS["gold"], line_gap=4,
        stroke=3, stroke_fill=(6, 14, 28, 255),
    )
    y += 18

    sub = "e ele é azul-turquesa"
    sf = font("Montserrat-ExtraBold.ttf", 50, weight=600)
    sw = text_w(draw, sub, sf)
    emoji_px = 80
    ef = emoji_font(emoji_px)
    emoji_w = emoji_px if ef else 0
    total = sw + (20 + emoji_w if ef else 0)
    sx = WIDTH // 2 - total // 2
    s_asc, s_desc = sf.getmetrics()
    draw.text((sx, y), sub, font=sf, fill=COLORS["text"],
              stroke_width=2, stroke_fill=(6, 14, 28, 255))
    if ef:
        try:
            line_center = y + (s_asc + s_desc) // 2
            draw.text((sx + sw + 20, line_center - emoji_px // 2),
                      "\U0001F420", font=ef, embedded_color=True)
        except Exception:
            pass

    # --- BASE: CTA badge + handle ---
    cta = "Manda  PISCINAS  no WhatsApp"
    cf = fit_font(draw, cta, "Montserrat-ExtraBold.ttf", 44, 30, max_w - 120, 1, weight=800)
    cw = text_w(draw, cta, cf)
    badge_w = cw + 120
    badge_h = 96
    bx = WIDTH // 2 - badge_w // 2
    by = HEIGHT - 250
    draw.rounded_rectangle((bx, by, bx + badge_w, by + badge_h), radius=48,
                           fill=hex_to_rgb(COLORS["accent"]))
    cyf = cf.getmetrics()
    draw.text((WIDTH // 2 - cw // 2, by + (badge_h - (cyf[0] + cyf[1])) // 2),
              cta, font=cf, fill=hex_to_rgb(COLORS["dark"]))

    hf2 = font("Inter-Regular.ttf", 34, weight=500)
    hw = text_w(draw, SOCIAL, hf2)
    draw.text((WIDTH // 2 - hw // 2, by + badge_h + 30), SOCIAL,
              font=hf2, fill=COLORS["text"],
              stroke_width=2, stroke_fill=(6, 14, 28, 255))

    img.save(output_path, quality=95)
    print(f"Card gerado: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("uso: python gerar_card_foto.py <foto_entrada> <card_saida>")
        sys.exit(1)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
