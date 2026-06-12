"""Profile — memória de personalização do Jamba.

Guarda fatos sobre Murillo (preferências, rotina, projetos) num arquivo simples
e os injeta no prompt do agente para o Jamba "conhecer o senhor" entre sessões.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
PROFILE_FILE = JAVIS_ROOT / "_memoria" / "perfil.json"
_MAX_FACTS = 60


def _load() -> list[dict]:
    if not PROFILE_FILE.exists():
        return []
    try:
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(facts: list[dict]) -> None:
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")


def save_fact(fact: str) -> str:
    fact = (fact or "").strip()
    if not fact:
        return "Nada para lembrar, senhor."
    facts = _load()
    # evita duplicar fato idêntico
    if any(f.get("fact", "").lower() == fact.lower() for f in facts):
        return "Já tenho isso registrado, senhor."
    facts.append({"fact": fact, "ts": datetime.now().isoformat(timespec="seconds")})
    facts = facts[-_MAX_FACTS:]
    _save(facts)
    return f"Anotado, senhor: {fact}"


def list_facts() -> list[str]:
    return [f.get("fact", "") for f in _load() if f.get("fact")]


def context_block() -> str:
    """Bloco de fatos para injetar no system prompt do agente."""
    facts = list_facts()
    if not facts:
        return ""
    linhas = "\n".join(f"- {f}" for f in facts[-30:])
    return f"\n\nO que você já sabe sobre o senhor (use quando for relevante):\n{linhas}\n"


def forget(substr: str) -> str:
    substr = (substr or "").strip().lower()
    if not substr:
        return "O que devo esquecer, senhor?"
    facts = _load()
    kept = [f for f in facts if substr not in f.get("fact", "").lower()]
    removed = len(facts) - len(kept)
    _save(kept)
    return f"Esqueci {removed} item(ns), senhor." if removed else "Não achei nada com isso, senhor."
