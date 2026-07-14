"""R4.5 — Modo Madrugada, exercitado em Git/SQLite/worktrees temporários.

O ponto destes testes não é o happy path: é provar que a Madrugada **não
consegue** fazer o que não deve. Ela roda uma task que um humano já aprovou,
para em `awaiting_review` e deixa o merge para a revisão da manhã.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "_apps" / "javis-local-interface" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import db  # noqa: E402
import repositories as repo  # noqa: E402
from execution import execution_task as et  # noqa: E402
from execution._gitcmd import clean_git_env  # noqa: E402
from execution.night_mode import ARM_PHRASE, NightMode, NightWindow  # noqa: E402
from execution.process_utils import ProcessResult  # noqa: E402
from execution.programming_task_admission import prepare_file  # noqa: E402
from execution.programming_task_flow import (  # noqa: E402
    APPROVE_START_PHRASE,
    ProgrammingTaskFlow,
)
from execution.project_execution_registry import ProjectExecutionRegistry  # noqa: E402
from execution.result_collector import ResultCollector  # noqa: E402
from execution.worktree_manager import WorktreeManager  # noqa: E402


CORE = "javes-core"
MIDNIGHT = datetime(2026, 7, 15, 2, 0, tzinfo=timezone.utc)  # 02h — dentro da janela
NOON = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)     # 12h — fora da janela


def _git(path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=path, shell=False, env=clean_git_env(), check=True,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _init_repo(path: Path) -> None:
    path.mkdir()
    _git(path, "init", "-b", "master")
    _git(path, "config", "user.email", "tests@javes.local")
    _git(path, "config", "user.name", "Javes Tests")
    (path / "docs").mkdir()
    (path / "docs" / "base.md").write_text("# Base\n", encoding="utf-8")
    _git(path, "add", "--", "docs/base.md")
    _git(path, "commit", "-m", "initial")


def _spec(**overrides) -> dict:
    data = {
        "schema_version": 1,
        "project_id": CORE,
        "title": "Atualiza documentação controlada",
        "objective": "Adicionar documentação pequena pelo fluxo supervisionado.",
        "executor": "claude",
        "allowed_paths": ["docs/"],
        "test_profile": "docs_only",
        "limits": {"max_duration_seconds": 300, "max_changed_files": 5,
                   "max_diff_lines": 300},
    }
    data.update(overrides)
    return data


class FakeAdapter:
    """Escreve um arquivo dentro de allowed_paths, como um agente bem-comportado."""

    def __init__(self, name: str = "real.md"):
        self.name = name
        self.calls = 0

    def run(self, request):
        self.calls += 1
        target = Path(request.worktree_path) / "docs" / self.name
        target.write_text(f"# {self.name}\n", encoding="utf-8")
        return ProcessResult(0, "success", "ok", "", False, 5, "fake")


@pytest.fixture()
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    for flag in ("JAVIS_ENABLE_NIGHT_MODE", "JAVIS_ENABLE_SUPERVISED_EXEC",
                 "JAVIS_ENABLE_REAL_PROGRAMMING_TASKS"):
        monkeypatch.delenv(flag, raising=False)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    db._initialized = False
    db.init_db()
    main = tmp_path / "repo"
    _init_repo(main)
    return {
        "tmp": tmp_path,
        "monkeypatch": monkeypatch,
        "registry": ProjectExecutionRegistry(main),
        "manager": WorktreeManager(allowed_repo_roots=[main],
                                   worktree_root=tmp_path / "worktrees"),
        "collector": ResultCollector(results_root=tmp_path / "results"),
        "adapter": FakeAdapter(),
    }


def _flow(env) -> ProgrammingTaskFlow:
    adapter = env["adapter"]
    return ProgrammingTaskFlow(
        registry=env["registry"], worktree_manager=env["manager"],
        result_collector=env["collector"],
        adapters={"claude": adapter, "codex": adapter},
    )


def _night(env, *, now=MIDNIGHT, window=NightWindow(), flow=None) -> NightMode:
    return NightMode(
        flow=flow if flow is not None else _flow(env),
        window=window,
        now=lambda: now,
        kill_switch=env["tmp"] / "MADRUGADA.OFF",
        log_dir=env["tmp"] / "night_logs",
    )


def _all_flags_on(env) -> None:
    for flag in ("JAVIS_ENABLE_NIGHT_MODE", "JAVIS_ENABLE_SUPERVISED_EXEC",
                 "JAVIS_ENABLE_REAL_PROGRAMMING_TASKS"):
        env["monkeypatch"].setenv(flag, "true")


def _prepared(env, spec=None, name="spec.json") -> dict:
    env["monkeypatch"].setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    path = env["tmp"] / name
    path.write_text(json.dumps(spec or _spec(), ensure_ascii=False), encoding="utf-8")
    return prepare_file(path, registry=env["registry"])


def _approved_by_human(env, flow) -> dict:
    """A task chega em `approved` SÓ pelo caminho humano: approve_start com a
    frase exata, consumindo o approval single-use."""
    prepared = _prepared(env)
    out = flow.approve_start(prepared["task_id"], prepared["approval_id"],
                             APPROVE_START_PHRASE)
    assert out["status"] == et.APPROVED, out
    return prepared


# ── default-deny ──────────────────────────────────────────────────────────
def test_madrugada_desligada_por_padrao(env):
    assert _night(env).run(ARM_PHRASE) == {"status": "blocked",
                                           "reason": "night_mode_disabled"}


def test_madrugada_exige_os_tres_flags(env):
    monkeypatch = env["monkeypatch"]
    night = _night(env)

    monkeypatch.setenv("JAVIS_ENABLE_NIGHT_MODE", "true")
    assert night.run(ARM_PHRASE)["reason"] == "supervised_execution_disabled"

    monkeypatch.setenv("JAVIS_ENABLE_SUPERVISED_EXEC", "true")
    assert night.run(ARM_PHRASE)["reason"] == "real_programming_tasks_disabled"

    monkeypatch.setenv("JAVIS_ENABLE_REAL_PROGRAMMING_TASKS", "true")
    # os três ligados: passa das flags e só então esbarra na ausência de task
    assert night.run(ARM_PHRASE)["reason"] == "no_approved_task"


def test_frase_de_armar_e_obrigatoria_e_vem_antes_de_tudo(env):
    _all_flags_on(env)
    flow = _flow(env)
    _approved_by_human(env, flow)
    out = _night(env, flow=flow).run("armar madrugada")  # caixa errada
    assert out == {"status": "blocked", "reason": "confirmation_phrase_required"}
    assert env["adapter"].calls == 0


# ── janela e kill switch ──────────────────────────────────────────────────
def test_fora_da_janela_nao_roda(env):
    _all_flags_on(env)
    flow = _flow(env)
    _approved_by_human(env, flow)
    out = _night(env, now=NOON, flow=flow).run(ARM_PHRASE)
    assert out == {"status": "blocked", "reason": "outside_night_window"}
    assert env["adapter"].calls == 0


def test_janela_suporta_virada_de_meia_noite():
    window = NightWindow(start_hour=22, end_hour=6)
    at = lambda hour: datetime(2026, 7, 15, hour, 0, tzinfo=timezone.utc)  # noqa: E731
    assert window.contains(at(23)) and window.contains(at(2))
    assert not window.contains(at(7)) and not window.contains(at(21))


def test_kill_switch_impede_a_noite_inteira(env):
    _all_flags_on(env)
    flow = _flow(env)
    _approved_by_human(env, flow)
    night = _night(env, flow=flow)
    night.kill_switch.write_text("off", encoding="utf-8")

    assert night.run(ARM_PHRASE) == {"status": "blocked", "reason": "kill_switch_active"}
    assert night.preflight()["kill_switch_active"] is True
    assert env["adapter"].calls == 0


# ── o que a Madrugada pode ver ────────────────────────────────────────────
def test_task_nao_aprovada_por_humano_e_invisivel_para_a_madrugada(env):
    """A propriedade central: sem `approve_start`, a task fica em
    `pending_approval` e a Madrugada não tem como sequer enxergá-la."""
    _all_flags_on(env)
    prepared = _prepared(env)
    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    assert task["status"] == et.PENDING_APPROVAL

    night = _night(env)
    assert night.approved_tasks() == []
    assert night.run(ARM_PHRASE) == {"status": "blocked", "reason": "no_approved_task"}
    assert env["adapter"].calls == 0
    # e a task continua intocada, esperando o humano
    assert repo.execution_tasks.get(prepared["task_id"], CORE)["status"] == et.PENDING_APPROVAL


def test_admissao_ja_impede_uma_segunda_task_enquanto_a_primeira_vive(env):
    """A invariante de raio de explosão vem de antes da Madrugada: enquanto uma
    task real estiver viva (inclusive parada em `awaiting_review`), a admissão
    recusa a próxima. É por isso que a Madrugada roda uma por noite."""
    _all_flags_on(env)
    flow = _flow(env)
    _approved_by_human(env, flow)

    segunda = _prepared(env, _spec(title="Segunda tarefa controlada"), name="spec2.json")

    assert segunda == {"status": "blocked", "reason": "active_programming_task_exists",
                       "project_id": CORE}


def test_se_houver_duas_aprovadas_madrugada_recusa_em_vez_de_escolher(env):
    """Defesa em profundidade: a admissão já impede este estado, mas se ele
    existisse, a Madrugada recusaria em vez de escolher sozinha qual task roda —
    ambas sairiam do mesmo commit e a segunda seria inmergeável."""
    _all_flags_on(env)
    flow = _flow(env)
    _approved_by_human(env, flow)

    intruder = f"exec_{'b' * 16}"
    repo.execution_tasks.create(
        task_id=intruder, project_id=CORE, executor="claude", objective="intrusa",
        repository_path=str(env["tmp"] / "repo"), source_branch="master",
        work_branch=et.branch_for(intruder), worktree_path="",
        status=et.APPROVED, approval_id=9999,
    )

    night = _night(env, flow=flow)
    assert len(night.approved_tasks()) == 2
    assert night.run(ARM_PHRASE) == {"status": "blocked",
                                     "reason": "multiple_approved_tasks"}
    assert env["adapter"].calls == 0


# ── execução real ─────────────────────────────────────────────────────────
def test_madrugada_executa_task_aprovada_e_para_em_awaiting_review(env):
    _all_flags_on(env)
    flow = _flow(env)
    prepared = _approved_by_human(env, flow)

    out = _night(env, flow=flow).run(ARM_PHRASE)

    assert out["status"] == "ok"
    assert out["task_id"] == prepared["task_id"]
    assert out["task_status"] == et.AWAITING_REVIEW, out
    assert env["adapter"].calls == 1
    assert repo.execution_tasks.get(prepared["task_id"], CORE)["status"] == et.AWAITING_REVIEW


def test_madrugada_pede_merge_mas_nao_aprova_nem_mergeia(env):
    """O teste que mais importa: depois da noite inteira, o merge continua sendo
    uma decisão humana. O approval existe, mas está PENDING e não consumido; a
    task NÃO avançou para approved_for_merge nem merged; o master não se moveu."""
    _all_flags_on(env)
    flow = _flow(env)
    prepared = _approved_by_human(env, flow)
    main = env["tmp"] / "repo"
    master_before = _git(main, "rev-parse", "master").stdout.strip()

    out = _night(env, flow=flow).run(ARM_PHRASE)

    merge_approval = repo.approvals.get(out["merge_approval_id"])
    assert merge_approval["action"] == "execution.merge"
    assert merge_approval["status"] == "pending"
    assert not merge_approval["consumed_at"]

    task = repo.execution_tasks.get(prepared["task_id"], CORE)
    assert task["status"] == et.AWAITING_REVIEW
    assert task["status"] not in {et.APPROVED_FOR_MERGE, et.MERGED, et.COMPLETED}
    assert task["merge_approval_id"] is None

    # o master do repositório real não andou um commit sequer
    assert _git(main, "rev-parse", "master").stdout.strip() == master_before


def test_noite_registra_relatorio_append_only(env):
    _all_flags_on(env)
    flow = _flow(env)
    _approved_by_human(env, flow)
    night = _night(env, flow=flow)

    night.run(ARM_PHRASE)
    log = night.log_dir / f"{MIDNIGHT.strftime('%Y-%m-%d')}_madrugada.jsonl"
    first = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(first) == 1
    assert json.loads(first[0])["task_status"] == et.AWAITING_REVIEW

    night.run(ARM_PHRASE)  # segunda noite: já não há task aprovada, mas nada é sobrescrito
    assert log.read_text(encoding="utf-8").strip().splitlines()[0] == first[0]


def test_falha_do_agente_nao_estoura_a_noite(env):
    """Um agente que explode vira falha registrada, não exceção subindo pra CLI."""
    _all_flags_on(env)

    class Exploding:
        calls = 0

        def run(self, request):
            Exploding.calls += 1
            raise RuntimeError("adapter caiu")

    adapter = Exploding()
    flow = ProgrammingTaskFlow(
        registry=env["registry"], worktree_manager=env["manager"],
        result_collector=env["collector"],
        adapters={"claude": adapter, "codex": adapter},
    )
    prepared = _approved_by_human(env, flow)

    out = _night(env, flow=flow).run(ARM_PHRASE)

    assert out["status"] == "ok"
    assert out["task_status"] == et.FAILED
    assert out["merge_approval_id"] is None
    assert repo.execution_tasks.get(prepared["task_id"], CORE)["status"] == et.FAILED


def test_preflight_nao_tem_efeito_colateral(env):
    _all_flags_on(env)
    flow = _flow(env)
    prepared = _approved_by_human(env, flow)
    night = _night(env, flow=flow)

    report = night.preflight()

    assert report["status"] == "ready"
    assert report["task_id"] == prepared["task_id"]
    assert report["inside_window"] is True
    assert env["adapter"].calls == 0
    assert repo.execution_tasks.get(prepared["task_id"], CORE)["status"] == et.APPROVED
