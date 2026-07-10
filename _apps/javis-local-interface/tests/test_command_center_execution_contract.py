from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXEC_JS = ROOT / "_apps" / "javis-local-interface" / "frontend" / "command-center" / "js" / "views" / "exec.js"


def _src() -> str:
    return EXEC_JS.read_text(encoding="utf-8")


def test_frontend_usa_task_id_e_project_id():
    src = _src()

    assert "execution/tasks/${encodeURIComponent(task.task_id)}" in src
    assert "project_id: task.project_id" in src
    assert "project_id=${encodeURIComponent(task.project_id)}" in src


def test_frontend_nao_envia_paths_arbitrarios():
    src = _src()

    assert "repository_path" not in src
    assert "worktree_path" not in src


def test_botao_executar_desabilitado_com_flag_false():
    src = _src()

    assert "supervised_execution_enabled" in src
    assert "Executar" in src
    assert "!_supervisedEnabled" in src


def test_resultados_sao_sanitizados_sem_stdout_stderr_bruto():
    src = _src()

    assert "/result?project_id=" in src
    assert "Resumo sanitizado" in src
    assert "stdout" not in src.lower()
    assert "stderr" not in src.lower()
