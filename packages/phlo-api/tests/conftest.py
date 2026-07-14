"""Test-module import path for API-local helpers."""

from __future__ import annotations

import sys
from pathlib import Path

TEST_DIR = str(Path(__file__).parent)
if TEST_DIR not in sys.path:
    sys.path.insert(0, TEST_DIR)
