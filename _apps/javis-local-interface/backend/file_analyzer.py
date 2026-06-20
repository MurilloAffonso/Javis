"""file_analyzer.py — converte e analisa arquivos com markitdown + LLM.

Suporta: PDF, Excel (.xlsx/.xls), Word (.docx), PowerPoint (.pptx),
         CSV, TXT, HTML, imagens.

Arquivos VISUAIS (imagem ou PDF que é diagrama/imagem, sem texto extraível) vão
pro caminho de VISÃO: o Claude pela assinatura ABRE o arquivo com a própria
ferramenta de leitura (enxerga imagem/PDF) e descreve — markitdown não dá conta
de fluxograma/print, que não têm texto pra extrair.
"""
from __future__ import annotations
from pathlib import Path

_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}

_SYSTEM_VISAO = (
    "Você é o Jamba analisando um arquivo VISUAL (imagem ou PDF de diagrama) para "
    "Murillo. USE sua ferramenta de leitura para ABRIR o arquivo no caminho "
    "informado e descreva o que realmente vê — não invente. Se for fluxograma ou "
    "diagrama, mapeie o fluxo PASSO A PASSO: as etapas, as setas (o que leva a o "
    "quê) e quem faz cada parte, em ordem. Responda em português do Brasil, direto "
    "e organizado. Trate-o por 'senhor'."
)


def _is_mostly_binary(txt: str) -> bool:
    """Heurística: a 'string' é na verdade lixo binário (PDF/imagem cru)?"""
    if not txt:
        return False
    sample = txt[:4000]
    printable = sum(1 for c in sample if c.isprintable() or c in "\n\r\t ")
    return (printable / len(sample)) < 0.85


def _to_markdown(path: Path) -> str:
    """Texto REAL do arquivo, ou "" se não der pra extrair (→ vai pra visão).

    Nunca devolve bytes crus: markitdown às vezes falha e o fallback antigo
    (read_text com errors='replace') vomitava o PDF binário como se fosse texto,
    fazendo o analisador mandar lixo pro cérebro. Agora, se não vier texto de
    verdade, retorna "" e o chamador cai no caminho de visão.
    """
    txt = ""
    try:
        from markitdown import MarkItDown
        txt = MarkItDown().convert(str(path)).text_content or ""
    except Exception:
        txt = ""
    # markitdown devolveu o PDF/binário cru, ou quase nada legível → não é texto.
    if txt.lstrip()[:5].startswith("%PDF") or _is_mostly_binary(txt):
        return ""
    if txt.strip():
        return txt
    # Último recurso: ler como texto puro (só vale pra .txt/.md/.csv/.html reais).
    # errors='strict' faz binário FALHAR (vira "") em vez de virar lixo.
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except Exception:
        return ""


def _analyze_visual(path: Path, pergunta: str = "") -> dict:
    """Caminho de visão: Claude (assinatura) abre e enxerga o arquivo."""
    import claude_brain
    if not claude_brain.available():
        return {"status": "error",
                "message": "Não consegui abrir o arquivo visual: Claude (assinatura) indisponível, senhor."}
    q = (f"Abra e analise o arquivo neste caminho: {path}\n"
         + (f"Pergunta específica do senhor: {pergunta}\n" if pergunta else "")
         + "Descreva o conteúdo. Se for fluxograma/diagrama, mapeie o fluxo passo a passo.")
    out = claude_brain.answer(q, system=_SYSTEM_VISAO, timeout=240,
                              add_dirs=[str(path.parent)])
    if out and out.strip():
        return {"status": "ok", "filename": path.name, "message": out, "chars": 0, "modo": "visao"}
    return {"status": "error", "message": "Não consegui extrair o conteúdo visual do arquivo, senhor."}


def analyze(path: str | Path, pergunta: str = "") -> dict:
    path = Path(path)
    if not path.exists():
        return {"status": "error", "message": f"Arquivo não encontrado: {path}"}

    # Imagem → direto pro caminho de visão (markitdown não lê pixel).
    if path.suffix.lower() in _IMG_EXT:
        return _analyze_visual(path, pergunta)

    try:
        texto = _to_markdown(path)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # PDF/doc que é diagrama/imagem → sai vazio no markitdown → caí na visão.
    if not texto.strip():
        return _analyze_visual(path, pergunta)

    texto_ctx = texto[:8000] + ("\n\n[... truncado ...]" if len(texto) > 8000 else "")

    from llm_providers import call_claude

    instrucao = (
        "Você é o Jamba analisando um arquivo para Murillo.\n"
        "Com base no conteúdo:\n"
        "1. Resuma o arquivo em 2-3 linhas\n"
        "2. Destaque os números e métricas mais importantes\n"
        "3. Liste 3 insights principais\n"
        "4. Sugira 2 ações práticas baseadas nos dados\n"
        "Responda em português, de forma direta e objetiva."
    )
    if pergunta:
        instrucao += f"\n\nPergunta específica: {pergunta}"

    try:
        analise = call_claude([
            {"role": "system", "content": instrucao},
            {"role": "user", "content": f"Arquivo: {path.name}\n\n{texto_ctx}"},
        ], temperature=0.3)
        return {"status": "ok", "filename": path.name, "message": analise, "chars": len(texto)}
    except Exception as e:
        return {"status": "error", "message": f"Erro na análise: {e}"}
