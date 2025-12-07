"""
Lineage extraction and publishing for OpenMetadata.

Extracts lineage information from Dagster and dbt,
and publishes it to OpenMetadata for data discovery and impact analysis.
"""

from __future__ import annotations

import logging
from typing import Any

from phlo.lineage.graph import LineageGraph

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
            # Get current run and its materialized assets
            run = context.run
            if not run:
                logger.warning("No run information available in context")
                return

            # Get assets from run result
            for key, result in context.run_context.output_map.items():
                asset_name = key.path[-1] if hasattr(key, "path") else str(key)
                self.graph.add_asset(asset_name, asset_type="unknown")

            logger.info(f"Extracted {len(self.graph.assets)} assets from Dagster")

        except Exception as e:
            logger.error(f"Failed to extract Dagster lineage: {e}")

    def extract_from_dbt_manifest(self, manifest: dict[str, Any]) -> None:
        """
        Extract lineage from dbt manifest.json.

        Args:
            manifest: Parsed dbt manifest dictionary
        """
        try:
            # Extract all models
            for unique_id, node in manifest.get("nodes", {}).items():
                if unique_id.startswith("model."):
                    model_name = node.get("name")
                    self.graph.add_asset(
                        model_name,
                        asset_type="transform",
                        status="unknown",
                    )

            # Extract sources (external data)
            for unique_id, source in manifest.get("sources", {}).items():
                source_name = f"{source.get('source_name')}.{source.get('name')}"
                self.graph.add_asset(
                    source_name,
                    asset_type="ingestion",
                    status="unknown",
                )

            # Extract model dependencies
            for unique_id, node in manifest.get("nodes", {}).items():
                if unique_id.startswith("model."):
                    model_name = node.get("name")

                    # Add edges from dependencies
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

            logger.info(f"Added {len(nessie_tables)} Iceberg namespaces to lineage")

        except Exception as e:
            logger.error(f"Failed to extract Iceberg lineage: {e}")

    def build_publishing_lineage(
        self,
        dbt_manifest: dict[str, Any],
        postgres_schema: str = "marts",
    ) -> dict[str, list[str]]:
        """
        Build lineage from raw data through to published tables.

        Shows: Source → dbt → Iceberg → Postgres flow

        Args:
            dbt_manifest: Parsed dbt manifest
            postgres_schema: Schema name for published tables

        Returns:
            Dictionary mapping source to all downstream published tables
        """
        lineage_map = {}

        try:
            # Find all published (marts) tables in dbt
            published_models = []
            for unique_id, node in dbt_manifest.get("nodes", {}).items():
                if unique_id.startswith("model.") and postgres_schema in node.get("schema", ""):
                    published_models.append(node.get("name"))

            # For each published model, trace back to sources
            for pub_model in published_models:
                upstream = self.graph.get_upstream(pub_model)
                for source in upstream:
                    if source not in lineage_map:
                        lineage_map[source] = []
                    lineage_map[source].append(pub_model)

            logger.info(f"Built publishing lineage for {len(lineage_map)} sources")
            return lineage_map

        except Exception as e:
            logger.error(f"Failed to build publishing lineage: {e}")
            return {}

    def publish_to_openmetadata(
        self,
        om_client: Any,  # OpenMetadataClient
        include_edges: bool = True,
    ) -> dict[str, int]:
        """
        Publish lineage to OpenMetadata.

        Args:
            om_client: OpenMetadataClient instance
            include_edges: Whether to publish lineage edges

        Returns:
            Dictionary with publication statistics
        """
        stats = {"edges_published": 0, "failed": 0}

        try:
            if not include_edges:
                logger.info("Skipping lineage edge publication")
                return stats

            # Publish all edges
            for source, targets in self.graph.edges.items():
                for target in targets:
                    try:
                        # Try to publish lineage edge
                        # Map to database.schema.table format if needed
                        from_fqn = self._normalize_fqn(source)
                        to_fqn = self._normalize_fqn(target)

                        om_client.create_lineage(from_fqn, to_fqn)
                        stats["edges_published"] += 1

                    except Exception as e:
                        logger.warning(f"Failed to publish edge {source}->{target}: {e}")
                        stats["failed"] += 1

            logger.info(f"Published {stats['edges_published']} lineage edges to OpenMetadata")

        except Exception as e:
            logger.error(f"Failed to publish lineage to OpenMetadata: {e}")

        return stats

    def get_impact_analysis(self, asset_name: str) -> dict[str, Any]:
        """
        Analyze impact of changes to an asset.

        Shows what downstream assets would be affected if this asset fails.

        Args:
            asset_name: Name of the asset

        Returns:
            Impact analysis dictionary
        """
        impact = self.graph.get_impact(asset_name)

        # Add more detailed information
        downstream = self.graph.get_downstream(asset_name)

        publishing_assets = [
            a for a in downstream if self.graph.assets.get(a, {}).asset_type == "publish"
        ]

        return {
            **impact,
            "publishing_assets_affected": publishing_assets,
            "total_affected": len(downstream),
        }

    def export_lineage(self, format_type: str = "json") -> str:
        """
        Export lineage in various formats.

        Args:
            format_type: Format type (json, dot, mermaid)

        Returns:
            Formatted lineage string
        """
        if format_type == "json":
            return self.graph.to_json()
        elif format_type == "dot":
            return self.graph.to_dot()
        elif format_type == "mermaid":
            return self.graph.to_mermaid()
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    @staticmethod
    def _normalize_fqn(name: str) -> str:
        """
        Normalize asset name to fully qualified name format.

        Converts shorthand names to schema.table format if needed.

        Args:
            name: Asset name

        Returns:
            Normalized fully qualified name
        """
        # If already has schema prefix, return as-is
        if "." in name:
            return name

        # Otherwise, assume it's a table in default schema
        # This is a simplification; in production you'd want a mapping
        return f"default.{name}"
