"""Testes do extrator de DNA cognitivo (dna_extractor).

LLM monkeypatchado (nada sai do PC). Cobre: parsing robusto de JSON, normalização
das 10 dimensões, card Markdown + persistência, reuso do parser de WhatsApp e a
reindexação do RAG.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import dna_extractor as dna   # noqa: E402

_CANNED = """```json
{
  "resumo": "Vende catamarã com urgência e tom caloroso.",
  "fidelidade": 88,
  "dna": {
    "voz_tom": [{"ideia": "Tom caloroso com emoji", "evidencia": "Bom dia! 🌅"}],
    "frameworks": [{"nome": "Fechamento por escassez",
                    "passos": ["dar o preço", "criar urgência de hoje"],
                    "evidencia": "fecha hoje que garanto"}],
    "gatilhos_decisao": [{"ideia": "Urgência de data", "evidencia": "amanhã"}]
  }
}
```"""


def test_parse_json_variants():
    assert dna._parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert dna._parse_json('lixo antes {"a": 1} lixo depois') == {"a": 1}
    assert dna._parse_json('{"a": 1,}') == {"a": 1}          # vírgula pendente
    assert dna._parse_json("Estou sem cérebro disponível agora, senhor") is None
    assert dna._parse_json("") is None


def test_extract_normalizes_all_dimensions(monkeypatch):
    monkeypatch.setattr(dna, "_llm", lambda s, u: _CANNED)
    r = dna.extract("texto qualquer", fonte="wa", tema="vendas")
    assert r["status"] == "ok"
    assert r["fidelidade"] == 88
    # todas as 10 dimensões presentes como lista
    assert all(k in r["dna"] and isinstance(r["dna"][k], list) for k in dna.DIMENSOES)
    assert len(r["dna"]["voz_tom"]) == 1
    assert r["dna"]["filosofias"] == []                      # ausente → lista vazia


def test_fidelidade_clamped(monkeypatch):
    monkeypatch.setattr(dna, "_llm", lambda s, u: '{"resumo":"x","fidelidade":150,"dna":{}}')
    r = dna.extract("t")
    assert r["fidelidade"] == 100
    assert all(k in r["dna"] for k in dna.DIMENSOES)


def test_llm_unavailable_errors(monkeypatch):
    monkeypatch.setattr(dna, "_llm", lambda s, u: "Estou sem cérebro disponível agora, senhor")
    r = dna.extract("texto")
    assert r["status"] == "error"


def test_save_writes_json_and_card(tmp_path, monkeypatch):
    monkeypatch.setattr(dna, "DNA_DIR", tmp_path / "dna")
    monkeypatch.setattr(dna, "_llm", lambda s, u: _CANNED)
    r = dna.extract("texto", fonte="teste", tema="vendas catamara")
    paths = dna.save(r)
    assert Path(paths["json_path"]).exists()
    md = Path(paths["md_path"]).read_text(encoding="utf-8")
    assert "Voz Tom" in md and "Frameworks" in md
    assert "Fechamento por escassez" in md
    assert "dar o preço" in md                               # passos do framework renderizados


def test_from_whatsapp_reuses_parser(monkeypatch):
    captured = {}

    def fake_llm(system, user):
        captured["user"] = user
        return _CANNED

    monkeypatch.setattr(dna, "_llm", fake_llm)
    export = (
        "01/07/2026 14:30 - Mensagens e ligações são criptografadas de ponta a ponta.\n"
        "01/07/2026 14:31 - Murillo: Bom dia! Temos catamarã amanhã 🌅\n"
        "01/07/2026 14:32 - Cliente: Quanto custa?\n"
        "01/07/2026 14:33 - Murillo: R$ 120 por pessoa, fecha hoje que garanto\n"
    )
    r = dna.from_whatsapp(export)
    assert r["status"] == "ok"
    assert r["fonte"] == "whatsapp"
    # o texto que foi ao LLM veio do parser: tem as mensagens, sem a linha de sistema
    assert "catamar" in captured["user"]
    assert "criptografad" not in captured["user"]


def test_from_whatsapp_bad_export():
    r = dna.from_whatsapp("isto não é um export de whatsapp")
    assert r["status"] == "error"


def test_extract_and_index_reindexes(tmp_path, monkeypatch):
    monkeypatch.setattr(dna, "DNA_DIR", tmp_path / "dna")
    monkeypatch.setattr(dna, "_llm", lambda s, u: _CANNED)
    calls = {"n": 0}
    import knowledge
    monkeypatch.setattr(knowledge, "build_index",
                        lambda force=False: calls.__setitem__("n", calls["n"] + 1))
    r = dna.extract_and_index("texto", fonte="t", tema="vendas")
    assert r["status"] == "ok"
    assert "json_path" in r
    assert calls["n"] == 1
