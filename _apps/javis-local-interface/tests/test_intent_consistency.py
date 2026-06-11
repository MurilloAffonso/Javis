"""Test: consistência de intents entre backend/command_router.py e config/commands.yaml.

Fonte de verdade: command_router.py (lógica real).
commands.yaml deve documentar o backend com fidelidade.
frontend/app.js é auditado informativamente — discrepâncias geram WARN, não FAIL.
"""
from __future__ import annotations
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"

_REPO_ROOT = Path(__file__).resolve().parents[1]


def check(description: str, condition: bool) -> bool:
    status = PASS if condition else FAIL
    print(f"  [{status}] {description}")
    return condition


def warn(description: str) -> None:
    print(f"  [{WARN}] {description}")


def _parse_commands_yaml(path: Path) -> dict[str, dict]:
    """Minimal parser for commands.yaml — extracts intent names and their scalar fields.

    Handles the specific two-level structure (intents > fields) without PyYAML.
    Ignores list fields (examples:) because they have no value on the same line.
    """
    intents: dict[str, dict] = {}
    current_intent: str | None = None
    in_intents = False

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        if stripped == "intents:":
            in_intents = True
            continue
        if not in_intents:
            continue
        # Intent name: exactly 2-space indent + word + colon + nothing else
        m2 = re.match(r'^  ([a-zA-Z_]+):\s*$', stripped)
        if m2:
            current_intent = m2.group(1)
            intents[current_intent] = {}
            continue
        if current_intent is None:
            continue
        # Scalar field: exactly 4-space indent + key + colon + value (non-empty)
        # List fields like "examples:" have no value → .+ won't match → safely ignored
        m4 = re.match(r'^    ([a-zA-Z_]+):\s*(.+)$', stripped)
        if m4:
            key = m4.group(1)
            raw = m4.group(2).strip().strip("\"'")
            if raw.lower() == "true":
                intents[current_intent][key] = True
            elif raw.lower() == "false":
                intents[current_intent][key] = False
            else:
                intents[current_intent][key] = raw

    return intents


def _parse_frontend_risk_intents(path: Path) -> set[str]:
    """Extracts intent keys from the RISK constant in app.js."""
    content = path.read_text(encoding="utf-8")
    # [^}]+ matches newlines in Python character classes (no DOTALL needed)
    risk_match = re.search(r'(?:const|var|let)\s+RISK\s*=\s*\{([^}]+)\}', content)
    if not risk_match:
        return set()
    block = risk_match.group(1)
    return {m.group(1) for m in re.finditer(r'(\w+)\s*:', block)}


# ─── test functions ────────────────────────────────────────────────────────────

def test_intent_sets() -> int:
    """Backend RISK_MAP e YAML devem conter os mesmos intents."""
    print("\n--- Sets de intents: backend (RISK_MAP) vs YAML ---")
    import command_router
    failures = 0

    yaml_path = _REPO_ROOT / "config" / "commands.yaml"
    ok_exists = yaml_path.exists()
    if not ok_exists:
        failures += 1
        check(f"commands.yaml existe em config/commands.yaml", False)
        return failures

    yaml_intents = _parse_commands_yaml(yaml_path)
    backend_set = set(command_router.RISK_MAP.keys())
    yaml_set = set(yaml_intents.keys())

    backend_only = backend_set - yaml_set
    yaml_only = yaml_set - backend_set

    for intent in sorted(backend_only):
        failures += 1
        check(f"intent '{intent}' do backend (RISK_MAP) está no YAML", False)

    for intent in sorted(yaml_only):
        failures += 1
        check(f"intent '{intent}' do YAML está no backend (RISK_MAP)", False)

    if not backend_only and not yaml_only:
        check(f"sets idênticos — {len(backend_set)} intents em ambos", True)

    return failures


