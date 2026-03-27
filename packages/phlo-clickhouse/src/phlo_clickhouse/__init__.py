"""ClickHouse service and resource plugin package."""

from phlo_clickhouse.plugin import (
    ClickHouseResourceProvider,
    ClickHouseServicePlugin,
    ClickHouseSetupServicePlugin,
)
from phlo_clickhouse.resource import ClickHouseResource
from phlo_clickhouse.settings import ClickHouseSettings, get_settings

__all__ = [
    "ClickHouseResource",
    "ClickHouseResourceProvider",
    "ClickHouseServicePlugin",
    "ClickHouseSetupServicePlugin",
    "ClickHouseSettings",
    "get_settings",
]
__version__ = "0.2.1"
