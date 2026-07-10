"""execution_policy — política default-deny de comandos (R4.1).

Funções PURAS que validarão (na R4.2) cada comando do executor. Nada é executado
aqui. A análise é sobre argv ESTRUTURADO (lista de argumentos), não regex em
string de shell livre — e o default é NEGAR.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._sanitize import sanitize

# Metacaracteres de shell → tentativa de encadear/redirecionar comandos.
_SHELL_META = (";", "&&", "||", "|", "`", "$(", "${", ">", "<", "\n", "\r", "&")

# Programas permitidos (basename, minúsculo). Tudo fora disto é negado.
_ALLOWED_PROGRAMS = {"git", "python", "python3", "pytest", "py"}

# Subcomandos git permitidos.
_GIT_ALLOWED_SUBS = {"status", "diff", "log", "show", "add", "commit"}
# Subcomandos git explicitamente perigosos.
_GIT_DENIED_SUBS = {"push", "fetch", "pull", "remote", "reset", "clean",
                    "checkout", "switch", "rebase", "merge", "cherry-pick",
                    "config", "submodule", "worktree"}

# Fragmentos de nome que indicam segredo/credencial.
_SENSITIVE_NAME = ("token", "secret", "credential", "password", "passwd",
                   "apikey", "api_key", "chave")


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""


def _deny(reason: str) -> PolicyDecision:
    return PolicyDecision(False, sanitize(reason, 200))


_ALLOW = PolicyDecision(True, "")


def _is_flag(arg: str) -> bool:
    return arg.startswith("-")


def _has_force(args: list[str]) -> bool:
    return any(a in ("-f", "--force") or a.startswith("--force") for a in args)


def _sensitive_name(name: str) -> bool:
    low = name.lower()
    if low == ".env" or low.startswith(".env."):
        return True
    return any(frag in low for frag in _SENSITIVE_NAME)


def validate_path(path: str, worktree_path) -> PolicyDecision:
    """Nega paths fora da worktree e nomes sensíveis (.env/token/chave/...)."""
    if not path or _is_flag(path):
        return _deny("path vazio ou flag no lugar de path")
    root = Path(worktree_path).resolve()
    # componente sensível em qualquer nível
    for part in Path(path).parts:
        if _sensitive_name(part):
            return _deny("path aponta para arquivo sensível (.env/token/chave)")
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else (root / candidate)).resolve()
    if resolved != root and root not in resolved.parents:
        return _deny("path fora da worktree")
    return _ALLOW


def _validate_path_args(args: list[str], worktree_path) -> PolicyDecision:
    """Valida cada arg que parece path (ignora flags). Aceita node-id de pytest
    (arquivo::teste) validando só a parte do arquivo."""
    for a in args:
        if _is_flag(a):
            continue
        file_part = a.split("::", 1)[0]
        if not file_part:
            continue
        dec = validate_path(file_part, worktree_path)
        if not dec.allowed:
            return dec
    return _ALLOW


def _check_git(args: list[str], worktree_path) -> PolicyDecision:
    if not args:
        return _deny("git sem subcomando")
    sub = args[0]
    rest = args[1:]
    if sub in _GIT_DENIED_SUBS:
        return _deny(f"git {sub} bloqueado")
    if sub not in _GIT_ALLOWED_SUBS:
        return _deny(f"git {sub} desconhecido (default-deny)")
    if _has_force(rest):
        return _deny("flag force bloqueada")
    if sub == "log":
        # exige limite explícito (-n N, --max-count, -<n>)
        has_limit = any(
            a == "-n" or a.startswith("--max-count") or (a.startswith("-") and a[1:].isdigit())
            for a in rest
        )
        if not has_limit:
            return _deny("git log exige limite explícito")
        return _ALLOW
    if sub == "add":
        paths = [a for a in rest if not _is_flag(a)]
        if not paths or any(a in (".", "-A", "--all", "*", ":/") for a in rest):
            return _deny("git add exige arquivos explícitos dentro da worktree")
        return _validate_path_args(rest, worktree_path)
    if sub == "commit":
        # commit local na work_branch; sem paths a validar (mensagem via -m)
        return _ALLOW
    # status / diff / show → permitidos; valida paths se houver
    return _validate_path_args(rest, worktree_path)


def _check_python(args: list[str], worktree_path) -> PolicyDecision:
    # Só as formas -m py_compile / -m pytest são permitidas.
    if len(args) >= 2 and args[0] == "-m":
        module = args[1]
        if module == "pip":
            return _deny("instalação de dependência bloqueada")
        if module in ("py_compile", "pytest"):
            return _validate_path_args(args[2:], worktree_path)
        return _deny(f"python -m {module} não permitido (default-deny)")
    return _deny("python permitido só como -m py_compile / -m pytest")


def check_command(argv, worktree_path) -> PolicyDecision:
    """Valida um comando (lista de argumentos) contra a worktree. Default-deny."""
    if not isinstance(argv, (list, tuple)) or not argv:
        return _deny("comando deve ser lista de argumentos não-vazia")
    argv = [str(a) for a in argv]
    # sem string de shell livre / encadeamento
    for tok in argv:
        if any(meta in tok for meta in _SHELL_META):
            return _deny("metacaractere de shell / encadeamento bloqueado")

    program = Path(argv[0]).name.lower()
    if program.endswith(".exe"):
        program = program[:-4]
    if program not in _ALLOWED_PROGRAMS:
        return _deny(f"programa não permitido: {program}")

    rest = argv[1:]
    if program == "git":
        return _check_git(rest, worktree_path)
    if program in ("python", "python3", "py"):
        return _check_python(rest, worktree_path)
    if program == "pytest":
        return _validate_path_args(rest, worktree_path)
    return _deny("comando desconhecido")


def explain_denial(argv, worktree_path) -> str:
    """Motivo sanitizado da negação (ou '' se permitido)."""
    dec = check_command(argv, worktree_path)
    return "" if dec.allowed else sanitize(dec.reason, 200)
