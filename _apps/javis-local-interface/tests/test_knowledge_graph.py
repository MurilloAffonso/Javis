"""Testes do knowledge graph (knowledge_graph): build de co-ocorrência + consulta.

Dossiês de DNA sintéticos em dir temporário, DB isolado, sem LLM.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import db               # noqa: E402
import knowledge_graph as kg  # noqa: E402


def _write_dossies(tmp_path):
    d1 = {
        "tema": "vendas",
        "dna": {
            "frameworks": [{"nome": "Fechamento por escassez", "evidencia": "fecha hoje"}],
            "voz_tom": [{"ideia": "Tom caloroso", "evidencia": "bom dia"}],
            "gatilhos_decisao": [{"ideia": "Urgência de data"}],
        },
    }
    d2 = {
        "tema": "lideranca",
        "dna": {
            "frameworks": [{"nome": "Fechamento por escassez"}],   # conceito compartilhado
            "valores": [{"ideia": "Confiança"}],
        },
    }
    (tmp_path / "d1.json").write_text(json.dumps(d1, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "d2.json").write_text(json.dumps(d2, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def graph(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "kg.db")
    monkeypatch.setattr(db, "_initialized", False)
    dossie_dir = tmp_path / "dna"
    dossie_dir.mkdir()
    _write_dossies(dossie_dir)
    return kg, dossie_dir


def test_build_nodes_and_edges(graph):
    mod, ddir = graph
    r = mod.build_from_dna(ddir)
    assert r["status"] == "ok"
    assert r["dossies"] == 2
    assert r["nodes"] == 4          # fechamento, tom, urgência, confiança
    assert r["edges"] == 4          # 3 no d1 + 1 no d2


def test_shared_concept_accumulates_mentions(graph):
    mod, ddir = graph
    mod.build_from_dna(ddir)
    row = db.query_one("SELECT mentions FROM kg_nodes WHERE key = ?", ("fechamento-por-escassez",))
    assert row is not None
    assert row["mentions"] == 2     # aparece nos dois dossiês


def test_neighbors_traverses_cooccurrence(graph):
    mod, ddir = graph
    mod.build_from_dna(ddir)
    res = mod.neighbors("escassez", depth=1)
    labels = {n["label"] for n in res["nodes"]}
    assert "Fechamento por escassez" in labels
    # ligado no d1 (tom, urgência) e no d2 (confiança)
    assert "Tom caloroso" in labels
    assert "Confiança" in labels


def test_neighbors_unknown_term(graph):
    mod, ddir = graph
    mod.build_from_dna(ddir)
    res = mod.neighbors("xptonaoexiste")
    assert res["nodes"] == [] and res["seeds"] == []


def test_rebuild_is_idempotent(graph):
    mod, ddir = graph
    mod.build_from_dna(ddir)
    r2 = mod.build_from_dna(ddir)          # segunda vez não duplica
    assert r2["nodes"] == 4 and r2["edges"] == 4
    row = db.query_one("SELECT mentions FROM kg_nodes WHERE key = ?", ("fechamento-por-escassez",))
    assert row["mentions"] == 2


def test_stats_and_top(graph):
    mod, ddir = graph
    mod.build_from_dna(ddir)
    s = mod.stats()
    assert s["nodes"] == 4 and s["edges"] == 4
    # o conceito mais conectado é o compartilhado (grau 4)
    assert s["top"][0]["label"] == "Fechamento por escassez"


def test_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "empty.db")
    monkeypatch.setattr(db, "_initialized", False)
    empty = tmp_path / "vazio"
    empty.mkdir()
    r = kg.build_from_dna(empty)
    assert r["nodes"] == 0 and r["edges"] == 0 and r["dossies"] == 0
