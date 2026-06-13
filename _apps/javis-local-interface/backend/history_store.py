# history_store.py — salva e carrega histórico de chat entre sessões
import json
from pathlib import Path
from datetime import datetime

_FILE = Path(__file__).parent.parent / "_data" / "chat_history.json"
MAX_ENTRIES = 200


def load() -> list[dict]:
    """Retorna as últimas MAX_ENTRIES mensagens salvas."""
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _FILE.exists():
        return []
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))[-MAX_ENTRIES:]
    except Exception:
        return []


def append(role: str, content: str) -> None:
    """Adiciona uma mensagem ao histórico."""
    hist = load()
    hist.append({"role": role, "content": content, "ts": datetime.now().isoformat()})
    _FILE.write_text(json.dumps(hist[-MAX_ENTRIES:], ensure_ascii=False, indent=2), encoding="utf-8")


def clear() -> None:
    """Limpa todo o histórico."""
    if _FILE.exists():
        _FILE.unlink()
