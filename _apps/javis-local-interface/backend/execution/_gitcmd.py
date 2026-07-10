"""Runner git mínimo com ambiente limpo (R4.2A).

Espelha a proteção do worktree_manager: lista de argumentos (shell=False),
timeout, captura de saída e remoção das variáveis GIT_* de localização (que um
git hook em execução exporta e apontariam para OUTRO repositório).
"""
from __future__ import annotations

import os
import subprocess

_GIT_LOCATION_ENV = (
    "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY", "GIT_NAMESPACE", "GIT_PREFIX",
)
_GIT_TIMEOUT = 30


def clean_git_env() -> dict:
    env = dict(os.environ)
    for key in _GIT_LOCATION_ENV:
        env.pop(key, None)
    return env


def run_git(cwd, args: list[str], timeout: int = _GIT_TIMEOUT) -> tuple[int, str, str]:
    """Executa `git <args>` em cwd. Retorna (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), shell=False, env=clean_git_env(),
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, (proc.stdout or ""), (proc.stderr or "")
