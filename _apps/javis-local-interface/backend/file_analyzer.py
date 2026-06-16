"""file_analyzer.py — converte e analisa arquivos com markitdown + LLM.

Suporta: PDF, Excel (.xlsx/.xls), Word (.docx), PowerPoint (.pptx),
         CSV, TXT, HTML, imagens.
"""
from __future__ import annotations
from pathlib import Path


def _to_markdown(path: Path) -> str:
    try:
        from markitdown import MarkItDown
        result = MarkItDown().convert(str(path))
        return result.text_content or ""
    except Exception as e:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            raise RuntimeError(f"Não consegui ler o arquivo: {e}")


def analyze(path: str | Path, pergunta: str = "") -> dict:
    path = Path(path)
    if not path.exists():
        return {"status": "error", "message": f"Arquivo não encontrado: {path}"}

    try:
        texto = _to_markdown(path)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    if not texto.strip():
        return {"status": "error", "message": "Arquivo vazio ou sem texto extraível."}

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
