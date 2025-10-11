from __future__ import annotations

import dagster as dg

from lakehousekit.defs.ingestion.airbyte import (
    AirbyteConnectionConfig,
    build_assets_from_configs as build_airbyte_assets,
)
from lakehousekit.defs.ingestion.raw import raw_bioreactor_data


def _airbyte_assets() -> list[dg.AssetsDefinition]:
    configs = [
        AirbyteConnectionConfig(
            connection_id="015ab542-1a18-4156-a44a-861b17f8d03c",
            destination_tables=["nightscout_entries"],
            group_name="raw_ingestion",
        )
    ]

    return build_airbyte_assets(configs)


def build_defs() -> dg.Definitions:
    assets = list(_airbyte_assets())
    assets.append(raw_bioreactor_data)

    return dg.Definitions(assets=assets)
