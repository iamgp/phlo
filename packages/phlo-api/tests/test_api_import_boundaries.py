"""Import boundary tests for phlo-api optional integrations."""

from __future__ import annotations

import importlib
import sys


def test_phlo_api_main_import_does_not_load_phlo_observatory() -> None:
    """phlo-api should load without importing the Observatory package."""
    for name in list(sys.modules):
        if name.startswith("phlo_observatory"):
            sys.modules.pop(name, None)
    sys.modules.pop("phlo_api.main", None)

    importlib.import_module("phlo_api.main")

    assert not any(name.startswith("phlo_observatory") for name in sys.modules)
