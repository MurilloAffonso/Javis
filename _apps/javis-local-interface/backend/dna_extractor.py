"""dna_extractor.py — extração de DNA cognitivo unificada (item 3 do roadmap mega-brain).

Consolida num pipeline ÚNICO e estruturado a "extração cognitiva" que hoje está
espalhada em três ferramentas ad-hoc:
  • skill_forge   → frameworks/método acionável
  • wa_analyzer   → voz/tom + objeções (vendas)
  • resumir_treino→ aprendizados de material de estudo

Em vez de três formatos soltos, extrai as MESMAS dimensões cognitivas de qualquer
texto (transcrição, export de WhatsApp, material de estudo) e grava um "dossiê"
JSON + um card em Markdown em `_memoria/dna/` — que entra automaticamente no RAG.

Reaproveita os parsers já existentes (ex.: wa_analyzer.parse_export) em vez de
duplicá-los. Free-first: usa o Claude da assinatura via llm_providers.call_claude
(fallback OpenRouter), sem API paga.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

JAVIS_ROOT = Path(__file__).resolve().parents[3]
DNA_DIR = JAVIS_ROOT / "_memoria" / "dna"

# As 10 dimensões do DNA cognitivo (rótulo → descrição p/ o prompt).
DIMENSOES: dict[str, str] = {
    "filosofias":        "crenças e princípios de fundo que guiam as decisões",
    "modelos_mentais":   "modelos/analogias usados para enxergar problemas",
    "frameworks":        "métodos acionáveis, passo a passo (o QUE fazer, em ordem)",
    "heuristicas":       "regras de bolso e gatilhos rápidos de decisão",
    "valores":           "o que é inegociável / o que mais importa",
    "voz_tom":           "estilo de comunicação: tom, expressões, jeito de falar",
    "objecoes_respostas": "objeção comum → como contorna (útil em vendas)",
    "gatilhos_decisao":  "o que faz avançar e o que faz travar/esfriar",
    "vocabulario":       "termos, jargões e palavras próprias do autor",
    "anti_padroes":      "o que ele evita / o que NÃO fazer",
}

_SYSTEM = (
    "Você é o extrator de DNA cognitivo do Javis. Recebe um texto (transcrição de "
    "especialista, conversa, material de estudo) e destila o MÉTODO e a MENTALIDADE "
    "por trás dele — não um resumo. Português do Brasil. Cite evidência curta (trecho "
    "real) sempre que possível. Se uma dimensão não aparecer no texto, devolva lista "
    "vazia — NÃO invente.\n\n"
    "Responda SOMENTE com um JSON válido, sem texto fora do JSON, neste formato:\n"
    "{\n"
    '  "resumo": "1-2 frases",\n'
    '  "fidelidade": <0-100 quão fiel você capturou>,\n'
    '  "dna": {\n'
    + ",\n".join(f'    "{k}": [ {{"ideia": "...", "evidencia": "..."}} ]' for k in DIMENSOES)
    + "\n  }\n}"
)


# ---------------------------------------------------------------------------
# LLM + parsing robusto de JSON
# ---------------------------------------------------------------------------
def _llm(system: str, user: str) -> str:
    # Extração de DNA é PESADA (texto grande → JSON grande de 10 dimensões).
    # Cascata de custo (decisão MegaBrain: "paga um Gemini que é baratinho"):
    #   1) OpenRouter free — a chave já funciona; grátis.
    #   2) Gemini direto — se GEMINI_API_KEY for válida (Google, grátis).
    #   3) Claude (assinatura) — rede de segurança.
    # Em cada nível só aceita se devolver JSON parseável; senão desce um degrau.
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    try:
        import openrouter_fallback as orf
        if orf.available():
            out = orf.call(msgs, temperature=0.2, max_tokens=8192, timeout=120)
            if out and _parse_json(out) is not None:
                return out
    except Exception:
        pass

    try:
        import gemini_brain
        if gemini_brain.available():
            out = gemini_brain.answer(user, system=system, timeout=120,
                                      max_tokens=8192, temperature=0.2)
            if out and _parse_json(out) is not None:
                return out
    except Exception:
        pass

    from llm_providers import call_claude
    return call_claude(msgs, temperature=0.2)


def _parse_json(raw: str) -> dict | None:
    """Extrai o objeto JSON da resposta do LLM (tolera cercas ```json e texto ao redor)."""
    if not raw:
        return None
    txt = raw.strip()
    txt = re.sub(r"^```(?:json)?", "", txt).strip()
    txt = re.sub(r"```$", "", txt).strip()
    i, j = txt.find("{"), txt.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return None                          # sem JSON (ex.: sentinela "sem cérebro")
    frag = txt[i:j + 1]
    try:
        return json.loads(frag)
    except Exception:
        frag2 = re.sub(r",\s*([}\]])", r"\1", frag)   # remove vírgula pendente
        try:
            return json.loads(frag2)
        except Exception:
            return None


def _normalize(parsed: dict) -> dict:
    """Garante todas as dimensões presentes (como lista) e campos base saneados."""
    dna_in = parsed.get("dna") or {}
    dna = {}
    for k in DIMENSOES:
        v = dna_in.get(k, [])
        dna[k] = v if isinstance(v, list) else [v]
    try:
        fid = int(parsed.get("fidelidade", 0))
    except Exception:
        fid = 0
    return {"resumo": str(parsed.get("resumo", "")).strip(),
            "fidelidade": max(0, min(100, fid)), "dna": dna}


# ---------------------------------------------------------------------------
# Pré-processamento por fonte (reusa parsers existentes)
# ---------------------------------------------------------------------------
def _preprocess(text: str, fonte_tipo: str) -> tuple[str, str, str] | None:
    """Retorna (texto_limpo, fonte, tema_sugerido) ou None se a fonte for inválida."""
    if fonte_tipo == "whatsapp":
        import wa_analyzer
        msgs = wa_analyzer.parse_export(text)
        if not msgs:
            return None
        return wa_analyzer._sample(msgs), "whatsapp", "voz e padrões de venda do Murillo"
    if fonte_tipo == "transcricao":
        return text, "transcricao", ""
    return text, "", ""


# ---------------------------------------------------------------------------
# API principal
# ---------------------------------------------------------------------------
def extract(text: str, fonte: str = "", tema: str = "") -> dict:
    """Extrai o DNA cognitivo de um texto. Retorna {status, fonte, tema, resumo,
    fidelidade, dna:{...10 dimensões...}} ou {status:'error', ...}."""
    text = (text or "").strip()
    if not text:
        return {"status": "error", "message": "Texto vazio."}
    user = (f"Foco/tema: {tema}\n\n" if tema else "") + f"Texto:\n{text[:14000]}"
    try:
        raw = _llm(_SYSTEM, user)
    except Exception as e:
        return {"status": "error", "message": f"Falha no LLM: {e}"}
    parsed = _parse_json(raw)
    if not parsed:
        return {"status": "error", "message": "LLM indisponível ou resposta sem JSON.", "raw": (raw or "")[:400]}
    norm = _normalize(parsed)
    return {"status": "ok", "fonte": fonte, "tema": tema,
            "gerado_em": datetime.now().isoformat(timespec="seconds"), **norm}


def from_whatsapp(text: str, fonte: str = "whatsapp") -> dict:
    pre = _preprocess(text, "whatsapp")
    if pre is None:
        return {"status": "error", "message": "Export de WhatsApp não reconhecido."}
    clean, f, tema = pre
    return extract(clean, fonte or f, tema)


def from_transcript(text: str, tema: str = "") -> dict:
    return extract(text, "transcricao", tema)


# ---------------------------------------------------------------------------
# Card em Markdown + persistência (entra no RAG via _memoria/)
# ---------------------------------------------------------------------------
def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:50] or "dna"


