"""Test: classificação determinística de escopo (backend/categoria.py).

categoria.de_path(path) rotula cada chunk do RAG em pessoal | projeto | vp,
usando o PATH como sinal — a fronteira do CLAUDE.md ("externos só por registro").
Puro: não toca banco, LLM nem disco (além de ler o project_registry em memória).
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import categoria  # noqa: E402

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(description: str, condition: bool) -> bool:
    print(f"  [{PASS if condition else FAIL}] {description}")
    return condition


def _fails(cases: list[tuple[str, str]]) -> int:
    fails = 0
    for path, esperado in cases:
        got = categoria.de_path(path)
        if not check(f"de_path({path!r}) == {esperado!r}  (got {got!r})", got == esperado):
            fails += 1
    return fails


def test_vp_por_registro() -> int:
    """Prefixo de vault externo → categoria vinda do project_registry (vp)."""
    return _fails([
        ("[CEREBRO.JAMPA] docs/fonte-da-verdade.md", "vp"),
        ("[CEREBRO.JAMPA] skills/manifest.json", "vp"),
        ("[CEREBRO.JAMPA] AGENTS.md", "vp"),
    ])


def test_pessoal() -> int:
    """DNA cognitivo do Murillo → pessoal (barra / e \\ toleradas)."""
    return _fails([
        ("_memoria/dna/thiago-finch.md", "pessoal"),
        ("_memoria\\dna\\thiago-finch.json", "pessoal"),
        ("_MEMORIA/DNA/CAPS.md", "pessoal"),  # case-insensitive
    ])


def test_projeto_default() -> int:
    """Todo o resto interno do Javis → projeto (default)."""
    return _fails([
        ("CLAUDE.md", "projeto"),
        ("_projetos/javis.md", "projeto"),
        ("_memoria/estado.md", "projeto"),      # _memoria != _memoria/dna
        ("_apps/javis-local-interface/README.md", "projeto"),
    ])


def test_bordas() -> int:
    """Path vazio → default; externo desconhecido → 'externo'; não confunde nome."""
    fails = 0
    fails += 0 if check("de_path('') == 'projeto'", categoria.de_path("") == "projeto") else 1
    fails += 0 if check("de_path(None-ish '') seguro", categoria.de_path("") == categoria.DEFAULT) else 1
    fails += 0 if check(
        "vault fora do registro → 'externo'",
        categoria.de_path("[VAULT.DESCONHECIDO] a/b.md") == "externo") else 1
    fails += 0 if check(
        "'_memoria/dna-notas.md' NÃO é pessoal (não é a pasta dna/)",
        categoria.de_path("_memoria/dna-notas.md") == "projeto") else 1
    return fails


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 55)
    print("Testes: categorização determinística de escopo (categoria.py)")
    print("=" * 55)

    total = 0
    total += test_vp_por_registro()
    total += test_pessoal()
    total += test_projeto_default()
    total += test_bordas()

    print("\n" + "=" * 55)
    if total == 0:
        print("\033[32m✅ Todos os testes passaram.\033[0m")
    else:
        print(f"\033[31m❌ {total} teste(s) falharam.\033[0m")
    print("=" * 55)
    sys.exit(total)


if __name__ == "__main__":
    main()
