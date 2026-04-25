"""Pytest wrapper for the live phlo-mcp stack smoke script."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_live_stack_smoke_script() -> None:
    if os.environ.get("PHLO_MCP_STACK_SMOKE", "").lower() not in {"1", "true", "yes", "on"}:
        pytest.skip("set PHLO_MCP_STACK_SMOKE=1 to run the live stack smoke test")

    script = Path(__file__).with_name("smoke_stack.py")
    result = subprocess.run(
        [sys.executable, str(script)],
        text=True,
        capture_output=True,
        timeout=600,
    )

    assert result.returncode == 0, result.stdout + result.stderr
