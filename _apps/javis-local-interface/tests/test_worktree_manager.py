"""R4.1 — worktree_manager em repositório Git TEMPORÁRIO isolado.

Nenhum teste toca o repo real do Javes nem a rede. Cria um repo git efêmero em
tmp_path e valida create/validate/remove + proteções.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from execution import execution_task as et  # noqa: E402
from execution import worktree_manager as wtm  # noqa: E402


def _clean_env():
    """Remove GIT_* de localização (o repo temp não pode herdar o repo do hook)."""
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
                "GIT_OBJECT_DIRECTORY", "GIT_NAMESPACE", "GIT_PREFIX"):
        env.pop(key, None)
    return env


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True, env=_clean_env())


def _make_repo(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init")
    _git(path, "config", "user.email", "t@e.st")
    _git(path, "config", "user.name", "Tester")
    (path / "a.txt").write_text("hello", encoding="utf-8")
    _git(path, "add", "a.txt")
    _git(path, "commit", "-m", "init")
    return _git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "master"


@pytest.fixture
def repo_and_mgr(tmp_path):
    repo = tmp_path / "repo"
    branch = _make_repo(repo)
    wt_root = tmp_path / "worktrees"
    mgr = wtm.WorktreeManager(allowed_repo_roots=[repo], worktree_root=wt_root)
    return repo, branch, wt_root, mgr


def _has_git() -> bool:
    try:
        return subprocess.run(["git", "--version"], capture_output=True).returncode == 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _has_git(), reason="git indisponível")


def test_cria_worktree_isolada(repo_and_mgr):
    repo, branch, wt_root, mgr = repo_and_mgr
    tid = et.new_task_id()
    meta = mgr.create(tid, repo, branch)
    assert meta["work_branch"] == f"javes/exec/{tid}"
    wp = Path(meta["worktree_path"])
    # branch segue o padrão
    assert et.validate_work_branch(meta["work_branch"])
    # worktree fica FORA do repo principal e DENTRO do worktree root
    assert wt_root.resolve() in wp.resolve().parents
    assert repo.resolve() not in wp.resolve().parents
    # branch ativa é a esperada
    assert mgr.validate_existing(tid)["active_branch"] == f"javes/exec/{tid}"


def test_recusa_repo_fora_da_allowlist(tmp_path, repo_and_mgr):
    repo, branch, wt_root, mgr = repo_and_mgr
    outro = tmp_path / "outro"
    _make_repo(outro)
    with pytest.raises(wtm.SecurityError):
        mgr.create(et.new_task_id(), outro, branch)


def test_recusa_task_id_invalido(repo_and_mgr):
    repo, branch, _, mgr = repo_and_mgr
    with pytest.raises(et.ValidationError):
        mgr.create("nao_valido", repo, branch)


def test_master_main_nunca_work_branch():
    for bad in ("master", "main"):
        with pytest.raises(et.ValidationError):
            et.validate_work_branch(bad)


def test_bloqueia_mudanca_rastreada_unstaged(repo_and_mgr):
    repo, branch, _, mgr = repo_and_mgr
    (repo / "a.txt").write_text("mudou", encoding="utf-8")  # tracked dirty
    with pytest.raises(wtm.GitStateError):
        mgr.create(et.new_task_id(), repo, branch)


def test_bloqueia_mudanca_staged(repo_and_mgr):
    repo, branch, _, mgr = repo_and_mgr
    (repo / "a.txt").write_text("mudou", encoding="utf-8")
    _git(repo, "add", "a.txt")
    with pytest.raises(wtm.GitStateError):
        mgr.create(et.new_task_id(), repo, branch)


def test_untracked_nao_bloqueia(repo_and_mgr):
    repo, branch, _, mgr = repo_and_mgr
    (repo / "novo_untracked.txt").write_text("x", encoding="utf-8")  # untracked
    tid = et.new_task_id()
    meta = mgr.create(tid, repo, branch)  # não deve levantar
    assert meta["task_id"] == tid


def test_recusa_source_branch_inexistente(repo_and_mgr):
    repo, _, _, mgr = repo_and_mgr
    with pytest.raises(wtm.GitStateError):
        mgr.create(et.new_task_id(), repo, "nao-existe")


def test_remove_so_dentro_do_worktree_root(repo_and_mgr):
    repo, branch, wt_root, mgr = repo_and_mgr
    tid = et.new_task_id()
    mgr.create(tid, repo, branch)
    out = mgr.remove(tid)
    assert out["removed"] is True
    assert wt_root.resolve() in Path(out["worktree_path"]).resolve().parents


def test_nao_remove_worktree_preservada_em_falha(repo_and_mgr):
    repo, branch, _, mgr = repo_and_mgr
    tid = et.new_task_id()
    mgr.create(tid, repo, branch)
    with pytest.raises(wtm.WorktreeError):
        mgr.remove(tid, status=et.FAILED)  # sem approved_cleanup
    # com autorização explícita, remove
    out = mgr.remove(tid, status=et.FAILED, approved_cleanup=True)
    assert out["removed"] is True
