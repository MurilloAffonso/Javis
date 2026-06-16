# browser.py — busca web e leitura de páginas
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
_HEADERS = {"User-Agent": _UA, "Accept-Language": "pt-BR,pt;q=0.9"}


def _clean(text: str, limit: int = 2500) -> str:
    return re.sub(r'\s+', ' ', text or "").strip()[:limit]


def search_google(query: str) -> dict:
    """Pesquisa na web via DuckDuckGo (sem CAPTCHA) e devolve os top resultados."""
    try:
        from ddgs import DDGS
        raw = list(DDGS().text(query, max_results=6))
        if not raw:
            return {"status": "ok", "message": f"Não encontrei resultados para '{query}', senhor."}

        results = [{"title": r.get("title",""), "snippet": r.get("body",""), "url": r.get("href","")} for r in raw]
        lines = []
        for i, r in enumerate(results[:5], 1):
            lines.append(f"{i}. {r['title']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet'][:180]}")

        return {
            "status": "ok",
            "message": f"Pesquisei '{query}'. Resultados:\n" + "\n".join(lines),
            "results": results,
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro ao pesquisar: {e}"}


def read_page(url: str) -> dict:
    """Lê o conteúdo principal de uma página web."""
    try:
        if not url.startswith("http"):
            url = "https://" + url

        if _HAS_PLAYWRIGHT:
            return _read_playwright(url)

        # Fallback: requests simples
        resp = requests.get(url, headers=_HEADERS, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = _clean(soup.get_text(separator=" "))
        return {"status": "ok", "message": text, "url": url}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao ler página: {e}"}


def _read_playwright(url: str) -> dict:
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(headless=True)
            ctx = b.new_context(user_agent=_UA)
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_load_state("networkidle", timeout=6000)
            except PWTimeout:
                pass
            page.evaluate("""() => {
                ['script','style','nav','footer','header','aside','noscript']
                    .forEach(t => document.querySelectorAll(t).forEach(e => e.remove()));
            }""")
            content = page.evaluate("() => document.body ? document.body.innerText : ''")
            b.close()
        return {"status": "ok", "message": _clean(content), "url": url}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao ler página: {e}"}


def navigate_visible(url: str) -> dict:
    """Abre uma URL no navegador padrão (visível para o senhor)."""
    try:
        import webbrowser
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return {"status": "ok", "message": f"Aberto no navegador: {url}"}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao abrir: {e}"}
