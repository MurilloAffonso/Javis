from __future__ import annotations

from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def _read(rel: str) -> str:
    return (FRONTEND / rel).read_text(encoding="utf-8")


def test_command_center_exports_project_scope_and_local_auth_header():
    app = _read("command-center/app.js")

    assert 'const CORE_PROJECT_ID = "javes-core"' in app
    assert 'const VP_PROJECT_ID = "project:cerebro-jampa"' in app
    assert 'const LOCAL_TOKEN_HEADER = "X-Javes-Local-Token"' in app
    assert "function withProjectId" in app
    assert "function withLocalAuth" in app


def test_operation_view_sends_project_id_for_task_mutations():
    op = _read("command-center/js/views/operacao.js")

    assert "withProjectId" in op
    assert "run-studio?project_id=project:cerebro-jampa" in op
    assert "prepare-distribution?project_id=project:cerebro-jampa" in op
    assert "status?project_id=project:cerebro-jampa" in op
    assert "complete?project_id=project:cerebro-jampa" in op


def test_vempassear_views_scope_vp_jampa_calls():
    modern = _read("command-center/js/views/vempassear.js")
    legacy = _read("vempassear.js")

    assert "const vpUrl = (path) => withProjectId" in modern
    assert 'vpUrl("jampa/responder-lead")' in modern
    assert 'vpUrl("vp/agents/run")' in modern
    assert 'VP_PROJECT_ID = "project:cerebro-jampa"' in legacy
    assert "function scopedPath" in legacy


def test_content_and_wa_views_send_project_scope():
    conteudo = _read("command-center/js/views/conteudo.js")
    treino = _read("command-center/js/views/treino.js")
    chat = _read("command-center/js/views/chat.js")
    voice = _read("command-center/js/voice.js")
    tarefas = _read("command-center/js/views/tarefas.js")

    assert 'project_id: projectId' in conteudo
    assert 'const projectId = _projeto === "vempassear" ? VP_PROJECT_ID : CORE_PROJECT_ID' in conteudo
    assert 'project_id: CORE_PROJECT_ID' in chat
    assert 'project_id: CORE_PROJECT_ID' in voice
    assert 'project_id: CORE_PROJECT_ID' in tarefas
    assert 'project_id: CORE_PROJECT_ID' in treino
    assert "withProjectId(BACKEND + \"wa/analyze\")" in treino
    assert "withProjectId(BACKEND + \"wa/save-voice\")" in treino
