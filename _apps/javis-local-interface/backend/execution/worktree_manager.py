"""worktree_manager — cria/valida/remove worktrees Git isoladas (R4.1).

Fundação segura: NÃO executa agentes. Toda operação Git usa subprocess com lista
de argumentos (shell=False), timeout e captura de saída; erros são sanitizados.

Invariantes:
- repository_path deve resolver EXATAMENTE para um allowed repo root;
- a worktree fica FORA da árvore principal, sob o worktree root
  (default: <desktop>/javis-worktrees), nunca em <repo>/_worktrees;
- branch sempre derivada do task_id (javes/exec/<task_id>), nunca master/main;
- nunca remove nada fora do worktree root.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from . import execution_task as et
from ._sanitize import sanitize

# Raiz do repo Javes (…/javis). Em produção é o único repo permitido; nos testes
# o construtor recebe um root temporário isolado.
JAVIS_ROOT = Path(__file__).resolve().parents[4]

# Worktrees ficam FORA do repo, ao lado dele (…/Desktop/javis-worktrees).
# Configurável por env segura (NÃO lê .env). Default derivado, não hardcoded.
_DEFAULT_WORKTREE_ROOT = JAVIS_ROOT.parent / "javis-worktrees"

_GIT_TIMEOUT = 30
# Variáveis que apontam o git para OUTRO repositório (ex.: setadas por um git
# hook em execução). Precisam ser removidas para o subprocess operar SEMPRE no
# repo/worktree que passamos via cwd — nunca no repo ambiente.
_GIT_LOCATION_ENV = (
    "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY", "GIT_NAMESPACE", "GIT_PREFIX",
)


def _clean_git_env() -> dict:
    env = dict(os.environ)
    for key in _GIT_LOCATION_ENV:
        env.pop(key, None)
    return env
# Marcadores de operação Git em andamento (merge/rebase/cherry-pick/revert).
_INPROGRESS = ("MERGE_HEAD", "REBASE_HEAD", "rebase-merge", "rebase-apply",
               "CHERRY_PICK_HEAD", "REVERT_HEAD")


class WorktreeError(et.ExecutionError):
    pass


class SecurityError(WorktreeError):
    pass


class GitStateError(WorktreeError):
    pass


def _resolve(path) -> Path:
    return Path(path).resolve()


def _is_within(child: Path, parent: Path) -> bool:
    """True se child está estritamente dentro de parent (após resolve)."""
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return child != parent


class WorktreeManager:
    def __init__(self, allowed_repo_roots=None, worktree_root=None):
        roots = allowed_repo_roots if allowed_repo_roots is not None else [JAVIS_ROOT]
        self.allowed_repo_roots = [_resolve(r) for r in roots]
        env_root = os.environ.get("JAVIS_WORKTREE_ROOT")  # env, não .env
        self.worktree_root = _resolve(worktree_root or env_root or _DEFAULT_WORKTREE_ROOT)

    # ── validações ────────────────────────────────────────────────────────
    def validate_repository_path(self, repository_path) -> Path:
        raw = Path(repository_path)
        # rejeita symlink explícito (resolve seguiria o link e mascararia o alvo)
        if raw.is_symlink():
            raise SecurityError("repository_path é symlink")
        resolved = raw.resolve()
        if resolved not in self.allowed_repo_roots:
            raise SecurityError("repository_path fora da allowlist de repos")
        return resolved

    def worktree_path_for(self, task_id: str) -> Path:
        """Reconstrói o path SEMPRE a partir do task_id validado (nunca do input)."""
        tid = et.validate_task_id(task_id)
        wp = _resolve(self.worktree_root / tid)
        if wp.parent != self.worktree_root:
            raise SecurityError("worktree_path fora do worktree root")
        return wp

    def _git(self, cwd: Path, args: list[str], timeout: int = _GIT_TIMEOUT):
        """Executa git com lista de args (shell=False), captura e timeout."""
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd), shell=False, env=_clean_git_env(),
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, (proc.stdout or ""), (proc.stderr or "")

    def _assert_tracked_clean(self, repo: Path, source_branch: str) -> None:
        """Bloqueia se houver mudança RASTREADA (unstaged/staged), operação Git
        em andamento, HEAD inválido ou source_branch inexistente.
        Arquivos UNTRACKED NÃO bloqueiam (regra R4.1)."""
        # HEAD válido?
        rc, _, err = self._git(repo, ["rev-parse", "--verify", "HEAD"])
        if rc != 0:
            raise GitStateError("HEAD inválido: " + sanitize(err))
        # source_branch existe?
        rc, _, err = self._git(repo, ["rev-parse", "--verify", source_branch])
        if rc != 0:
            raise GitStateError(f"source_branch inexistente: {sanitize(source_branch)}")
        # unstaged tracked (git diff --quiet → rc 0 limpo)
        rc, _, _ = self._git(repo, ["diff", "--quiet"])
        if rc != 0:
            raise GitStateError("há alteração rastreada não-staged")
        # staged (git diff --cached --quiet)
        rc, _, _ = self._git(repo, ["diff", "--cached", "--quiet"])
        if rc != 0:
            raise GitStateError("há alteração staged")
        # merge/rebase/cherry-pick em andamento?
        rc, out, _ = self._git(repo, ["rev-parse", "--git-dir"])
        git_dir = (repo / out.strip()) if rc == 0 and out.strip() else (repo / ".git")
        for marker in _INPROGRESS:
            if (git_dir / marker).exists():
                raise GitStateError("operação Git em andamento (merge/rebase/cherry-pick)")

    def _active_branch(self, worktree: Path) -> str:
        rc, out, _ = self._git(worktree, ["rev-parse", "--abbrev-ref", "HEAD"])
        return out.strip() if rc == 0 else ""

    def _branch_exists(self, repo: Path, branch: str) -> bool:
        rc, _, _ = self._git(repo, ["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"])
        return rc == 0

    # ── create ────────────────────────────────────────────────────────────
    def create(self, task_id: str, repository_path, source_branch: str,
               project_id: str | None = None, idempotent: bool = False) -> dict:
        tid = et.validate_task_id(task_id)
        repo = self.validate_repository_path(repository_path)
        source_branch = (source_branch or "").strip()
        if not source_branch:
            raise GitStateError("source_branch vazio")
        work_branch = et.validate_work_branch(et.branch_for(tid))
        worktree_path = self.worktree_path_for(tid)
        pid = et.normalize_project_id(project_id)

        self._assert_tracked_clean(repo, source_branch)

        # branch já existente → recusa, salvo idempotência explicitamente segura
        if self._branch_exists(repo, work_branch) and not idempotent:
            raise GitStateError("work_branch já existe")

        self.worktree_root.mkdir(parents=True, exist_ok=True)
        rc, _, err = self._git(
            repo, ["worktree", "add", "-b", work_branch, str(worktree_path), source_branch]
        )
        if rc != 0:
            # não remove evidência silenciosamente; devolve erro seguro
            raise GitStateError("git worktree add falhou: " + sanitize(err))

        active = self._active_branch(worktree_path)
        if active != work_branch:
            raise GitStateError(f"branch ativa inesperada: {sanitize(active)}")
        if active in ("master", "main"):
            raise SecurityError("worktree caiu em master/main")

        return {
            "task_id": tid,
            "project_id": pid,
            "repository_path": str(repo),
            "source_branch": source_branch,
            "work_branch": work_branch,
            "worktree_path": str(worktree_path),
        }

    # ── validate existing ─────────────────────────────────────────────────
    def validate_existing(self, task_id: str) -> dict:
        wp = self.worktree_path_for(task_id)
        exists = wp.is_dir() and (wp / ".git").exists()
        active = self._active_branch(wp) if exists else ""
        return {
            "task_id": et.validate_task_id(task_id),
            "worktree_path": str(wp),
            "exists": exists,
            "active_branch": active,
            "is_expected_branch": active == et.branch_for(task_id),
        }

    # ── remove ────────────────────────────────────────────────────────────
    def remove(self, task_id: str, status: str | None = None,
               approved_cleanup: bool = False) -> dict:
        wp = self.worktree_path_for(task_id)  # reconstruído do task_id
        if not _is_within(wp, self.worktree_root):
            raise SecurityError("recusa remover path fora do worktree root")
        # preserva worktree de tarefas em falha, salvo limpeza aprovada
        if status in (et.FAILED, et.TIMED_OUT, et.REVIEW_REJECTED) and not approved_cleanup:
            raise WorktreeError("worktree preservada para auditoria (falha) — exige approved_cleanup")

        repo = self.allowed_repo_roots[0]
        rc, _, err = self._git(repo, ["worktree", "remove", "--force", str(wp)])
        removed = rc == 0
        # prune só quando seguro (após remoção ok)
        if removed:
            self._git(repo, ["worktree", "prune"])
        return {"task_id": et.validate_task_id(task_id), "removed": removed,
                "worktree_path": str(wp), "error": sanitize(err) if not removed else ""}
