from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from dagster import AssetsDefinition
from dagster_airbyte import build_airbyte_assets


@dataclass(frozen=True)
class AirbyteConnectionConfig:
    connection_id: str
    destination_tables: Sequence[str] | None = None
    group_name: str | None = None


def build_assets_from_configs(
    configs: Iterable[AirbyteConnectionConfig],
) -> list[AssetsDefinition]:
    assets: list[AssetsDefinition] = []
    for config in configs:
        connection_assets = build_airbyte_assets(
            connection_id=config.connection_id,
            destination_tables=list(config.destination_tables or []),
            group_name=config.group_name,
        )
        assets.extend(connection_assets)

    return assets
