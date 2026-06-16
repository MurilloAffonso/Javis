"""Site Analyzer — busca uma URL, extrai a estrutura e gera código similar.

Fluxo:
  url → fetch HTML → extrai título/meta/headings/estrutura → Claude analisa
      → devolve análise + esqueleto de código HTML/CSS recriando o layout.

Não clona conteúdo protegido — recria a *estrutura* visual/semântica em código novo.
"""
from __future__ import annotations
import re
import requests

_UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_TIMEOUT = 15

# Sites conhecidos do senhor — citados por nome, sem precisar da URL.
# Casa por substring (sem acento) no texto falado/digitado.
KNOWN_SITES: dict[str, str] = {
    "vem passear": "https://vempassearjampa.com",
    "vempassear": "https://vempassearjampa.com",
}


def _known_site(text: str) -> str | None:
    """Resolve o site pelo nome próprio (ex.: 'analisa meu site Vem Passear')."""
    import unicodedata
    t = unicodedata.normalize("NFKD", (text or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    for alias, url in KNOWN_SITES.items():
        if alias in t:
            return url
    return None


def _extract_url(text: str) -> str | None:
    """Acha uma URL no texto falado/digitado."""
    # Nome próprio conhecido (ex.: "Vem Passear") tem prioridade MÁXIMA — mesmo que
    # o modelo passe uma URL com TLD errado (https://...com.br que não resolve),
    # usamos a canônica que funciona.
    known = _known_site(text)
    if known:
        return known
    m = re.search(r"https?://[^\s]+", text)
    if m:
        return m.group(0).rstrip(".,;)")
    # fala: "analisa o site exemplo.com" → tenta domínio solto
    m = re.search(r"\b([a-z0-9-]+\.(?:com|com\.br|net|org|io|dev|app|gov|edu)(?:\.[a-z]{2})?)\b", text, re.I)
    if m:
        return "https://" + m.group(1)
    return None


def _strip(html: str, tag: str) -> list[str]:
    return re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.I | re.S)


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fetch_structure(url: str) -> dict:
    """Baixa o HTML e extrai um resumo estrutural leve (sem despejar a página toda)."""
    resp = requests.get(url, headers=_UA, timeout=_TIMEOUT)
    resp.raise_for_status()
    html = resp.text

    title = (_strip(html, "title") or [""])[0]
    title = _clean(title)

    metas = re.findall(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I)
    description = metas[0] if metas else ""

    headings = []
    for level in ("h1", "h2", "h3"):
        for h in _strip(html, level)[:8]:
            txt = _clean(h)
            if txt:
                headings.append(f"{level}: {txt}")

    # contagens estruturais
    counts = {
        "links":   len(re.findall(r"<a\b", html, re.I)),
        "imgs":    len(re.findall(r"<img\b", html, re.I)),
        "forms":   len(re.findall(r"<form\b", html, re.I)),
        "buttons": len(re.findall(r"<button\b", html, re.I)),
        "sections":len(re.findall(r"<section\b", html, re.I)),
        "navs":    len(re.findall(r"<nav\b", html, re.I)),
    }

    # nav links (rótulos dos menus)
    nav_labels = []
    for nav in _strip(html, "nav")[:2]:
        for a in _strip(nav, "a")[:10]:
            lbl = _clean(a)
            if lbl:
                nav_labels.append(lbl)

    return {
        "url": url,
        "title": title,
        "description": description,
        "headings": headings[:20],
        "counts": counts,
        "nav": nav_labels[:12],
        "bytes": len(html),
    }


def analyze(text_or_url: str, generate_code: bool = True) -> dict:
    """Analisa um site a partir de texto/URL e retorna análise + código (opcional)."""
    url = _extract_url(text_or_url)
    if not url:
        return {"status": "error", "message": "Não achei uma URL. Diga algo como: analisa o site exemplo.com"}

    try:
        struct = fetch_structure(url)
    except Exception as e:
        return {"status": "error", "message": f"Não consegui acessar {url}: {e}"}

    from llm_providers import call_claude

    struct_summary = (
        f"URL: {struct['url']}\n"
        f"Título: {struct['title']}\n"
        f"Descrição: {struct['description']}\n"
        f"Menu: {', '.join(struct['nav']) or '—'}\n"
        f"Headings:\n" + "\n".join("  " + h for h in struct['headings']) + "\n"
        f"Elementos: {struct['counts']}\n"
    )

    instruction = (
        "Você é o Javis analisando um site para Murillo.\n"
        "Com base no resumo estrutural abaixo:\n"
        "1. Descreva em 3-4 linhas o que o site é e como está organizado.\n"
    )
    if generate_code:
        instruction += (
            "2. Gere um esqueleto HTML+CSS NOVO (código próprio, não copiado) que "
            "recria um layout SEMELHANTE — mesma estrutura de seções/menu/hero, "
            "com placeholders no conteúdo. Use um só arquivo HTML com <style> embutido. "
            "Responda em português; coloque o código num bloco ```html.\n"
        )
    else:
        instruction += "2. Liste 3 pontos fortes e 3 pontos a melhorar no layout.\n"

    analysis = call_claude([
        {"role": "system", "content": instruction},
        {"role": "user",   "content": struct_summary},
    ], temperature=0.4)

    return {
        "status": "ok",
        "url": url,
        "structure": struct,
        "message": analysis,
    }
