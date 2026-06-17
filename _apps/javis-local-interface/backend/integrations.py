"""Integrations — conectores de APIs externas (YouTube, Google, etc.).

Cada função degrada com elegância: se a API key não estiver no .env,
retorna None e o chamador usa o fallback (busca por página, etc.).
"""
from __future__ import annotations
import os
import requests

_TIMEOUT = 10


def youtube_search_id(query: str) -> str | None:
    """Busca no YouTube e retorna o videoId do 1º resultado (ou None se sem key/erro)."""
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key or not query.strip():
        return None
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 1,
                "videoEmbeddable": "true",
                "key": api_key,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return None
        return items[0]["id"]["videoId"]
    except Exception:
        return None


def youtube_watch_url(query: str) -> str | None:
    """Retorna a URL de assistir (autoplay) do vídeo encontrado, ou None."""
    vid = youtube_search_id(query)
    if vid:
        return f"https://www.youtube.com/watch?v={vid}"
    return None


def youtube_search_many(query: str, max_results: int = 5) -> list[dict]:
    """Busca vários vídeos (título, canal, url, data). Lista vazia se sem key/erro."""
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key or not query.strip():
        return []
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "order": "relevance",
                "maxResults": max_results,
                "videoEmbeddable": "true",
                "key": api_key,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        out = []
        for it in resp.json().get("items", []):
            vid = it.get("id", {}).get("videoId")
            sn = it.get("snippet", {})
            if not vid:
                continue
            out.append({
                "title": sn.get("title", ""),
                "channel": sn.get("channelTitle", ""),
                "published": (sn.get("publishedAt") or "")[:10],
                "url": f"https://www.youtube.com/watch?v={vid}",
            })
        return out
    except Exception:
        return []


def youtube_transcript(video_url_or_id: str, langs: tuple[str, ...] = ("pt", "pt-BR", "en")) -> str | None:
    """Busca a transcrição real de um vídeo do YouTube (sem precisar de API key).

    Retorna o texto completo da legenda, ou None se o vídeo não tiver
    legenda disponível nesses idiomas ou a busca falhar.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None
    video_id = video_url_or_id
    if "watch?v=" in video_url_or_id:
        video_id = video_url_or_id.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url_or_id:
        video_id = video_url_or_id.split("youtu.be/")[-1].split("?")[0]
    try:
        api = YouTubeTranscriptApi()
        snippets = api.fetch(video_id, languages=list(langs))
        return " ".join(s.text for s in snippets).strip() or None
    except Exception:
        return None


def github_search_repos(query: str, max_results: int = 5) -> list[dict]:
    """Busca repositórios no GitHub (API pública, sem token — sujeita a rate limit baixo)."""
    if not query.strip():
        return []
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": max_results},
            headers={"Accept": "application/vnd.github+json"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        out = []
        for it in resp.json().get("items", []):
            out.append({
                "title": it.get("full_name", ""),
                "channel": f"⭐ {it.get('stargazers_count', 0)}",
                "published": (it.get("pushed_at") or "")[:10],
                "url": it.get("html_url", ""),
                "description": it.get("description") or "",
            })
        return out
    except Exception:
        return []


def weather(city: str = "") -> dict | None:
    """Clima atual via OpenWeather. Retorna dict resumido ou None (sem key/erro)."""
    api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        return None
    city = (city or os.environ.get("JAMBA_CITY", "João Pessoa,BR")).strip()
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric", "lang": "pt_br"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        d = resp.json()
        return {
            "city":  d.get("name", city),
            "temp":  round(d["main"]["temp"]),
            "feels": round(d["main"]["feels_like"]),
            "desc":  d["weather"][0]["description"],
            "humidity": d["main"]["humidity"],
            "wind":  round(d.get("wind", {}).get("speed", 0) * 3.6),  # m/s → km/h
        }
    except Exception:
        return None


def whatsapp_send(numero: str, mensagem: str = "") -> dict:
    """Abre o WhatsApp com a mensagem pronta para um número (wa.me — grátis, nativo).

    numero: só dígitos com DDI (ex.: 5583999998888). Vazio = abre o WhatsApp sem destino.
    """
    import webbrowser
    import urllib.parse
    num = "".join(c for c in (numero or "") if c.isdigit())
    msg = urllib.parse.quote((mensagem or "").strip())
    if num:
        url = f"https://wa.me/{num}" + (f"?text={msg}" if msg else "")
        webbrowser.open(url)
        return {"status": "ok", "message": f"Abrindo WhatsApp para {num}, senhor — é só confirmar o envio."}
    # sem número → abre o WhatsApp Web
    webbrowser.open("https://web.whatsapp.com")
    return {"status": "ok", "message": "Abrindo o WhatsApp, senhor."}


def available() -> dict:
    """Diz quais integrações estão configuradas (key presente no .env)."""
    def has(k: str) -> bool:
        return bool(os.environ.get(k, "").strip())
    return {
        "youtube":    has("YOUTUBE_API_KEY"),
        "google":     has("GOOGLE_API_KEY"),
        "canva":      has("CANVA_API_KEY"),
        "spotify":    has("SPOTIFY_CLIENT_ID") and has("SPOTIFY_CLIENT_SECRET"),
        "openweather":has("OPENWEATHER_API_KEY"),
        "telegram":   has("TELEGRAM_BOT_TOKEN"),
        "elevenlabs": has("ELEVENLABS_API_KEY"),
    }
