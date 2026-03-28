"""Resource provider plugin for phlo-lineage capabilities.

This module provides the LineageResourceProvider class, which exposes phlo-lineage
capabilities through the Phlo plugin system. It enables other Phlo components to
discover and use lineage tracking functionality as a capability provider.

Capabilities Exposed:
    - LineageSinkSpec: The phlo-lineage sink for recording and querying lineage data.

Plugin Registration:
    This provider is auto-discovered via entry points. No manual registration required.

Example:
    The lineage sink is accessible through Phlo's capability system:

    >>> from phlo.capabilities import get_lineage_sink
    >>> sink = get_lineage_sink("phlo-lineage")
    >>> sink.record_asset_edges([("bronze.orders", "silver.stg_orders")])

"""

from __future__ import annotations

from phlo.capabilities import LineageSinkSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_lineage.lineage_sink import PhloLineageSink


class LineageResourceProvider(ResourceProviderPlugin):
    """Expose phlo-lineage as a lineage sink capability."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for capability discovery.

        Returns:
            PluginMetadata with name, version, description, and tags for
            the lineage capability provider.

        Attributes Returned:
            - name: "lineage"
            - version: "0.1.0"
            - description: "Lineage sink capability provider"
            - tags: ["lineage"]

        Example:
            >>> provider = LineageResourceProvider()
            >>> meta = provider.metadata
            >>> print(meta.name)
            'lineage'
            >>> print(meta.tags)
            ['lineage']

        """
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Lineage sink capability provider",
            tags=["lineage"],
        )

    def get_resources(self) -> list:
        """Return list of raw resources exposed by this provider.

        This provider does not expose any raw resources directly. All lineage
        functionality is accessed through the lineage_sinks capability interface.

        Returns:
            Empty list. Raw resources are not exposed in this slice.

        See Also:
            get_lineage_sinks() for the capability interface.

        """
        return []

    def get_lineage_sinks(self) -> list[LineageSinkSpec]:
        """Expose the phlo-lineage sink as a capability.

        Returns the lineage sink specification that allows other Phlo components
        to record and query data lineage through a standardized interface.

        Returns:
            List containing a single LineageSinkSpec with:
                - name: "phlo-lineage" (identifier for capability lookup)
                - provider: PhloLineageSink instance (the actual sink implementation)

        Capability Usage:
            Components can access this sink via:
            >>> from phlo.capabilities import get_lineage_sink
            >>> sink = get_lineage_sink("phlo-lineage")
            >>> sink.record_row_lineage(row_id="...", table_name="bronze.orders")

        See Also:
            PhloLineageSink for the full API documentation.
            phlo.capabilities module for capability discovery patterns.

        """
        return [
            LineageSinkSpec(
                name="phlo-lineage",
                provider=PhloLineageSink(),
            )
        ]
