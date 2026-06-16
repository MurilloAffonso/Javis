"""App Launcher — abre o máximo de coisas no PC do senhor por nome.

Estratégia em cascata:
  1. Apps conhecidos (mapa de aliases → comando)
  2. URI de sistema (ms-settings:, etc.)
  3. `start <nome>` genérico do Windows (acha no menu Iniciar / PATH)
"""
from __future__ import annotations
import os
import shutil
import subprocess
import urllib.parse
import webbrowser

# Aliases → como abrir (comando para shell `start`)
WINDOWS_APPS: dict[str, str] = {
    # navegadores
    "chrome": "chrome", "google chrome": "chrome",
    "edge": "msedge", "firefox": "firefox", "opera": "opera", "brave": "brave",
    # produtividade
    "word": "winword", "excel": "excel", "powerpoint": "powerpnt",
    "outlook": "outlook", "onenote": "onenote",
    "bloco de notas": "notepad", "notepad": "notepad",
    "calculadora": "calc", "calculator": "calc", "calc": "calc",
    "paint": "mspaint", "wordpad": "write",
    # sistema
    "explorador": "explorer", "explorer": "explorer", "arquivos": "explorer",
    "configurações": "ms-settings:", "configuracoes": "ms-settings:", "settings": "ms-settings:",
    "painel de controle": "control", "control panel": "control",
    "gerenciador de tarefas": "taskmgr", "task manager": "taskmgr", "taskmgr": "taskmgr",
    "prompt": "cmd", "cmd": "cmd", "powershell": "powershell",
    "loja": "ms-windows-store:", "microsoft store": "ms-windows-store:",
    "câmera": "microsoft.windows.camera:", "camera": "microsoft.windows.camera:",
    "fotos": "ms-photos:", "photos": "ms-photos:",
    "mapa": "bingmaps:", "mapas": "bingmaps:",
    "calendário": "outlookcal:", "calendario": "outlookcal:",
    # comunicação / mídia / jogos (se instalados)
    "spotify": "spotify", "discord": "discord", "telegram": "telegram",
    "whatsapp": "whatsapp", "steam": "steam", "epic": "com.epicgames.launcher:",
    "obs": "obs64", "zoom": "zoom", "teams": "teams", "vlc": "vlc",
    # dev
    "vscode": "code", "vs code": "code", "code": "code",
    "github desktop": "github", "docker": "docker desktop",
}

# URIs de Configurações específicas
SETTINGS_URIS = {
    "wifi": "ms-settings:network-wifi",
    "wi-fi": "ms-settings:network-wifi",
    "bluetooth": "ms-settings:bluetooth",
    "som": "ms-settings:sound",
    "áudio": "ms-settings:sound",
    "audio": "ms-settings:sound",
    "tela": "ms-settings:display",
    "monitor": "ms-settings:display",
    "bateria": "ms-settings:batterysaver",
    "atualização": "ms-settings:windowsupdate",
    "atualizacao": "ms-settings:windowsupdate",
    "impressora": "ms-settings:printers",
    "impressoras": "ms-settings:printers",
}


def open_app(name: str) -> dict:
    """Abre um app/janela do sistema pelo nome falado."""
    raw = (name or "").strip()
    key = raw.lower()
    if not key:
        return {"status": "error", "message": "Qual app devo abrir, senhor?"}

    # 1) Configurações específicas
    if key in SETTINGS_URIS:
        return _start(SETTINGS_URIS[key], raw)

    # 2) Apps conhecidos
    for alias, cmd in WINDOWS_APPS.items():
        if alias in key:
            return _start(cmd, alias)

    # 3) Genérico — deixa o Windows tentar achar no menu Iniciar
    return _start(raw, raw)


def _start(cmd: str, label: str) -> dict:
    try:
        if cmd.endswith(":") or cmd.startswith(("ms-", "microsoft.", "bingmaps", "outlook", "com.")):
            os.startfile(cmd)  # URIs de protocolo
        else:
            subprocess.Popen(["cmd", "/c", "start", "", cmd], shell=False)
        return {"status": "ok", "message": f"Abrindo {label}, senhor."}
    except Exception as e:
        return {"status": "error", "message": f"Não consegui abrir {label}, senhor: {e}"}


def _norm(s: str) -> str:
    """Minúsculas sem acento, para casar 'imagens'/'músicas'/'área' etc."""
    import unicodedata
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


# Aliases de pastas conhecidas → subpasta do perfil do usuário (~).
KNOWN_FOLDERS: dict[str, str] = {
    "documentos": "Documents", "documents": "Documents", "docs": "Documents",
    "downloads": "Downloads", "download": "Downloads", "baixados": "Downloads",
    "imagens": "Pictures", "fotos": "Pictures", "pictures": "Pictures", "figuras": "Pictures",
    "videos": "Videos", "video": "Videos",
    "musica": "Music", "musicas": "Music", "music": "Music", "sons": "Music",
    "area de trabalho": "Desktop", "desktop": "Desktop",
    "onedrive": "OneDrive",
}


def open_folder(name: str) -> dict:
    """Abre uma pasta NOMEADA (Documentos, Downloads, Imagens, Desktop...) ou um caminho.

    Resolve a pasta certa do perfil do Windows em vez de só abrir o Explorer no
    lugar padrão.
    """
    raw = (name or "").strip()
    if not raw:
        return {"status": "error", "message": "Qual pasta devo abrir, senhor?"}

    # 1) Caminho absoluto explícito (ex.: C:\... ou /...)
    if os.path.isabs(raw) and os.path.isdir(raw):
        target = raw
    else:
        # 2) Pasta conhecida do perfil (casa por substring, sem acento)
        key = _norm(raw)
        sub = None
        for alias, folder in KNOWN_FOLDERS.items():
            if alias in key:
                sub = folder
                break
        home = os.path.expanduser("~")
        if sub is None:
            return {"status": "error",
                    "message": f"Não conheço a pasta '{raw}', senhor. Tente Documentos, Downloads, Imagens, Vídeos, Música ou Desktop."}
        target = os.path.join(home, sub)
        # OneDrive costuma espelhar Documentos/Imagens/Desktop — tenta lá se faltar
        if not os.path.isdir(target):
            alt = os.path.join(home, "OneDrive", sub)
            if os.path.isdir(alt):
                target = alt

    if not os.path.isdir(target):
        return {"status": "error", "message": f"A pasta não existe no PC, senhor: {target}"}
    try:
        os.startfile(target) if os.name == "nt" else subprocess.Popen(["xdg-open", target])
    except Exception as e:
        return {"status": "error", "message": f"Não consegui abrir a pasta, senhor: {e}"}
    return {"status": "ok", "message": f"Pasta aberta: {target}"}


def open_site(url: str) -> dict:
    """Abre qualquer site. Aceita 'youtube.com' ou 'https://...'."""
    u = (url or "").strip()
    if not u:
        return {"status": "error", "message": "Qual site, senhor?"}
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    webbrowser.open(u)
    return {"status": "ok", "message": f"Abrindo {u}, senhor."}


def google_search(term: str) -> dict:
    """Pesquisa no Google."""
    t = (term or "").strip()
    if not t:
        return {"status": "error", "message": "O que pesquiso, senhor?"}
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(t))
    return {"status": "ok", "message": f"Pesquisando \"{t}\" no Google, senhor."}
