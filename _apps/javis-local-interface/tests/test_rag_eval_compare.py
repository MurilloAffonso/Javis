from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import knowledge as k          # noqa: E402
import knowledge_eval as ke    # noqa: E402


def _blocked_openai() -> ModuleType:
    module = ModuleType("openai")

    def _getattr(name: str):
        raise AssertionError(f"openai import should not happen on local eval path: {name}")

    module.__getattr__ = _getattr  # type: ignore[attr-defined]
    return module


def test_eval_compare_local_embedder_is_offline_and_deterministic(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setitem(sys.modules, "openai", _blocked_openai())
    monkeypatch.setitem(sys.modules, "knowledge", k)

    alpha = tmp_path / "alpha-target.md"
    beta = tmp_path / "beta-target.md"
    alpha.write_text("alpha alpha target", encoding="utf-8")
    beta.write_text("beta beta target", encoding="utf-8")

    monkeypatch.setattr(k, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(k, "_external_vaults", lambda: [])
    monkeypatch.setattr(k, "_iter_files", lambda: iter([alpha, beta]))

    golden = [
        {"q": "alpha", "relevant": ["alpha-target.md"]},
        {"q": "beta", "relevant": ["beta-target.md"]},
    ]

    result = ke.evaluate_embedders(golden=golden, k=1, providers=("local",))
    local = result["embedders"]["local"]

    assert result["status"] == "ok"
    assert local["status"] == "ok"
    assert local["recall@k"] == 1.0
    assert local["mrr"] == 1.0
    assert local["per_question"][0]["topk_paths"] == ["alpha-target.md"]
