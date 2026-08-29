"""Ensure workflow import failures remain visible to Dagster callers.

Discovery imports each workflow independently to report every broken module,
but an import failure must prevent an incomplete asset graph from loading.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from phlo.exceptions import PhloDiscoveryError
from phlo_dagster.framework.discovery import _import_workflow_modules


@pytest.mark.parametrize(
    ("source", "exception_name", "exception_detail"),
    [
        ("def broken(:\n", "SyntaxError", "invalid syntax"),
        (
            "raise RuntimeError('import dependency unavailable')\n",
            "RuntimeError",
            "import dependency unavailable",
        ),
        (
            "def reject(_workflow):\n"
            "    raise ValueError('decorator registration rejected')\n\n"
            "@reject\n"
            "def broken():\n"
            "    pass\n",
            "ValueError",
            "decorator registration rejected",
        ),
    ],
    ids=("syntax", "import", "decorator"),
)
def test_workflow_import_failures_name_the_module_path_and_root_error(
    tmp_path: Path,
    source: str,
    exception_name: str,
    exception_detail: str,
) -> None:
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    healthy_path = workflows / "healthy.py"
    healthy_path.write_text("healthy_workflow = object()\n")
    broken_path = workflows / "broken.py"
    broken_path.write_text(source)

    try:
        with pytest.raises(PhloDiscoveryError) as exc_info:
            _import_workflow_modules(workflows)

        message = str(exc_info.value)
        assert "module=workflows.broken" in message
        assert f"path={broken_path}" in message
        assert exception_name in message
        assert exception_detail in message
        assert "workflows.healthy" in sys.modules
    finally:
        sys.modules.pop("workflows.healthy", None)
        sys.modules.pop("workflows.broken", None)
