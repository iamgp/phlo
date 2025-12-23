from __future__ import annotations

import dagster as dg
from phlo.plugins.base import DagsterExtensionPlugin, PluginMetadata

from phlo_iceberg.resource import IcebergResource


class IcebergDagsterPlugin(DagsterExtensionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="iceberg",
            version="0.1.0",
            description="Iceberg/Nessie catalog resource for Phlo",
        )

    def get_definitions(self) -> dg.Definitions:
        return dg.Definitions(resources={"iceberg": IcebergResource()})
