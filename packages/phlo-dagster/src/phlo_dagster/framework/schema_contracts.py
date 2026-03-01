"""Schema-contract refresh integration for Dagster materialization flows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def maybe_refresh_contracts(workflows_path: Path, logger: Any) -> None:
    """Refresh schema contracts when explicitly enabled via env vars."""
    enabled = os.getenv("PHLO_AUTO_REFRESH_CONTRACTS", "").strip().lower()
    if enabled not in {"1", "true", "yes"}:
        return

    selection = os.getenv("PHLO_CONTRACT_REFRESH_SELECTION")

    try:
        from phlo.cli.commands.schema_migrate import refresh_contracts_for_selection
    except Exception:
        logger.warning(
            "schema_contract_refresh_unavailable",
            workflows_path=str(workflows_path),
            selection=selection,
            exc_info=True,
        )
        return

    try:
        refreshed_count = refresh_contracts_for_selection(selection=selection, force=True)
    except Exception:
        logger.warning(
            "schema_contract_refresh_failed",
            workflows_path=str(workflows_path),
            selection=selection,
            exc_info=True,
        )
        return

    logger.info(
        "schema_contract_refresh_completed",
        workflows_path=str(workflows_path),
        selection=selection,
        refreshed_count=refreshed_count,
    )
