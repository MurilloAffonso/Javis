from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import gate  # noqa: E402
import knowledge  # noqa: E402


class _FlatEmbedder:
    name = "local"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] for _ in texts]


def _blocked_module(name: str) -> ModuleType:
    module = ModuleType(name)

    def _getattr(attr: str):
        raise AssertionError(f"{name} nao deveria ser chamado no reindex local: {attr}")

    module.__getattr__ = _getattr  # type: ignore[attr-defined]
    return module


@pytest.fixture
def legacy_knowledge(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVES_PROVIDER_MODE", "local")
    monkeypatch.setenv("JAVIS_RAG_EMBEDDER", "local")
    monkeypatch.setenv("JAVIS_RAG", "legacy")
    monkeypatch.setattr(knowledge, "JAVIS_ROOT", tmp_path)
    monkeypatch.setattr(knowledge, "INDEX_FILE", tmp_path / "_memoria" / "knowledge_index.json")
    monkeypatch.setattr(knowledge, "_hybrid", lambda: None)
    monkeypatch.setattr(knowledge, "_selected_embedder", lambda: _FlatEmbedder())
    return knowledge


def _write(path: Path, text: str, mtime: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_busca_core_exclui_documentos_vp(legacy_knowledge, tmp_path):
    _write(tmp_path / "_docs" / "core.md", "R2 RAG local project_id javes-core", 100)
    _write(tmp_path / "_projetos" / "cerebro-jampa" / "vp.md", "R2 RAG local project_id VP Jampa", 200)

    legacy_knowledge.build_index(force=True)

    hits = legacy_knowledge.search("R2 RAG local project_id", k=5)

    assert hits
    assert all("cerebro-jampa" not in h["path"] for h in hits)


def test_documento_recente_prioriza_roadmap_antigo_equivalente(legacy_knowledge, tmp_path):
    text = "proximas fases R2 R2.1 provider local-first gates por rota project_id RAG local"
    _write(tmp_path / "_docs" / "ROADMAP_ANTIGO.md", text, 100)
    _write(tmp_path / "docs" / "SAFE_STARTUP.md", text, 300)

    legacy_knowledge.build_index(force=True)

    hits = legacy_knowledge.search("quais sao as proximas fases R2 project_id RAG local", k=2)

    assert hits[0]["path"] == "docs\\SAFE_STARTUP.md" or hits[0]["path"] == "docs/SAFE_STARTUP.md"


def test_busca_sem_project_id_usa_javes_core(legacy_knowledge, tmp_path):
    _write(tmp_path / "_docs" / "core.md", "memoria local javes-core", 100)
    _write(tmp_path / "_projetos" / "vem-passear" / "vp.md", "memoria local vempassear", 200)

    legacy_knowledge.build_index(force=True)

    hits = legacy_knowledge.search("memoria local", k=5, project_id="")

    assert hits
    assert all("vem-passear" not in h["path"] for h in hits)


def test_busca_vp_exige_project_id_explicito(legacy_knowledge, tmp_path):
    _write(tmp_path / "_docs" / "core.md", "catalogo passeios memoria", 100)
    _write(tmp_path / "_projetos" / "vem-passear" / "vp.md", "catalogo passeios memoria", 200)

    legacy_knowledge.build_index(force=True)

    core_hits = legacy_knowledge.search("catalogo passeios memoria", k=5)
    vp_hits = legacy_knowledge.search(
        "catalogo passeios memoria",
        k=5,
        project_id=gate.CEREBRO_JAMPA_SCOPE,
    )

    assert all("vem-passear" not in h["path"] for h in core_hits)
    assert any("vem-passear" in h["path"] for h in vp_hits)


def test_reindex_local_nao_chama_providers_cloud(monkeypatch, legacy_knowledge, tmp_path):
    monkeypatch.setenv("JAVIS_RAG_EMBEDDER", "ollama")
    for name in ("openai", "google.generativeai", "anthropic", "openrouter"):
        monkeypatch.setitem(sys.modules, name, _blocked_module(name))
    monkeypatch.setattr(knowledge, "_selected_embedder", lambda: _FlatEmbedder())
    _write(tmp_path / "docs" / "SAFE_STARTUP.md", "R2.2 reindex local seguro", 100)

    res = legacy_knowledge.build_index(force=True)

    assert res["status"] == "ok"
    assert res["chunks"] >= 1
