"""R5.1 — a aprovação de uma tarefa de navegador é amarrada ao conteúdo.

Antes desta fase, o gate de `/browser/run` validava action/route/project/uso
único, mas nunca o texto da tarefa. Uma aprovação para "ler a previsão do tempo"
podia ser consumida por "entrar no Instagram e postar" — o `metadata.task` era
gravado e nunca reconferido. Estes testes provam que agora não dá: trocar a
tarefa invalida o approval, como o `spec_hash` faz no executor.
"""
from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

TEST_TOKEN = "test-local-token"
CORE = "javes-core"


def _server(monkeypatch, tmp_path):
    monkeypatch.setenv("JAVIS_SKIP_DOTENV", "1")
    monkeypatch.setenv("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    monkeypatch.setenv("JAVIS_ENABLE_BROWSER", "true")
    monkeypatch.setenv("JAVES_LOCAL_TOKEN", TEST_TOKEN)
    server = importlib.import_module("server")
    import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "javis.db")
    monkeypatch.setattr(db, "_initialized", False)
    db.init_db()
    return server


def _json(resp):
    return json.loads(resp.body.decode("utf-8"))


def _stub_browser_agent(monkeypatch, ran: list):
    async def run_task(task, max_steps=12):
        ran.append(task)
        return {"status": "ok", "result": "stub", "task": task}

    monkeypatch.setitem(sys.modules, "browser_agent",
                        SimpleNamespace(run_task=run_task, available=lambda: True))


def _call(server, task, approval_id=None, approved=False, project_id=CORE):
    return _json(asyncio.run(server.browser_run(
        server.BrowserRequest(task=task, project_id=project_id,
                              approved=approved, approval_id=approval_id),
        x_javes_local_token=TEST_TOKEN,
    )))


def _approve_for(server, repo, task, project_id=CORE):
    """Cria e aprova um approval amarrado ao hash da tarefa — como o humano faz
    quando lê a tarefa e clica em aprovar."""
    task_hash = server._browser_task_hash(task, project_id)
    approval_id = repo.approvals.add(
        "browser task", kind="route_gate", project_id=project_id,
        action="browser.run", route="/browser/run", risk_level="high",
        spec_hash=task_hash,
    )
    repo.approvals.decide(approval_id, True, approved_by="test")
    return approval_id


# ── nível de unidade: o predicado do repositório ──────────────────────────
def test_valid_for_action_exige_hash_igual_quando_pedido(monkeypatch, tmp_path):
    _server(monkeypatch, tmp_path)
    import repositories as repo

    approval_id = repo.approvals.add(
        "x", kind="route_gate", project_id=CORE, action="browser.run",
        route="/browser/run", spec_hash="hash-da-tarefa-A",
    )
    repo.approvals.decide(approval_id, True, approved_by="test")
    approval = repo.approvals.get(approval_id)

    ok = repo.approvals.valid_for_action(approval, "browser.run", route="/browser/run",
                                         project_id=CORE, payload_hash="hash-da-tarefa-A")
    wrong = repo.approvals.valid_for_action(approval, "browser.run", route="/browser/run",
                                            project_id=CORE, payload_hash="hash-da-tarefa-B")
    assert ok is True
    assert wrong is False


def test_sem_payload_hash_comportamento_antigo_preservado(monkeypatch, tmp_path):
    """Retrocompatibilidade: quem não passa payload_hash (todas as outras rotas)
    continua validando exatamente como antes."""
    _server(monkeypatch, tmp_path)
    import repositories as repo

    approval_id = repo.approvals.add(
        "x", kind="route_gate", project_id=CORE, action="wa.save_voice",
        route="/wa/save-voice",
    )
    repo.approvals.decide(approval_id, True, approved_by="test")
    approval = repo.approvals.get(approval_id)

    assert repo.approvals.valid_for_action(
        approval, "wa.save_voice", route="/wa/save-voice", project_id=CORE) is True


# ── nível de rota: a propriedade que importa ──────────────────────────────
def test_aprovar_tarefa_A_nao_autoriza_tarefa_B(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo
    ran: list = []
    _stub_browser_agent(monkeypatch, ran)

    approval_id = _approve_for(server, repo, "ler a previsão do tempo em weather.com")

    # a MESMA aprovação, usada para uma tarefa diferente, é recusada
    hijack = _call(server, "entrar no Instagram e postar uma foto", approval_id=approval_id)

    assert hijack["status"] == "approval_required"
    assert ran == []  # o agente de navegador NUNCA foi chamado
    # e a aprovação segue intacta para seu uso legítimo (não foi consumida)
    assert repo.approvals.get(approval_id)["consumed_at"] is None


def test_aprovacao_vale_para_a_tarefa_exata_que_foi_aprovada(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo
    ran: list = []
    _stub_browser_agent(monkeypatch, ran)

    task = "ler a previsão do tempo em weather.com"
    approval_id = _approve_for(server, repo, task)

    out = _call(server, task, approval_id=approval_id)

    assert out["status"] == "ok"
    assert ran == [task]
    assert repo.approvals.get(approval_id)["consumed_at"] is not None  # single-use


def test_espacos_diferentes_nao_invalidam_a_aprovacao(monkeypatch, tmp_path):
    """O hash normaliza espaços em branco: reformatar a mesma tarefa não deveria
    forçar uma reaprovação, só mudança real de conteúdo."""
    server = _server(monkeypatch, tmp_path)
    import repositories as repo
    ran: list = []
    _stub_browser_agent(monkeypatch, ran)

    approval_id = _approve_for(server, repo, "ler   a  previsão\tdo tempo")
    out = _call(server, "ler a previsão do tempo", approval_id=approval_id)

    assert out["status"] == "ok"
    assert len(ran) == 1


def test_sem_aprovacao_a_rota_pede_aprovacao_e_nao_executa(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    import repositories as repo  # noqa: F401
    ran: list = []
    _stub_browser_agent(monkeypatch, ran)

    out = _call(server, "qualquer tarefa", approved=True)  # 'approved=True' não basta

    assert out["status"] == "approval_required"
    assert ran == []


def test_hash_inclui_projeto_nao_vaza_entre_escopos(monkeypatch, tmp_path):
    server = _server(monkeypatch, tmp_path)
    a = server._browser_task_hash("mesma tarefa", "javes-core")
    b = server._browser_task_hash("mesma tarefa", "cerebro-jampa")
    assert a != b
