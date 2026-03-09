from collections.abc import Callable
from typing import Any


def phlo_sling_replication(*args: Any, **kwargs: Any) -> Callable[..., Any]:
    """Lazily resolve and forward to the sling replication decorator factory."""
    from phlo_sling.decorator import phlo_sling_replication as _phlo_sling_replication

    return _phlo_sling_replication(*args, **kwargs)


def get_sling_assets() -> list[Any]:
    """Lazily resolve and return registered sling replication assets."""
    from phlo_sling.decorator import get_sling_assets as _get_sling_assets

    return _get_sling_assets()


__all__ = ["get_sling_assets", "phlo_sling_replication"]
