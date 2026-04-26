"""Data ingestion public API for Phlo.

This module provides the primary interface for data ingestion operations in Phlo.
It exports the main decorator and utility functions for defining and retrieving
ingestion pipelines.

The ingestion functionality is implemented by the ``phlo-dlt`` package, which
provides a decorator-based interface for extracting and loading data from
various sources into the lakehouse.

Key Exports:
    - :func:`phlo_ingestion`: Primary decorator for defining ingestion pipelines
    - :func:`get_ingestion_assets`: Retrieve all defined ingestion assets

Note:
    This module requires the ``phlo-dlt`` package to be installed. Install with:
    ``pip install phlo[defaults]`` or ``pip install phlo-dlt``.

Example:
    ```python
    import phlo

    @phlo.ingestion(
        source="github",
        table_name="events",
        group_name="raw"
    )
    def github_events():
        # Return data to be ingested
        return fetch_github_data()

    # Get all ingestion assets
    assets = phlo.ingestion.get_ingestion_assets()
    ```

See Also:
    - :mod:`phlo.quality`: Data quality validation
    - :class:`phlo.plugins.base.SourceConnectorPlugin`: Source connector interface
    - :mod:`phlo.hooks.events.IngestionEvent`: Ingestion lifecycle events

Raises:
    ModuleNotFoundError: If ``phlo-dlt`` is not installed.

"""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

from phlo.logging import get_logger

logger = get_logger(__name__)

try:
    from phlo_dlt import get_ingestion_assets, phlo_ingestion
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via optional extras
    logger.warning("phlo_dlt_not_installed", exc_info=True)
    raise ModuleNotFoundError(
        "phlo.ingestion requires phlo-dlt. Install phlo[defaults] or phlo-dlt."
    ) from exc


class _CallableIngestionModule(ModuleType):
    """Module type that lets ``phlo.ingestion(...)`` call the decorator."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return phlo_ingestion(*args, **kwargs)


sys.modules[__name__].__class__ = _CallableIngestionModule

__all__ = ["get_ingestion_assets", "phlo_ingestion"]
