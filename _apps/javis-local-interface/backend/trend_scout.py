"""
trend_scout.py — esquadrões de estudo: cada área busca vídeo de tendência
(YouTube Data API) e repositório relevante (GitHub) e joga em
_treinamento/<area>/_entrada/. Não resume nada (isso é o passo manual do
NotebookLM) — só coleta e organiza a matéria-prima.
"""
from __future__ import annotations
import re
import hashlib
from pathlib import Path
from datetime import datetime

import integrations

TREINO_DIR = Path(__file__).resolve().parents[3] / "_treinamento"

# cada área tem 1+ buscas de vídeo (YouTube) e 1+ buscas de repositório (GitHub)
AREA_QUERIES = {
    "vendas": {
        "youtube": ["técnicas de vendas turismo receptivo 2026", "como vender passeio de barco objeções"],
        "github": ["whatsapp crm sales automation"],
    },
    "conteudo": {
        "youtube": ["tendências reels turismo Brasil 2026", "edição de vídeo vertical para Instagram tendência"],
        "github": ["instagram content calendar automation"],
    },
    "tecnico": {
        "youtube": ["agentes de IA automação 2026 novidades", "notebooklm api integração"],
        "github": ["ai agent orchestration framework"],
    },
    "estrategia": {
        "youtube": ["expansão negócio turismo local estratégia 2026", "growth marketing turismo receptivo"],
        "github": ["small business growth strategy playbook", "tourism business analytics dashboard"],
    },
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def _existing_urls(entrada_dir: Path) -> set[str]:
    urls = set()
    if not entrada_dir.is_dir():
        return urls
    for f in entrada_dir.glob("*.md"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^Fonte:\s*(\S+)", text, re.M)
            if m:
                urls.add(m.group(1))
        except Exception:
            continue
    return urls


def _write_item(entrada_dir: Path, kind: str, item: dict) -> bool:
    """Grava 1 item coletado como .md em _entrada, se a URL ainda não existir. True se gravou."""
    existing = _existing_urls(entrada_dir)
    if item["url"] in existing:
        return False
    entrada_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    h = hashlib.sha1(item["url"].encode()).hexdigest()[:8]
    fname = f"{today}_{kind}_{_slug(item['title'])}_{h}.md"

    # Vídeo: tenta a transcrição (conteúdo real → resumo fiel, não só por tema)
    transcricao = ""
    if kind == "video":
        try:
            t = integrations.youtube_transcript(item["url"])
            if t and t.strip():
                transcricao = f"\n## Transcrição\n{t.strip()}\n"
        except Exception:
            transcricao = ""

    body = (
        f"# {item['title']}\n\n"
        f"Tipo: {kind}\n"
        f"Fonte: {item['url']}\n"
        f"Origem: {item.get('channel', '')}\n"
        f"Data: {item.get('published', '')}\n"
        f"Coletado em: {today}\n"
        f"Transcrição: {'sim' if transcricao else 'não disponível'}\n\n"
        f"{item.get('description', '')}\n"
        f"{transcricao}\n"
        f"## Próximo passo\nResumir com o Javis ('Resumir pendentes' na aba Treino) → "
        f"entra no RAG. (Ou NotebookLM, se preferir resumo manual.)\n"
    )
    (entrada_dir / fname).write_text(body, encoding="utf-8")
    return True


def scout_area(area: str) -> dict:
    """Roda as buscas de uma área e grava o que for novo. Retorna contagem do que entrou."""
    cfg = AREA_QUERIES.get(area)
    if not cfg:
        return {"area": area, "error": "área desconhecida", "novos": 0}

    entrada_dir = TREINO_DIR / area / "_entrada"
    novos = 0
    detalhes = []

    for q in cfg.get("youtube", []):
        for v in integrations.youtube_search_many(q, max_results=2):
            if _write_item(entrada_dir, "video", v):
                novos += 1
                detalhes.append({"tipo": "video", "titulo": v["title"]})

    for q in cfg.get("github", []):
        for r in integrations.github_search_repos(q, max_results=2):
            if _write_item(entrada_dir, "repo", r):
                novos += 1
                detalhes.append({"tipo": "repo", "titulo": r["title"]})

    return {"area": area, "novos": novos, "detalhes": detalhes}


def scout_all() -> list[dict]:
    return [scout_area(area) for area in AREA_QUERIES]


def _count_files(p: Path) -> int:
    if not p.is_dir():
        return 0
    return sum(1 for f in p.iterdir() if f.is_file() and not f.name.startswith("."))


def area_status(area: str) -> dict:
    return {
        "area": area,
        "entrada": _count_files(TREINO_DIR / area / "_entrada"),
        "resumos": _count_files(TREINO_DIR / area / "_resumos"),
    }


def all_status() -> list[dict]:
    return [area_status(area) for area in AREA_QUERIES]
