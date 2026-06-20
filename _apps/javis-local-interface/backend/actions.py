"""Actions — executa ações locais da whitelist. Sem shell arbitrário."""
from __future__ import annotations
import subprocess
import shutil
import webbrowser
import os
import platform
from datetime import datetime
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]

URLS = {
    "open_browser":   "https://www.google.com",
    "open_youtube":   "https://www.youtube.com",
    # Stream lofi 24/7 — abre no modo player e dá autoplay
    "open_music":     "https://www.youtube.com/watch?v=jfKfPfyJRdk",
    "open_openwebui": "http://localhost:3000",
}

# Sites que o senhor pode pedir pelo nome ("abre o instagram")
_KNOWN_SITES = {
    "instagram":   "https://www.instagram.com",
    "facebook":    "https://www.facebook.com",
    "whatsapp":    "https://web.whatsapp.com",
    "gmail":       "https://mail.google.com",
    "google maps": "https://www.google.com/maps",
    "maps":        "https://www.google.com/maps",
    "drive":       "https://drive.google.com",
    "chatgpt":     "https://chat.openai.com",
    "google":      "https://www.google.com",
}

# Palavras de comando removidas ao montar uma busca no navegador
_BROWSER_FILLERS = {
    "abra", "abre", "abrir", "entra", "entre", "entrar", "vai", "no", "na",
    "o", "a", "navegador", "browser", "chrome", "firefox", "edge", "internet",
    "pra", "para", "mim", "por", "favor", "e", "me", "quero", "que", "você",
    "voce", "jamba", "site", "pagina", "página", "da", "do", "de",
    "procura", "procurar", "pesquisa", "pesquisar", "busca", "buscar", "acessa",
    "acessar", "abre o", "no navegador",
}

# Termos genéricos que removemos para extrair o que tocar de fato
_MUSIC_FILLERS = {
    "toca", "tocar", "toque", "coloca", "colocar", "bota", "botar", "play",
    "uma", "um", "o", "a", "de", "do", "da", "no", "na", "som", "música",
    "musica", "playlist", "aí", "ai", "por", "favor", "pra", "para", "mim",
    "jamba", "youtube",
    # verbos de comando que vazavam para a busca (ex.: "abra o youtube e toque racionais")
    "abra", "abre", "abrir", "entra", "entre", "entrar", "vai", "quero", "que",
    "e", "me",
}

_MAX_IDEA_LEN = 2000


def _hora_data(_: str) -> dict:
    from datetime import datetime
    dias = ["segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"]
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    n = datetime.now()
    return {"status":"ok","message":f"São {n.strftime('%H:%M')}, {dias[n.weekday()]}, {n.day} de {meses[n.month-1]} de {n.year}, senhor."}


def execute(intent: str, user_text: str = "") -> dict:
    """Despacha para o handler correto e retorna resultado padronizado."""
    handlers = {
        "abrir_navegador":  _open_browser,
        "abrir_youtube":    _open_youtube,
        "tocar_musica":     _play_music,
        "abrir_openwebui":  _open_openwebui,
        "abrir_javis":      _open_javis_folder,
        "abrir_vscode":     _open_vscode,
        "abrir_terminal":   _open_terminal,
        "abrir_projeto":    lambda t: _open_javis_folder(t),
        "registrar_ideia":  _register_idea,
        "listar_lembretes": _list_reminders,
        "status_sistema":   _system_status,
        "analisar_site":    _analyze_site,
        "clima":            _weather,
        "hora_data":        _hora_data,
        "trocar_motor":     _switch_brain,
        "acao_perigosa":    _blocked,
        "conversa":         _to_llm,
        "desconhecido":     _to_llm,
    }
    handler = handlers.get(intent, _to_llm)
    try:
        return handler(user_text)
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


# --- handlers individuais ---

