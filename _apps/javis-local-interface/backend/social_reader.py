"""social_reader.py — lê redes sociais e fóruns sem API paga.

Reddit: API JSON pública (reddit.com/search.json)
YouTube: yt-dlp search (metadata, sem baixar)
"""
from __future__ import annotations
import requests

_UA = {"User-Agent": "Mozilla/5.0 (compatible; Javis/2.0; Python/requests)"}
_TIMEOUT = 15


def pesquisar_reddit(query: str, limite: int = 6) -> dict:
    """Busca no Reddit via DuckDuckGo — Reddit bloqueia acesso direto sem OAuth."""
    try:
        from ddgs import DDGS
        resultados = list(DDGS().text(f"reddit {query}", max_results=limite))
        reddit_res = [r for r in resultados if "reddit.com" in r.get("href", "")]
        if not reddit_res:
            # fallback: qualquer resultado relacionado
            reddit_res = resultados

        linhas = [f"Reddit — '{query}':\n"]
        for i, r in enumerate(reddit_res, 1):
            titulo = r.get("title", "")
            corpo = r.get("body", "")
            url = r.get("href", "")
            linhas.append(f"{i}. {titulo}")
            if corpo and "hides" not in corpo:
                linhas.append(f"   {corpo[:200]}")
            linhas.append(f"   {url}")
        return {"status": "ok", "message": "\n".join(linhas)}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao pesquisar Reddit: {e}"}


def pesquisar_youtube(query: str, limite: int = 5) -> dict:
    try:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limite}:{query}", download=False)

        entries = (info or {}).get("entries", [])
        if not entries:
            return {"status": "ok", "message": f"Nenhum vídeo para '{query}'."}

        linhas = [f"YouTube — '{query}':\n"]
        for i, v in enumerate(entries, 1):
            dur = int(v.get("duration") or 0)
            dur_str = f"{dur//60}:{dur%60:02d}" if dur else "—"
            views = int(v.get("view_count") or 0)
            linhas.append(f"{i}. {v.get('title','—')} [{dur_str}]")
            linhas.append(f"   Canal: {v.get('uploader','—')} · {views:,} views")
        return {"status": "ok", "message": "\n".join(linhas)}
    except ImportError:
        return {"status": "error", "message": "yt-dlp não instalado."}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao pesquisar YouTube: {e}"}


def pesquisar_redes(query: str) -> dict:
    """Pesquisa Reddit + YouTube e retorna resultado combinado."""
    partes = []

    reddit = pesquisar_reddit(query)
    if reddit["status"] == "ok":
        partes.append(reddit["message"])

    yt = pesquisar_youtube(query)
    if yt["status"] == "ok":
        partes.append(yt["message"])

    if not partes:
        return {"status": "error", "message": "Não consegui buscar em nenhuma rede."}

    return {"status": "ok", "message": "\n\n---\n\n".join(partes)}
