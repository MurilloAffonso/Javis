"""MemoryBridge — leitura e escrita da memória persistente do Javis.

Integra com _memoria/ (vault Obsidian) e chat_history.jsonl.
Agentes podem salvar decisões e recuperar contexto de sessões anteriores.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

MEMORIA_DIR      = Path(__file__).resolve().parents[4] / "_memoria"
HISTORY_FILE     = Path(__file__).resolve().parents[2] / "logs" / "chat_history.jsonl"


class MemoryBridge:
    def __init__(self) -> None:
        MEMORIA_DIR.mkdir(exist_ok=True)

    # ── Escrita ───────────────────────────────────────────────

    def save_decision(self, task: str, decision: str, agents: list[str]) -> str:
        ts   = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = task[:40].lower().replace(" ", "-").replace("/", "-")
        name = f"decisao-{ts}-{slug}.md"
        path = MEMORIA_DIR / name

        content = (
            f"# Decisão: {task[:80]}\n\n"
            f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"**Agentes:** {', '.join(agents)}\n\n"
            f"## Resultado\n\n{decision}\n\n"
            f"#decisao #{' #'.join(agents)}\n"
        )
        path.write_text(content, encoding="utf-8")
        return name

    def save_idea(self, text: str) -> str:
        ts   = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"ideia-{ts}.md"
        path = MEMORIA_DIR / name
        path.write_text(
            f"# Ideia — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{text}\n\n#ideia\n",
            encoding="utf-8",
        )
        return name

    # ── Leitura ───────────────────────────────────────────────

    def recall(self, query: str, limit: int = 3) -> str:
        """Busca na memória por palavras-chave. Busca semântica real fica a cargo de knowledge.py."""
        if not MEMORIA_DIR.exists():
            return ""
        words = [w.lower() for w in query.split() if len(w) > 3]
        if not words:
            return ""

        hits: list[tuple[int, str, str]] = []
        for f in sorted(MEMORIA_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            content = f.read_text(encoding="utf-8", errors="ignore")
            score = sum(1 for w in words if w in content.lower())
            if score:
                hits.append((score, f.name, content[:400]))

        hits.sort(key=lambda x: x[0], reverse=True)
        return "\n\n---\n\n".join(f"[{name}]:\n{snippet}" for _, name, snippet in hits[:limit])

    def recent_decisions(self, n: int = 5) -> str:
        """Retorna as N decisões mais recentes."""
        if not MEMORIA_DIR.exists():
            return ""
        files = sorted(MEMORIA_DIR.glob("decisao-*.md"),
                       key=lambda x: x.stat().st_mtime, reverse=True)[:n]
        return "\n\n".join(f.read_text(encoding="utf-8", errors="ignore")[:300] for f in files)

    def save_lesson(self, task: str, diagnosis: str) -> str:
        """Rootcause salva aprendizados para evitar repetição de erros."""
        ts   = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"aprendizado-{ts}.md"
        path = MEMORIA_DIR / name
        path.write_text(
            f"# Aprendizado — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"**Tarefa:** {task[:80]}\n\n"
            f"## Diagnóstico Rootcause\n\n{diagnosis}\n\n"
            f"#aprendizado #rootcause\n",
            encoding="utf-8",
        )
        return name

    def save_voice_command(self, text: str, intent: str, brain: str) -> None:
        """Registra padrão de voz — alimenta o aprendizado da vida própria."""
        entry = {
            "ts":     datetime.now().isoformat(),
            "text":   text[:200],
            "intent": intent,
            "brain":  brain,
        }
        voice_log = MEMORIA_DIR / "voice_patterns.jsonl"
        try:
            with open(voice_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def grow(self, task: str, response: str, agents: list[str], deliverable: str = "") -> None:
        """Faz a memória crescer a cada interação relevante (loop de vida própria)."""
        entry = {
            "ts": datetime.now().isoformat(),
            "task": task[:200],
            "agents": agents,
            "deliverable": deliverable,
            "response_preview": response[:400],
        }
        growth_log = MEMORIA_DIR / "growth_log.jsonl"
        try:
            with open(growth_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def recent_chat(self, n: int = 10) -> list[dict]:
        """Retorna as N mensagens mais recentes do histórico de chat."""
        if not HISTORY_FILE.exists():
            return []
        lines = HISTORY_FILE.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
        entries = []
        for line in reversed(lines[-n * 2:]):
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
        return list(reversed(entries[-n:]))
