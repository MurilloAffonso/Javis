"""Test-suite defaults for legacy behavior.

Production/runtime defaults stay safe in safe_config.py. The existing tests were
written before R1 and exercise enabled adapters/actions with monkeypatches.
"""
from __future__ import annotations

import os


def pytest_configure():
    os.environ.setdefault("JAVIS_SKIP_DOTENV", "1")
    os.environ.setdefault("JAVIS_ENABLE_EXTERNAL_ADAPTERS", "true")
    os.environ.setdefault("JAVIS_ENABLE_BROWSER", "true")
    os.environ.setdefault("JAVIS_ENABLE_LOCAL_ACTIONS", "true")
    os.environ.setdefault("JAVIS_ENABLE_VP_EFFECTS", "true")
