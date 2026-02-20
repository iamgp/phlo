from collections.abc import Callable
from typing import Any


def phlo_ingestion(*args: Any, **kwargs: Any) -> Callable[..., Any]:
    """Lazily resolve and forward to the ingestion decorator factory."""
    from phlo_dlt.decorator import phlo_ingestion as _phlo_ingestion

    return _phlo_ingestion(*args, **kwargs)


def get_ingestion_assets() -> list[Any]:
    """Lazily resolve and return registered ingestion assets."""
    from phlo_dlt.decorator import get_ingestion_assets as _get_ingestion_assets

    return _get_ingestion_assets()


__all__ = ["get_ingestion_assets", "phlo_ingestion"]
