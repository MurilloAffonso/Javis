"""R4.2A — ResultCollector: coleta sanitizada, truncada, escopada e sem rede.

Usa um repo Git TEMPORÁRIO isolado como worktree. Nenhum agente é executado.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import db  # noqa: E402
import repositories as repo  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution import result_collector as rc  # noqa: E402

CORE = "javes-core"
JAMPA = "project:cerebro-jampa"


def _clean_env():
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
                "GIT_OBJECT_DIRECTORY", "GIT_NAMESPACE", "GIT_PREFIX"):
        env.pop(key, None)
    return env


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True, env=_clean_env())


def _make_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init")
    _git(path, "config", "user.email", "t@e.st")
    _git(path, "config", "user.name", "Tester")
    (path / "a.txt").write_text("hello\n", encoding="utf-8")
    _git(path, "add", "a.txt")
    _git(path, "commit", "-m", "init")


def _has_git() -> bool:
    try:
        return subprocess.run(["git", "--version"], capture_output=True).returncode == 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _has_git(), reason="git indisponível")


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()


@pytest.fixture
def worktree(tmp_path):
    wt = tmp_path / "wt"
    _make_repo(wt)
    (wt / "a.txt").write_text("mudou\n", encoding="utf-8")   # tracked dirty
    (wt / "novo.txt").write_text("x\n", encoding="utf-8")     # untracked
    return wt


def _mk_task(project_id: str = CORE) -> str:
    tid = et.new_task_id()
    repo.execution_tasks.create(
        task_id=tid, project_id=project_id, executor="claude", objective="obj",
        repository_path="/repo", source_branch="main",
        work_branch=f"javes/exec/{tid}", worktree_path=str(project_id), status="testing",
    )
    return tid


def test_coleta_escreve_e_persiste_escopado(tmp_path, worktree):
    tid = _mk_task(CORE)
    coll = rc.ResultCollector(results_root=tmp_path / "results")
    out = coll.collect(tid, CORE, worktree, stdout="ok", stderr="", test_report="1 passed")
    # arquivos gravados dentro da raiz de resultados
    for key in ("result_path", "diff_path", "test_report_path"):
        assert Path(out[key]).exists()
        assert (tmp_path / "results").resolve() in Path(out[key]).resolve().parents
    # a.txt aparece como alterado
    assert out["changed_count"] >= 1
    # persistido, filtrado por task_id+project_id
    task = repo.execution_tasks.get(tid, CORE)
    assert task["result_path"] == out["result_path"]
    assert repo.execution_tasks.get(tid, JAMPA) is None


def test_sanitiza_tokens_e_authorization(tmp_path, worktree):
    tid = _mk_task(CORE)
    coll = rc.ResultCollector(results_root=tmp_path / "results")
    leak = "chave sk-abc123def456ZZ e Authorization: Bearer sk-secret999888"
    out = coll.collect(tid, CORE, worktree, stdout=leak, stderr=leak)
    stdout_txt = (Path(out["result_path"]).parent / "stdout.txt").read_text(encoding="utf-8")
    stderr_txt = (Path(out["result_path"]).parent / "stderr.txt").read_text(encoding="utf-8")
    for blob in (stdout_txt, stderr_txt):
        assert "sk-abc123def456ZZ" not in blob
        assert "sk-secret999888" not in blob
        assert "[REDACTED]" in blob


def test_trunca_stdout(monkeypatch, tmp_path, worktree):
    monkeypatch.setattr(rc, "MAX_STREAM_CHARS", 10)
    tid = _mk_task(CORE)
    coll = rc.ResultCollector(results_root=tmp_path / "results")
    out = coll.collect(tid, CORE, worktree, stdout="A" * 500)
    stdout_txt = (Path(out["result_path"]).parent / "stdout.txt").read_text(encoding="utf-8")
    assert "[truncado em 10 chars]" in stdout_txt
    assert out["stdout_chars"] <= 60  # 10 + marcador


def test_path_fora_da_raiz_recusado(tmp_path, worktree):
    coll = rc.ResultCollector(results_root=tmp_path / "results")
    # arquivo fora da worktree não é considerado "dentro"
    assert coll.within_worktree(tmp_path / "fora.txt", worktree) is False
    assert coll.within_worktree(worktree / "a.txt", worktree) is True
    # task_id inválido não constrói dir de resultados
    with pytest.raises(et.ValidationError):
        coll.results_dir_for("../escapar")


def test_worktree_inexistente_recusado(tmp_path):
    tid = _mk_task(CORE)
    coll = rc.ResultCollector(results_root=tmp_path / "results")
    with pytest.raises(rc.ResultError):
        coll.collect(tid, CORE, tmp_path / "nao_existe", stdout="x")


def test_summary_nao_traz_conteudo_bruto(tmp_path, worktree):
    tid = _mk_task(CORE)
    coll = rc.ResultCollector(results_root=tmp_path / "results")
    out = coll.collect(tid, CORE, worktree, stdout="segredo qualquer", stderr="erro")
    # o retorno traz só paths + contagens, nunca stdout/stderr/diff bruto
    assert "stdout" not in out and "stderr" not in out and "diff" not in out
    assert set(("result_path", "diff_path", "test_report_path", "changed_count")).issubset(out)