def _switch_brain(text: str) -> dict:
    """Troca o motor de EXECUÇÃO (programar) entre Claude e Codex por voz/texto.

    Sem nome de motor na fala → só informa qual está ativo. Roda no fast-path
    (sem LLM), resposta instantânea.
    """
    import brain_switch
    low = (text or "").lower()
    quer_codex  = "codex" in low
    quer_claude = "claude" in low

    if quer_codex and not quer_claude:
        alvo = "codex"
    elif quer_claude and not quer_codex:
        alvo = "claude"
    else:
        # nenhum (ou ambos) citado → só reporta o ativo
        ativo = brain_switch.get_active()
        nome = "Codex" if ativo == "codex" else "Claude"
        return {"status": "ok", "message": f"O motor de execução ativo é o {nome}, senhor."}

    atual = brain_switch.get_active()
    nome_alvo = "Codex" if alvo == "codex" else "Claude"
    if atual == alvo:
        return {"status": "ok", "message": f"O motor já está no {nome_alvo}, senhor."}
    try:
        brain_switch.set_active(alvo)
    except Exception as exc:
        return {"status": "error", "message": f"Não consegui trocar o motor, senhor: {exc}"}
    return {"status": "ok", "message": f"Pronto, senhor. As tarefas de programação agora vão pro {nome_alvo}."}


def _browser_target(text: str) -> tuple[str, str]:
    """Decide PRA ONDE abrir o navegador a partir do que o senhor falou.
    Retorna (url, rótulo amigável)."""
    import re
    import urllib.parse

    raw = text or ""
    low = raw.lower()

    # 1) URL explícita (https://...)
    m = re.search(r"https?://[^\s]+", raw)
    if m:
        url = m.group(0).rstrip(".,;)")
        return url, url

    # 2) domínio solto (ex.: "vempassearjampa.com.br")
    m = re.search(r"\b([a-z0-9-]+\.(?:com|com\.br|net|org|io|dev|app|gov|edu)(?:\.[a-z]{2})?)\b", low)
    if m:
        return "https://" + m.group(1), m.group(1)

    # 3) Instagram da Vem Passear — só abre o perfil se o handle estiver configurado (.env)
    if "instagram" in low and ("vem passear" in low or "vempassear" in low or "jampa" in low):
        handle = os.environ.get("VEMPASSEAR_INSTAGRAM", "").strip().lstrip("@")
        if handle:
            return f"https://www.instagram.com/{handle}", f"o Instagram @{handle}"

    # 4) site conhecido pelo nome (instagram, gmail, maps...)
    for name, url in _KNOWN_SITES.items():
        if name in low:
            return url, name.capitalize()

    # 5) sobrou conteúdo? faz uma busca no Google
    words = [w for w in re.findall(r"[a-zà-ÿ0-9]+", low) if w not in _BROWSER_FILLERS]
    if words:
        q = " ".join(words)
        return "https://www.google.com/search?q=" + urllib.parse.quote(q), f'a busca por "{q}"'

    # 6) nada específico → Google
    return URLS["open_browser"], "o navegador"


def _open_browser(text: str = "") -> dict:
    url, label = _browser_target(text)
    webbrowser.open(url)
    return {"status": "ok", "message": f"Abrindo {label}, senhor."}


def _open_youtube(_: str) -> dict:
    webbrowser.open(URLS["open_youtube"])
    return {"status": "ok", "message": "YouTube aberto."}


def _play_music(text: str) -> dict:
    """Toca música. Com YOUTUBE_API_KEY toca o vídeo EXATO; senão busca/abre o stream lofi."""
    import re
    import urllib.parse

    words = re.findall(r"[a-zà-ÿ0-9]+", (text or "").lower())
    query = [w for w in words if w not in _MUSIC_FILLERS]

    if query:
        term = " ".join(query)
        # 1) Tenta a API do YouTube — abre o vídeo exato (autoplay de verdade)
        try:
            import integrations
            url = integrations.youtube_watch_url(term)
        except Exception:
            url = None
        if url:
            webbrowser.open(url)
            return {"status": "ok", "message": f"🎵 Tocando \"{term}\" no YouTube, senhor."}
        # 2) Fallback — página de busca (sem API key)
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(term)
        webbrowser.open(url)
        return {"status": "ok", "message": f"🎵 Buscando \"{term}\" no YouTube — clique no primeiro vídeo para tocar."}

    webbrowser.open(URLS["open_music"])
    return {"status": "ok", "message": "🎵 Tocando lofi no YouTube (stream 24/7), senhor."}


def _open_openwebui(_: str) -> dict:
    webbrowser.open(URLS["open_openwebui"])
    return {"status": "ok", "message": "Open WebUI aberto em http://localhost:3000"}


def _open_javis_folder(_: str) -> dict:
    path = str(JAVIS_ROOT)
    if platform.system() == "Windows":
        os.startfile(path)
    else:
        subprocess.Popen(["xdg-open", path])
    return {"status": "ok", "message": f"Pasta aberta: {path}"}


