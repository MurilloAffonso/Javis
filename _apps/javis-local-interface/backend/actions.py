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
    "open_music":     "https://www.youtube.com/results?search_query=lofi+beats+para+trabalhar",
    "open_openwebui": "http://localhost:3000",
}

_MAX_IDEA_LEN = 2000


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
        "status_sistema":   _system_status,
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

def _open_browser(_: str) -> dict:
    webbrowser.open(URLS["open_browser"])
    return {"status": "ok", "message": "Navegador aberto."}


def _open_youtube(_: str) -> dict:
    webbrowser.open(URLS["open_youtube"])
    return {"status": "ok", "message": "YouTube aberto."}


def _play_music(_: str) -> dict:
    webbrowser.open(URLS["open_music"])
    return {"status": "ok", "message": "Música iniciada no YouTube."}


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
    services = {"Open WebUI (3000)": 3000, "Ollama (11434)": 11434,
                "Voz sandbox (12393)": 12393}
    results = []
    for name, port in services.items():
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                results.append(f"  ✅ {name}")
        except OSError:
            results.append(f"  ❌ {name}")
    summary = "\n".join(results)
    return {"status": "ok", "message": f"Status dos serviços:\n{summary}"}


def _blocked(_: str) -> dict:
    return {"status": "blocked",
            "message": "⛔ Ação bloqueada pelo Command Router — risk_level: critical."}


def _to_llm(text: str) -> dict:
    return {"status": "llm",
            "message": "Encaminhando para Open WebUI: http://localhost:3000",
            "redirect": "http://localhost:3000"}
