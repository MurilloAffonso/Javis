"""pulso_mercado.py — "Pulso de mercado" (inspirado no last30days-skill, MIT).

Junta o que está sendo falado sobre um tópico em fontes GRÁTIS (Reddit + YouTube
via social_reader, HackerNews via Algolia, GitHub via integrations) e o Claude
(assinatura) sintetiza um brief com implicações para o negócio. Sem API paga.
"""
from __future__ import annotations
import requests

_TIMEOUT = 15


def _hackernews(query: str, limite: int = 6) -> str:
    try:
        r = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "story", "hitsPerPage": limite},
            timeout=_TIMEOUT,
        )
        hits = r.json().get("hits", [])
        if not hits:
            return ""
        linhas = [f"HackerNews — '{query}':"]
        for h in hits:
            linhas.append(
                f"- {h.get('title', '')} ({h.get('points', 0)} pts, "
                f"{h.get('num_comments', 0)} comentários) {h.get('url') or ''}"
            )
        return "\n".join(linhas)
    except Exception:
        return ""


def _github(query: str, limite: int = 5) -> str:
    try:
        import integrations
        repos = integrations.github_search_repos(query, max_results=limite)
        if not repos:
            return ""
        linhas = [f"GitHub — '{query}':"]
        for r in repos:
            desc = (r.get("description") or "")[:120]
            linhas.append(f"- {r.get('title', '')} — {desc}")
        return "\n".join(linhas)
    except Exception:
        return ""


def pulso(topico: str) -> dict:
    """Coleta sinais grátis + sintetiza com o Claude. Retorna o brief."""
    topico = (topico or "").strip()
    if not topico:
        return {"status": "error", "message": "Diga o tópico do pulso, senhor."}

    partes = []
    try:
        import social_reader
        redes = social_reader.pesquisar_redes(topico)
        if redes.get("status") == "ok":
            partes.append(redes["message"])
    except Exception:
        pass
    hn = _hackernews(topico)
    if hn:
        partes.append(hn)
    gh = _github(topico)
    if gh:
        partes.append(gh)

    bruto = "\n\n---\n\n".join(partes)
    if not bruto.strip():
        return {"status": "error", "message": "Não achei sinal em nenhuma fonte, senhor."}

    try:
        import claude_brain
        if claude_brain.available():
            sys_p = (
                "Você é o analista de mercado do Javis (negócio: Vem Passear Jampa, "
                "turismo em João Pessoa). Recebe sinais brutos de redes/fóruns/repos e "
                "entrega um PULSO em português, objetivo:\n"
                "1) 3-5 pontos do que estão falando / tendências;\n"
                "2) o que isso significa para o negócio;\n"
                "3) 2 ações práticas.\n"
                "Cite a fonte quando der; não invente."
            )
            brief = claude_brain.answer(
                f"Tópico: {topico}\n\nSinais coletados:\n{bruto[:6000]}",
                system=sys_p, timeout=120,
            )
            if brief and brief.strip():
                return {"status": "ok", "topico": topico, "brief": brief.strip(), "fontes": len(partes)}
    except Exception:
        pass

    # sem cérebro: devolve o bruto coletado
    return {"status": "ok", "topico": topico, "brief": bruto[:3000], "fontes": len(partes)}
