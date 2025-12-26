"""
Lineage extraction and publishing for OpenMetadata.

Extracts lineage information from Dagster and dbt,
and publishes it to OpenMetadata for data discovery and impact analysis.
"""

from __future__ import annotations

import logging
from typing import Any

from phlo_lineage.graph import LineageGraph

logger = logging.getLogger(__name__)


class LineageExtractor:
    """
    Extracts lineage from various sources (Dagster, dbt, Iceberg).

    Builds a unified lineage graph and publishes to OpenMetadata.
    """

    def __init__(self):
        """Initialize lineage extractor."""
        self.graph = LineageGraph()

    def extract_from_dagster(self, context: Any) -> None:
        """
        Extract lineage from Dagster context.

        Args:
            context: Dagster context with run and asset information
        """
        try:
            if not hasattr(context, "get_asset_materialization_events"):
                logger.warning(
                    "Unsupported Dagster execution context for lineage extraction. "
                    "Expected an ExecuteInProcessResult-like object with "
                    "get_asset_materialization_events()."
                )
                return

            events = context.get_asset_materialization_events()
            if not isinstance(events, list):
                logger.warning("Dagster context returned unexpected materialization events type")
                return

            for event in events:
                asset_key = getattr(event, "asset_key", None)
                if asset_key is None:
                    continue
                if hasattr(asset_key, "path") and asset_key.path:
                    asset_name = asset_key.path[-1]
                else:
                    asset_name = str(asset_key)
                self.graph.add_asset(asset_name, asset_type="unknown")

            logger.info(f"Extracted {len(self.graph.assets)} assets from Dagster materializations")

        except Exception as e:
            logger.error(f"Failed to extract Dagster lineage: {e}")

    def extract_from_dbt_manifest(self, manifest: dict[str, Any]) -> None:
        """
        Extract lineage from dbt manifest.json.

        Args:
            manifest: Parsed dbt manifest dictionary
        """
        try:
            for unique_id, node in manifest.get("nodes", {}).items():
                if unique_id.startswith("model."):
                    model_name = node.get("name")
                    self.graph.add_asset(
                        model_name,
                        asset_type="transform",
                        status="unknown",
                    )

            for unique_id, source in manifest.get("sources", {}).items():
                source_name = f"{source.get('source_name')}.{source.get('name')}"
                self.graph.add_asset(
                    source_name,
                    asset_type="ingestion",
                    status="unknown",
                )

            for unique_id, node in manifest.get("nodes", {}).items():
                if unique_id.startswith("model."):
                    model_name = node.get("name")

                    for dep_id in node.get("depends_on", {}).get("nodes", []):
                        if dep_id.startswith("model."):
                            dep_name = manifest["nodes"][dep_id].get("name")
                            self.graph.add_edge(dep_name, model_name)
                        elif dep_id.startswith("source."):
                            source = manifest.get("sources", {}).get(dep_id, {})
                            source_name = f"{source.get('source_name')}.{source.get('name')}"
                            self.graph.add_edge(source_name, model_name)

            logger.info(
                f"Extracted {len(self.graph.assets)} assets and "
                f"{sum(len(v) for v in self.graph.edges.values())} edges from dbt"
            )

        except Exception as e:
            logger.error(f"Failed to extract dbt lineage: {e}")

    def extract_from_iceberg(
        self,
        nessie_tables: dict[str, list[dict[str, Any]]],
    ) -> None:
        """
        Add Iceberg tables to lineage graph.

        Args:
            nessie_tables: Dictionary of namespace -> tables from Nessie
        """
        try:
            for namespace, tables in nessie_tables.items():
                for table in tables:
                    table_name = table.get("name")
                    full_name = f"{namespace}.{table_name}"

                    self.graph.add_asset(
                        full_name,
                        asset_type="ingestion",
                        status="unknown",
                    )

            logger.info(f"Extracted {len(self.graph.assets)} tables from Iceberg catalog")

        except Exception as e:
            logger.error(f"Failed to extract Iceberg lineage: {e}")

    def build_publishing_lineage(
        self,
        manifest: dict[str, Any],
        postgres_schema: str,
    ) -> dict[str, list[str]]:
        """
        Build source -> published tables mapping.

        Identifies dbt models in `postgres_schema` as "published" tables, then returns
        which of those tables are downstream of each ingestion source.
        """
        published_models: set[str] = set()
        for unique_id, node in manifest.get("nodes", {}).items():
            if not unique_id.startswith("model."):
                continue
            if node.get("schema") == postgres_schema and node.get("name"):
                published_models.add(node["name"])

        if not published_models:
            return {}

        lineage: dict[str, list[str]] = {}
        for _unique_id, source in manifest.get("sources", {}).items():
            source_fqn = f"{source.get('source_name')}.{source.get('name')}"
            downstream = self.graph.get_downstream(source_fqn)
            published_downstream = sorted(a for a in downstream if a in published_models)
            if published_downstream:
                lineage[source_fqn] = published_downstream

        return lineage

    def publish_to_openmetadata(
        self,
        om_client: Any,  # OpenMetadataClient
        include_edges: bool = True,
    ) -> dict[str, int]:
        """
        Publish lineage graph to OpenMetadata.

        Args:
            om_client: OpenMetadataClient instance

        Returns:
            Publication statistics
        """
        stats = {"edges_published": 0, "failed": 0}

        if not include_edges:
            return stats

        try:
            for from_asset, to_assets in self.graph.edges.items():
                for to_asset in to_assets:
                    try:
                        om_client.create_lineage(from_asset, to_asset)
                        stats["edges_published"] += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to publish lineage edge {from_asset}->{to_asset}: {e}"
                        )
                        stats["failed"] += 1

            logger.info(f"Published {stats['edges_published']} lineage edges to OpenMetadata")

        except Exception as e:
            logger.error(f"Failed to publish lineage to OpenMetadata: {e}")
            stats["failed"] += 1

        return stats

    def get_impact_analysis(self, asset_name: str) -> dict[str, Any]:
        """Return downstream impact analysis for an asset."""
        affected = sorted(self.graph.get_downstream(asset_name))
        return {"affected_assets": affected, "total_affected": len(affected)}

    def export_lineage(self, format_type: str = "json") -> str:
        """Export lineage graph in a supported format."""
        if format_type == "json":
            return self.graph.to_json()
        if format_type == "dot":
            return self.graph.to_dot()
        if format_type == "mermaid":
            return self.graph.to_mermaid()
        raise ValueError(f"Unsupported format: {format_type}")

    @staticmethod
    def _normalize_fqn(fqn: str) -> str:
        """Normalize unqualified table names to `default.<name>`."""
        return fqn if "." in fqn else f"default.{fqn}"
