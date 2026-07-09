from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

BACKEND = Path(__file__).resolve().parents[1] / "backend"
ROOT = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import knowledge as k          # noqa: E402
import knowledge_eval as ke    # noqa: E402


def _blocked_openai() -> ModuleType:
    module = ModuleType("openai")

    def _getattr(name: str):
        raise AssertionError(f"openai import should not happen on local bench path: {name}")

    module.__getattr__ = _getattr  # type: ignore[attr-defined]
    return module


def _bench_module():
    path = ROOT / "scripts" / "rag_embedder_bench.py"
    spec = importlib.util.spec_from_file_location("rag_embedder_bench_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rag_bench_local_offline_deterministic_and_does_not_touch_index(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.delenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", raising=False)
    monkeypatch.setitem(sys.modules, "openai", _blocked_openai())
    monkeypatch.setitem(sys.modules, "knowledge", k)
    monkeypatch.setitem(sys.modules, "knowledge_eval", ke)

    alpha = tmp_path / "alpha-target.md"
    beta = tmp_path / "beta-target.md"
    alpha.write_text("alpha alpha target", encoding="utf-8")
    beta.write_text("beta beta target", encoding="utf-8")

    index = tmp_path / "knowledge_index.json"
    index.write_text("sentinel", encoding="utf-8")
    before = index.read_text(encoding="utf-8")

    monkeypatch.setattr(k, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(k, "INDEX_FILE", index)
    monkeypatch.setattr(k, "_external_vaults", lambda: [])
    monkeypatch.setattr(k, "_iter_files", lambda: iter([alpha, beta]))
    monkeypatch.setattr(ke, "load_golden", lambda path=None: [
        {"q": "alpha", "relevant": ["alpha-target.md"]},
        {"q": "beta", "relevant": ["beta-target.md"]},
    ])

    report = tmp_path / "rag_report.md"
    bench = _bench_module()
    result = bench.run_bench(k=1, providers=("local",), doc_path=report)

    local = result["embedders"]["local"]
    assert result["status"] == "ok"
    assert local["status"] == "ok"
    assert local["recall@k"] == 1.0
    assert local["mrr"] == 1.0
    assert index.read_text(encoding="utf-8") == before
    assert "| local | ok |" in report.read_text(encoding="utf-8")
