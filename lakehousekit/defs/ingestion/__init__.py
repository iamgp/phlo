from __future__ import annotations

import dagster as dg

from lakehousekit.defs.ingestion.airbyte import (
    AirbyteConnectionConfig,
)
from lakehousekit.defs.ingestion.airbyte import (
    build_assets_from_configs as build_airbyte_assets,
)

# Bioreactor assets disabled - focusing on Nightscout workflow
# from lakehousekit.defs.ingestion.raw import raw_bioreactor_data


def _airbyte_assets() -> list[dg.AssetsDefinition]:
    """
    Build Airbyte assets from configured connections.

    Connections are looked up by name at runtime, making them resilient
    to Docker restarts and workspace recreation. Simply create connections
    in Airbyte with the names specified below and they'll be automatically
    discovered.
    """
    configs = [
        AirbyteConnectionConfig(
            connection_name="Nightscout to Local JSON",
            destination_tables=["nightscout_entries"],
            group_name="raw_ingestion",
        ),
    ]

    return build_airbyte_assets(configs)


def build_defs() -> dg.Definitions:
    assets = list(_airbyte_assets())
    # Bioreactor assets disabled - focusing on Nightscout workflow
    # assets.append(raw_bioreactor_data)

    return dg.Definitions(assets=assets)
