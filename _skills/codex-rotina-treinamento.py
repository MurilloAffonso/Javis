"""codex-rotina-treinamento — rotina noturna do Codex.

Lê os arquivos em `_treinamento/<area>/_entrada/`, manda cada um pro Open Notebook
(localhost:5055) que resume com Gemini 2.5 Flash, e exporta o resumo final em
`_treinamento/<area>/_resumos/`. Idempotente: arquivos já processados são
pulados via fingerprint (md5 + mtime) salvo em `_treinamento/.processed.json`.

Premissa: Open Notebook está no ar (`docker compose up -d` em
`_ferramentas/integracoes/open-notebook/`) com:
- provider Google AI configurado e gemini-2.5-flash registrado,
- transformação "Dense Summary" disponível (padrão),
- Default Transformation Prompt em PT-BR (já configurado).

Sem dependências externas — usa só `urllib` da stdlib. Pensado pra rodar pelo
Codex CLI (`codex exec`) ou via cron/Task Scheduler de madrugada.

Uso:
    python _skills/codex-rotina-treinamento.py
    python _skills/codex-rotina-treinamento.py --force   # reprocessa tudo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

API_BASE = os.environ.get("OPEN_NOTEBOOK_API", "http://localhost:5055")
JAVIS_ROOT = Path(__file__).resolve().parents[1]
TRAINING_DIR = JAVIS_ROOT / "_treinamento"
LOG_DIR = JAVIS_ROOT / "_logs"
STATE_FILE = TRAINING_DIR / ".processed.json"

AREAS = ["vendas", "conteudo", "tecnico", "estrategia"]
TRANSFORMATION_NAME = "resumo_denso_pt_br"  # transformation custom criada via API, prompt PT-BR
MODEL_NAME = "gemini-2.5-flash"
EXTS = {".md", ".txt"}
HTTP_TIMEOUT = 120


def _http(method: str, path: str, body: dict | None = None, timeout: int = HTTP_TIMEOUT) -> dict | list:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {body_text[:400]}") from None


def _get_id_by_name(endpoint: str, name: str, kind: str) -> str:
    for item in _http("GET", endpoint):
        if item.get("name") == name:
            return item["id"]
    raise RuntimeError(f"{kind} {name!r} não encontrado em {endpoint}. Configure no painel do Open Notebook primeiro.")


def _fingerprint(p: Path) -> str:
    h = hashlib.md5(p.read_bytes()).hexdigest()
    return f"{h}:{p.stat().st_mtime_ns}"


def _load_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict[str, str]) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _process_file(file: Path, transformation_id: str, model_id: str) -> tuple[str, int]:
    text = file.read_text(encoding="utf-8")
    title = file.stem

    # 1. Cria fonte no Open Notebook (pra ficar disponível no painel pra chat/podcast).
    # Atenção: o endpoint JSON-encoded é `/api/sources/json` — `/api/sources` é
    # multipart pra upload de arquivo.
    src = _http("POST", "/api/sources/json", {
        "type": "text",
        "title": title,
        "content": text,
        "embed": False,
        "async_processing": False,
    })
    source_id = src.get("id") or (src.get("source") or {}).get("id") or ""

    # 2. Roda Dense Summary explicitamente pra capturar o output.
    body = {
        "source_id": source_id,
        "transformation_id": transformation_id,
        "input_text": text,
        "model_id": model_id,
    }
    out = _http("POST", "/api/transformations/execute", body)
    summary = (out.get("content") or out.get("output") or "").strip()
    if not summary:
        raise RuntimeError(f"transformation devolveu vazio (keys={list(out.keys())[:6]})")

    # 3. Salva o resumo final em _treinamento/<area>/_resumos/.
    resumos_dir = file.parent.parent / "_resumos"
    resumos_dir.mkdir(parents=True, exist_ok=True)
    out_file = resumos_dir / f"{file.stem}.md"
    out_file.write_text(
        f"# Resumo — {title}\n\n"
        f"> Gerado pela rotina noturna do Codex via Open Notebook + Gemini 2.5 Flash.\n"
        f"> Origem: `{file.relative_to(JAVIS_ROOT).as_posix()}`. Data: {datetime.now():%Y-%m-%d %H:%M}.\n"
        f"> Fonte no Open Notebook: `{source_id}`.\n\n"
        f"{summary}\n",
        encoding="utf-8",
    )
    return source_id, len(summary)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rotina Codex / Open Notebook para resumir _treinamento.")
    parser.add_argument("--force", action="store_true", help="Reprocessa todos os arquivos (ignora state).")
    parser.add_argument("--areas", nargs="+", default=AREAS, help="Áreas a processar (default: todas).")
    args = parser.parse_args(argv)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    state = {} if args.force else _load_state()
    log_lines: list[str] = []
    processed = skipped = failed = 0

    try:
        transformation_id = _get_id_by_name("/api/transformations", TRANSFORMATION_NAME, "Transformação")
        model_id = _get_id_by_name("/api/models", MODEL_NAME, "Modelo")
    except Exception as e:
        print(f"[codex-rotina] FATAL: {e}", file=sys.stderr)
        return 2

    for area in args.areas:
        entrada = TRAINING_DIR / area / "_entrada"
        if not entrada.is_dir():
            continue
        for f in sorted(entrada.iterdir()):
            if f.suffix.lower() not in EXTS or f.name.startswith("."):
                continue
            key = f.relative_to(JAVIS_ROOT).as_posix()
            fp = _fingerprint(f)
            if state.get(key) == fp:
                skipped += 1
                continue
            try:
                src_id, n = _process_file(f, transformation_id, model_id)
                state[key] = fp
                processed += 1
                log_lines.append(f"OK  {key}  → resumo {n} chars (source {src_id})")
            except Exception as e:
                failed += 1
                log_lines.append(f"ERR {key}  → {e}")

    _save_state(state)

    log_file = LOG_DIR / f"{datetime.now():%Y-%m-%d}_codex-treinamento.md"
    header = (
        f"# Rotina Codex / Open Notebook — {datetime.now():%Y-%m-%d %H:%M}\n\n"
        f"Processados: **{processed}**  ·  Pulados (já feitos): {skipped}  ·  Falhas: {failed}\n\n"
        "## Detalhe\n"
    )
    body = "\n".join(f"- {l}" for l in log_lines) if log_lines else "- (nada a fazer)"
    log_file.write_text(header + body + "\n", encoding="utf-8")

    print(f"[codex-rotina] processados={processed} pulados={skipped} falhas={failed} -> {log_file.name}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