def test_risk_levels() -> int:
    """risk_level de cada intent deve ser idêntico no backend e no YAML."""
    print("\n--- risk_level: backend vs YAML ---")
    import command_router
    failures = 0

    yaml_intents = _parse_commands_yaml(_REPO_ROOT / "config" / "commands.yaml")

    for intent, (risk_backend, _) in sorted(command_router.RISK_MAP.items()):
        yaml_entry = yaml_intents.get(intent, {})
        risk_yaml = yaml_entry.get("risk_level", "<ausente>")
        ok = risk_yaml == risk_backend
        if not ok:
            failures += 1
            print(f"    DETALHE: backend={risk_backend!r}  yaml={risk_yaml!r}")
        check(f"'{intent}' risk_level == {risk_backend!r}", ok)

    return failures


def test_requires_approval() -> int:
    """requires_approval de cada intent deve ser idêntico no backend e no YAML."""
    print("\n--- requires_approval: backend vs YAML ---")
    import command_router
    failures = 0

    yaml_intents = _parse_commands_yaml(_REPO_ROOT / "config" / "commands.yaml")

    for intent, (_, req_backend) in sorted(command_router.RISK_MAP.items()):
        yaml_entry = yaml_intents.get(intent, {})
        req_yaml = yaml_entry.get("requires_approval", "<ausente>")
        ok = req_yaml == req_backend
        if not ok:
            failures += 1
            print(f"    DETALHE: backend={req_backend!r}  yaml={req_yaml!r}")
        check(f"'{intent}' requires_approval == {req_backend}", ok)

    return failures


def test_actions() -> int:
    """action de cada intent deve ser idêntica no backend (ACTION_MAP) e no YAML."""
    print("\n--- action: backend (ACTION_MAP) vs YAML ---")
    import command_router
    failures = 0

    yaml_intents = _parse_commands_yaml(_REPO_ROOT / "config" / "commands.yaml")

    for intent, action_backend in sorted(command_router.ACTION_MAP.items()):
        yaml_entry = yaml_intents.get(intent, {})
        action_yaml = yaml_entry.get("action", "<ausente>")
        ok = action_yaml == action_backend
        if not ok:
            failures += 1
            print(f"    DETALHE: backend={action_backend!r}  yaml={action_yaml!r}")
        check(f"'{intent}' action == {action_backend!r}", ok)

    return failures


def test_frontend_audit() -> int:
    """Auditoria informativa: intents do backend presentes no frontend/app.js.

    Discrepâncias geram WARN (não FAIL). O frontend será corrigido em etapa futura.
    Retorna sempre 0 para não bloquear a suíte.
    """
    print("\n--- Auditoria frontend/app.js (informativo — não bloqueia) ---")
    import command_router

    js_path = _REPO_ROOT / "frontend" / "app.js"
    if not js_path.exists():
        warn(f"frontend/app.js não encontrado — pulando auditoria")
        return 0

    frontend_intents = _parse_frontend_risk_intents(js_path)
    backend_intents = set(command_router.RISK_MAP.keys())

    missing = backend_intents - frontend_intents
    extra = frontend_intents - backend_intents

    if missing:
        for intent in sorted(missing):
            warn(f"'{intent}' está no backend mas AUSENTE no frontend/app.js (RISK map)")
    else:
        print(f"  [INFO] frontend/app.js cobre todos os {len(backend_intents)} intents do backend")

    if extra:
        for intent in sorted(extra):
            warn(f"'{intent}' está no frontend mas AUSENTE no backend (RISK_MAP)")

    return 0  # auditoria informativa — nunca falha


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 55)
    print("Testes: consistência de intents (backend ↔ YAML ↔ frontend)")
    print("=" * 55)

    total_failures = 0
    total_failures += test_intent_sets()
    total_failures += test_risk_levels()
    total_failures += test_requires_approval()
    total_failures += test_actions()
    total_failures += test_frontend_audit()

    print("\n" + "=" * 55)
    if total_failures == 0:
        print("\033[32m✅ Todos os testes passaram.\033[0m")
    else:
        print(f"\033[31m❌ {total_failures} teste(s) falharam.\033[0m")
    print("=" * 55)
    sys.exit(total_failures)


if __name__ == "__main__":
    main()