def _open_vscode(_: str) -> dict:
    code_exe = shutil.which("code")
    if code_exe is None:
        return {"status": "error", "message": "VS Code não encontrado no PATH."}
    if not JAVIS_ROOT.is_dir():
        return {"status": "error", "message": f"Pasta não encontrada: {JAVIS_ROOT}"}
    subprocess.Popen([code_exe, str(JAVIS_ROOT)])
    return {"status": "ok", "message": f"VS Code aberto em: {JAVIS_ROOT}"}


def _open_terminal(_: str) -> dict:
    if platform.system() == "Windows":
        subprocess.Popen(["powershell.exe", "-NoExit"], cwd=str(JAVIS_ROOT))
    else:
        subprocess.Popen(["gnome-terminal", "--working-directory", str(JAVIS_ROOT)])
    return {"status": "ok", "message": "Terminal aberto."}


def _register_idea(text: str) -> dict:
    clean = text.strip()
    if not clean:
        return {"status": "error", "message": "Texto vazio — ideia não registrada."}
    truncated = len(clean) > _MAX_IDEA_LEN
    if truncated:
        clean = clean[:_MAX_IDEA_LEN]
    ideas_dir = JAVIS_ROOT / "_ideias"
    ideas_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    file = ideas_dir / f"ideia_{stamp}.md"
    content = f"# Ideia — {stamp}\n\n{clean}\n"
    if truncated:
        content += "\n> ⚠️ Texto truncado para 2000 caracteres.\n"
    file.write_text(content, encoding="utf-8")
    msg = f"Ideia salva em _ideias/ideia_{stamp}.md"
    if truncated:
        msg += " (truncado para 2000 chars)"
    return {"status": "ok", "message": msg}


def _system_status(_: str) -> dict:
    import socket
    services = {"Open WebUI (3000)": 3000, "Voz sandbox (12393)": 12393}
    results = []
    for name, port in services.items():
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                results.append(f"  ✅ {name}")
        except OSError:
            results.append(f"  ❌ {name}")
    summary = "\n".join(results)
    return {"status": "ok", "message": f"Status dos serviços:\n{summary}"}


def _analyze_site(text: str) -> dict:
    """Analisa um site e gera um esqueleto de código próprio recriando o layout."""
    import site_analyzer
    result = site_analyzer.analyze(text, generate_code=True)
    if result.get("status") != "ok":
        return {"status": "error", "message": result.get("message", "Falha ao analisar site.")}
    return {"status": "ok", "message": result["message"], "url": result.get("url", "")}


def _weather(text: str) -> dict:
    """Clima atual. Extrai cidade de 'clima em X'; senão usa JAMBA_CITY."""
    import re
    import integrations

    m = re.search(r"\b(?:em|no|na|de|do|da)\s+([a-zà-ÿ\s]{3,40})$", (text or "").strip(), re.I)
    city = m.group(1).strip() if m else ""

    data = integrations.weather(city)
    if not data:
        if not os.environ.get("OPENWEATHER_API_KEY", "").strip():
            return {"status": "error",
                    "message": "Clima indisponível, senhor — falta a OPENWEATHER_API_KEY no .env (grátis em openweathermap.org/api)."}
        return {"status": "error", "message": "Não consegui obter o clima dessa cidade, senhor."}

    msg = (f"🌡️ {data['city']}: {data['temp']}°C ({data['desc']}), "
           f"sensação {data['feels']}°C, umidade {data['humidity']}%, vento {data['wind']} km/h, senhor.")
    return {"status": "ok", "message": msg}


def _list_reminders(_: str) -> dict:
    try:
        import reminders
        pending = reminders.list_pending()
    except Exception:
        pending = []
    if not pending:
        return {"status": "ok", "message": "Nenhum lembrete pendente, senhor."}
    lines = [f"  • {r}" for r in pending]
    return {"status": "ok", "message": "Lembretes pendentes:\n" + "\n".join(lines)}


def _blocked(_: str) -> dict:
    return {"status": "blocked",
            "message": "⛔ Ação bloqueada pelo Command Router — risk_level: critical."}


def _to_llm(text: str) -> dict:
    return {"status": "llm",
            "message": "Encaminhando para Open WebUI: http://localhost:3000",
            "redirect": "http://localhost:3000"}
