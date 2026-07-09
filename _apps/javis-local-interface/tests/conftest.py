"""Test-suite defaults for legacy behavior.

Production/runtime defaults stay safe in safe_config.py. The existing tests were
written before R1 and exercise enabled adapters/actions with monkeypatches.
"""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PYTEST_TMP_ROOT = ROOT / "_tmp" / "pytest"


def pytest_configure():
    os.environ.setdefault("JAVIS_SKIP_DOTENV", "1")
    os.environ.setdefault("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    os.environ.setdefault("JAVIS_ENABLE_BROWSER", "true")
    os.environ.setdefault("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    os.environ.setdefault("JAVIS_ENABLE_VP_EFFECTS", "true")
    os.environ.setdefault("JAVES_LOCAL_TOKEN", "test-local-token")
    PYTEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    for name in ("TMPDIR", "TEMP", "TMP"):
        os.environ.setdefault(name, str(PYTEST_TMP_ROOT))


@pytest.fixture
def tmp_path():
    path = PYTEST_TMP_ROOT / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