def _fmt_item(it) -> str:
    if isinstance(it, dict):
        ideia = it.get("ideia") or it.get("nome") or it.get("objecao") or ""
        ev = it.get("evidencia") or it.get("resposta") or ""
        passos = it.get("passos")
        linha = f"- **{ideia}**" if ideia else "- "
        if passos and isinstance(passos, list):
            linha += "".join(f"\n  {i+1}. {p}" for i, p in enumerate(passos))
        if ev:
            linha += f"\n  > {ev}"
        return linha
    return f"- {it}"


def _card_md(result: dict) -> str:
    fonte = result.get("fonte") or "—"
    tema = result.get("tema") or "—"
    linhas = [
        f"# DNA cognitivo — {tema if tema != '—' else fonte}",
        f"> Fonte: {fonte} · Fidelidade: {result.get('fidelidade', 0)} · "
        f"Gerado: {result.get('gerado_em', date.today().isoformat())} (dna_extractor)",
        "",
        result.get("resumo", ""),
        "",
    ]
    dna = result.get("dna", {})
    for k, desc in DIMENSOES.items():
        itens = dna.get(k) or []
        if not itens:
            continue
        titulo = k.replace("_", " ").title()
        linhas.append(f"## {titulo}")
        linhas.append(f"_{desc}_")
        linhas.extend(_fmt_item(it) for it in itens)
        linhas.append("")
    return "\n".join(linhas).strip() + "\n"


def save(result: dict) -> dict:
    """Grava o dossiê JSON + o card Markdown em _memoria/dna/. Retorna os caminhos."""
    DNA_DIR.mkdir(parents=True, exist_ok=True)
    base = f"{_slug(result.get('tema') or result.get('fonte') or 'dna')}-{date.today().isoformat()}"
    json_path = DNA_DIR / f"{base}.json"
    md_path = DNA_DIR / f"{base}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_card_md(result), encoding="utf-8")
    return {"json_path": str(json_path), "md_path": str(md_path)}


def extract_and_index(text: str, fonte: str = "", tema: str = "",
                      fonte_tipo: str = "", reindex: bool = True) -> dict:
    """Extrai o DNA, salva o dossiê e reindexa o RAG (best-effort). Ponto de entrada
    do endpoint. `fonte_tipo`: '' | 'whatsapp' | 'transcricao'."""
    if fonte_tipo:
        pre = _preprocess(text, fonte_tipo)
        if pre is None:
            return {"status": "error", "message": f"Fonte '{fonte_tipo}' não reconhecida."}
        text, f, tema_sug = pre
        fonte = fonte or f
        tema = tema or tema_sug
    r = extract(text, fonte, tema)
    if r.get("status") == "ok":
        try:
            r.update(save(r))
        except Exception as e:
            r["save_error"] = str(e)
        if reindex:
            try:
                import knowledge
                knowledge.build_index(force=False)
            except Exception:
                pass
    return r
