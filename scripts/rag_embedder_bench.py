"""R5.1 RAG embedder bench.

This is a one-shot eval script, not the server. It does not enable adapters,
does not change the default embedder, and does not overwrite the real RAG index.

Manual full baseline:

    ollama pull nomic-embed-text
    $env:JAVIS_ENABLE_EXTERNAL_ADAPTERS = "true"
    $env:JAVIS_OLLAMA_EMBED_MODEL = "nomic-embed-text"
    $env:OPENAI_API_KEY = "..."  # optional; only for paid OpenAI baseline
    python scripts/rag_embedder_bench.py

Notes:
- `JAVIS_RAG_EMBEDDER` is irrelevant here; the bench iterates providers.
- If a flag, key, or local Ollama is missing, that provider is reported as
  `skipped` with a reason.
- Output is printed and written to `docs/AUDIT_R5_RAG_EVAL.md`.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "_apps" / "javis-local-interface" / "backend"
DEFAULT_DOC = REPO_ROOT / "docs" / "AUDIT_R5_RAG_EVAL.md"
PROVIDERS = ("openai", "local", "ollama")


def _ensure_backend_path() -> None:
    backend = str(BACKEND)
    if backend not in sys.path:
        sys.path.insert(0, backend)


def _provider_tuple(raw: str) -> tuple[str, ...]:
    providers = tuple(p.strip().lower() for p in raw.split(",") if p.strip())
    unknown = [p for p in providers if p not in PROVIDERS]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown provider(s): {', '.join(unknown)}; allowed: {', '.join(PROVIDERS)}"
        )
    return providers or PROVIDERS


def _fmt(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _provider_rows(result: dict) -> list[dict]:
    rows = []
    for name, data in result.get("embedders", {}).items():
        note = data.get("note", "")
        if name == "local" and data.get("status") == "ok" and not note:
            note = "char 3-gram offline, dep-free"
        rows.append({
            "provider": name,
            "status": data.get("status", "unknown"),
            "hit_rate": data.get("hit_rate"),
            "recall": data.get("recall@k"),
            "precision": data.get("precision@k"),
            "mrr": data.get("mrr"),
            "n": data.get("n"),
            "note": note,
        })
    return rows


def format_table(result: dict) -> str:
    k = result.get("k", 5)
    lines = [
        f"| Provider | Status | hit_rate | recall@{k} | precision@{k} | MRR | n | Nota |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in _provider_rows(result):
        lines.append(
            "| {provider} | {status} | {hit_rate} | {recall} | {precision} | {mrr} | {n} | {note} |".format(
                provider=row["provider"],
                status=row["status"],
                hit_rate=_fmt(row["hit_rate"]),
                recall=_fmt(row["recall"]),
                precision=_fmt(row["precision"]),
                mrr=_fmt(row["mrr"]),
                n=_fmt(row["n"]),
                note=row["note"] or "-",
            )
        )
    return "\n".join(lines)


def format_console(result: dict) -> str:
    if result.get("status") != "ok":
        return json.dumps(result, ensure_ascii=False, indent=2)
    return "\n".join([
        "RAG embedder bench",
        format_table(result),
        "",
        f"Recommendation: {result.get('recommendation', '-')}",
    ])


def compact_result(result: dict) -> dict:
    if result.get("status") != "ok":
        return result
    embedders = {}
    for provider, data in result.get("embedders", {}).items():
        embedders[provider] = {
            key: value
            for key, value in data.items()
            if key != "per_question"
        }
    return {
        "status": result.get("status"),
        "k": result.get("k"),
        "embedders": embedders,
        "recommendation": result.get("recommendation"),
    }


def format_markdown(result: dict, generated_at: str | None = None) -> str:
    generated_at = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    k = result.get("k", 5)
    table = format_table(result) if result.get("status") == "ok" else "Bench failed."
    recommendation = result.get("recommendation", "-")
    raw = json.dumps(compact_result(result), ensure_ascii=False, indent=2)
    return f"""# Audit R5 - RAG embedder quality eval

Atualizado: {generated_at}

Objetivo: comparar, no mesmo golden set, os providers `openai`, `local` e `ollama` para decidir o default do RAG por evidencia. O default continua `openai` ate haver evidencia melhor.

## Como rodar o baseline completo

Este bench e one-shot: nao e o servidor, nao muda o default e nao liga adaptador em runtime. Ele apenas respeita as variaveis de ambiente ja exportadas.

```powershell
ollama pull nomic-embed-text
$env:JAVIS_ENABLE_EXTERNAL_ADAPTERS = "true"
$env:JAVIS_OLLAMA_EMBED_MODEL = "nomic-embed-text"
$env:OPENAI_API_KEY = "..."  # opcional, so para baseline pago OpenAI
python scripts/rag_embedder_bench.py
```

Notas:
- `JAVIS_RAG_EMBEDDER` e irrelevante aqui; o bench itera `openai`, `local` e `ollama`.
- Se OpenAI, Ollama ou o gate `external_adapters` nao estiverem acessiveis, o provider fica `skipped` com motivo.
- O bench nao sobrescreve `_memoria/knowledge_index.json`.

Golden set: `_memoria/rag_eval_golden.json`  
K: {k}

## Resultado

{table}

## Recomendacao

{recommendation}

## Observacoes

- O provider `local` agora usa char 3-gram offline e sem dependencia externa.
- Baseline R5 anterior do hash puro: recall@5 0.2708, MRR 0.2021.
- A linha `local` acima e sempre re-medida pelo bench atual.

## JSON bruto

```json
{raw}
```
"""


def run_bench(
    k: int = 5,
    providers: tuple[str, ...] = PROVIDERS,
    doc_path: Path = DEFAULT_DOC,
    write_doc: bool = True,
) -> dict:
    _ensure_backend_path()
    import knowledge_eval

    result = knowledge_eval.evaluate_embedders(k=k, providers=providers)
    if write_doc:
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(format_markdown(result), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one-shot RAG embedder bench.")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--providers", type=_provider_tuple, default=PROVIDERS)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--no-write-doc", action="store_true")
    args = parser.parse_args(argv)

    result = run_bench(
        k=args.k,
        providers=args.providers,
        doc_path=args.doc,
        write_doc=not args.no_write_doc,
    )
    print(format_console(result))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
