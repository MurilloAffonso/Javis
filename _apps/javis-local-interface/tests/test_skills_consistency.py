from __future__ import annotations

import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = PROJECT_ROOT / "_skills"

AGENT_IDS = [
    "architect",
    "developer",
    "ux_designer",
    "qa",
    "pm",
    "po",
    "scrum",
    "analyst",
    "devops",
    "data_engineer",
    "jarvis_soul",
    "aios_master",
    "squad_creator",
    "rootcause",
    "critico",
    "advogado",
    "sintetizador",
]


@pytest.mark.parametrize("agent_id", AGENT_IDS)
def test_agent_skill_contract(agent_id: str) -> None:
    path = SKILLS_DIR / f"agente-{agent_id}.md"
    assert path.exists(), f"skill file missing: {path.relative_to(PROJECT_ROOT)}"

    content = path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{path.name} must start with frontmatter"
    assert f"agente: {agent_id}" in content, f"{path.name} must declare agente: {agent_id}"

    for section in ("IDENTIDADE", "Processo", "REGRAS"):
        assert re.search(
            rf"^#+\s+{re.escape(section)}\b",
            content,
            re.MULTILINE,
        ), f"{path.name} missing section: {section}"
