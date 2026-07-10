from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from execution.executor_adapter import AdapterRequest, ClaudeCodeAdapter, CodexAdapter  # noqa: E402
from execution import process_utils  # noqa: E402
from execution.worktree_manager import JAVIS_ROOT  # noqa: E402


CORE = "javes-core"
TID = "exec_aaaaaaaa"


def _worktree(tmp_path):
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / ".git").write_text("gitdir: fake", encoding="utf-8")
    prompt = wt / "prompt.txt"
    prompt.write_text("objective", encoding="utf-8")
    return wt, prompt


def _request(wt: Path, prompt: Path, executor: str = "claude") -> AdapterRequest:
    return AdapterRequest(
        task_id=TID,
        project_id=CORE,
        objective="obj",
        worktree_path=str(wt),
        timeout_seconds=10,
        prompt_path=str(prompt),
        executor=executor,
    )


def test_adapter_usa_cwd_exato_da_worktree(tmp_path):
    wt, prompt = _worktree(tmp_path)
    captured = {}

    def runner(argv, **kwargs):
        captured["argv"] = argv
        captured["cwd"] = kwargs["cwd"]
        return process_utils.ProcessResult(0, "success", "", "", False, 1, "ok")

    result = ClaudeCodeAdapter(runner=runner).run(_request(wt, prompt))
    assert result.status == "success"
    assert Path(captured["cwd"]) == wt.resolve()


def test_adapter_recusa_repo_principal():
    prompt = JAVIS_ROOT / "prompt.txt"
    result = ClaudeCodeAdapter().run(_request(JAVIS_ROOT, prompt))
    assert result.status == "blocked"
    assert "repo principal" in result.stderr or "worktree" in result.stderr


def test_claude_nao_recebe_bash_nem_add_dir_do_repo_principal(tmp_path):
    wt, prompt = _worktree(tmp_path)
    captured = {}

    def runner(argv, **kwargs):
        captured["argv"] = argv
        return process_utils.ProcessResult(0, "success", "", "", False, 1, "ok")

    ClaudeCodeAdapter(runner=runner).run(_request(wt, prompt))
    joined = " ".join(captured["argv"])
    assert "Bash" not in joined
    assert "--add-dir" not in captured["argv"]
    assert str(JAVIS_ROOT) not in captured["argv"]
    assert "Read,Edit,Write" in joined


def test_codex_sem_sandbox_seguro_falha_fechado(tmp_path):
    wt, prompt = _worktree(tmp_path)
    result = CodexAdapter(help_text=None).run(_request(wt, prompt, executor="codex"))
    assert result.status == "blocked"
    assert "secure_codex_sandbox_unavailable" in result.stderr


def test_codex_com_sandbox_verificado_usa_workspace_write(tmp_path):
    wt, prompt = _worktree(tmp_path)
    captured = {}

    def runner(argv, **kwargs):
        captured["argv"] = argv
        captured["cwd"] = kwargs["cwd"]
        return process_utils.ProcessResult(0, "success", "", "", False, 1, "ok")

    result = CodexAdapter(
        help_text="codex exec --sandbox <MODE> workspace-write",
        runner=runner,
    ).run(_request(wt, prompt, executor="codex"))
    assert result.status == "success"
    assert captured["argv"][0:4] == ["codex", "exec", "--sandbox", "workspace-write"]
    assert Path(captured["cwd"]) == wt.resolve()
