from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import gate  # noqa: E402
import history_store  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(history_store, "_FILE", tmp_path / "chat_history.json")
    db._initialized = False
    db.init_db()


def test_historico_jampa_nao_aparece_no_javes():
    history_store.ensure_session(gate.CORE_SCOPE, "core")
    history_store.ensure_session(gate.CEREBRO_JAMPA_SCOPE, "jampa")
    history_store.append(gate.CORE_SCOPE, "core", {"role": "user", "content": "memória do núcleo"})
    history_store.append(gate.CEREBRO_JAMPA_SCOPE, "jampa", {"role": "user", "content": "memória do jampa"})

    core = history_store.load(gate.CORE_SCOPE, "core")

    assert [row["content"] for row in core] == ["memória do núcleo"]
    assert all("jampa" not in row["content"] for row in core)


def test_historico_javes_nao_aparece_no_jampa():
    history_store.ensure_session(gate.CORE_SCOPE, "core")
    history_store.ensure_session(gate.CEREBRO_JAMPA_SCOPE, "jampa")
    history_store.append(gate.CORE_SCOPE, "core", {"role": "assistant", "content": "resposta core"})
    history_store.append(gate.CEREBRO_JAMPA_SCOPE, "jampa", {"role": "assistant", "content": "resposta jampa"})

    jampa = history_store.load(gate.CEREBRO_JAMPA_SCOPE, "jampa")

    assert [row["content"] for row in jampa] == ["resposta jampa"]
    assert all("core" not in row["content"] for row in jampa)


def test_chamada_antiga_sem_project_id_usa_javes_core():
    history_store.append("user", "legado core")

    rows = history_store.load()

    assert rows[-1]["content"] == "legado core"
    assert history_store.list_sessions(gate.CORE_SCOPE)[0]["project_id"] == gate.CORE_SCOPE
