"""Hasura metadata export, import and schema management."""

import json
from pathlib import Path
from typing import Any, Optional

from phlo_hasura.client import HasuraClient
from phlo.logging import get_logger

logger = get_logger(__name__)


class HasuraMetadataSync:
    """Manage Hasura metadata export/import and version control."""

    def __init__(self, client: Optional[HasuraClient] = None):
        """Initialize metadata sync.

        Args:
            client: HasuraClient instance
        """
        self.client = client or HasuraClient()

    def export_metadata(self, output_path: Optional[str | Path] = None) -> dict[str, Any]:
        """Export Hasura metadata.

        Args:
            output_path: Optional path to save metadata

        Returns:
            Metadata dictionary
        """
        metadata = self.client.export_metadata()

        if output_path:
            output_path = Path(output_path)
            with open(output_path, "w") as f:
                json.dump(metadata, f, indent=2)

        return metadata

    def import_metadata(self, input_path: str | Path) -> dict[str, Any]:
        """Import Hasura metadata from file.

        Args:
            input_path: Path to metadata file

        Returns:
            API response
        """
        input_path = Path(input_path)

        with open(input_path) as f:
            metadata = json.load(f)

        return self.client.apply_metadata(metadata)

    def merge_metadata(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Merge two metadata dictionaries (override over base).

        Args:
            base: Base metadata
            override: Metadata to override with

        Returns:
            Merged metadata
        """
        merged = base.copy()

        # Merge top-level keys
        for key in ["version", "metadata"]:
            if key in override:
                merged[key] = override[key]

        # Merge sources (custom types, functions, etc.)
        if "sources" in override:
            # Replace entire sources list for simplicity
            merged["sources"] = override["sources"]

        return merged

    def get_diff(self, current: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
        """Calculate diff between current and desired metadata.

        Args:
            current: Current metadata
            desired: Desired metadata

        Returns:
            Diff summary
        """
        diff = {
            "sources": {"added": [], "removed": [], "modified": []},
            "tables": {"added": [], "removed": [], "modified": []},
            "relationships": {"added": [], "removed": []},
            "permissions": {"added": [], "removed": []},
        }

        # Track current tables and sources
        current_sources = {s.get("name"): s for s in current.get("sources", [])}
        desired_sources = {s.get("name"): s for s in desired.get("sources", [])}

        # Check for added/removed sources
        for name in desired_sources:
            if name not in current_sources:
                diff["sources"]["added"].append(name)

        for name in current_sources:
            if name not in desired_sources:
                diff["sources"]["removed"].append(name)

        # Check table differences
        current_tables = self._extract_tables(current)
        desired_tables = self._extract_tables(desired)

        current_table_set = set(current_tables.keys())
        desired_table_set = set(desired_tables.keys())

        diff["tables"]["added"] = list(desired_table_set - current_table_set)
        diff["tables"]["removed"] = list(current_table_set - desired_table_set)

        # Check for modified tables
        for table_path in current_table_set & desired_table_set:
            if current_tables[table_path] != desired_tables[table_path]:
                diff["tables"]["modified"].append(table_path)

        # Check relationship and permission differences
        current_rels = self._extract_relationships(current)
        desired_rels = self._extract_relationships(desired)

        diff["relationships"]["added"] = list(set(desired_rels) - set(current_rels))
        diff["relationships"]["removed"] = list(set(current_rels) - set(desired_rels))

        return diff

    def _extract_tables(self, metadata: dict[str, Any]) -> dict[str, dict]:
        """Extract table information from metadata.

        Args:
            metadata: Metadata dictionary

        Returns:
            Dict of table_path -> table_info
        """
        tables = {}

        for source in metadata.get("sources", []):
            if source.get("name") != "default":
                continue

            for table in source.get("tables", []):
                schema = table.get("table", {}).get("schema", "public")
                name = table["table"]["name"]
                table_path = f"{schema}.{name}"
                tables[table_path] = table

        return tables

    def _extract_relationships(self, metadata: dict[str, Any]) -> list[tuple]:
        """Extract relationships from metadata.

        Args:
            metadata: Metadata dictionary

        Returns:
            List of (table, relationship_name) tuples
        """
        rels = []

        for source in metadata.get("sources", []):
            if source.get("name") != "default":
                continue

            for table in source.get("tables", []):
                schema = table.get("table", {}).get("schema", "public")
                table_name = table["table"]["name"]

                for rel in table.get("object_relationships", []):
                    rel_name = rel.get("name")
                    rels.append((f"{schema}.{table_name}", rel_name, "object"))

                for rel in table.get("array_relationships", []):
                    rel_name = rel.get("name")
                    rels.append((f"{schema}.{table_name}", rel_name, "array"))

        return rels

    def generate_diff_report(self, current: dict[str, Any], desired: dict[str, Any]) -> str:
        """Generate human-readable diff report.

        Args:
            current: Current metadata
            desired: Desired metadata

        Returns:
            Formatted diff report
        """
        diff = self.get_diff(current, desired)

        lines = ["Hasura Metadata Diff Report", "=" * 60]

        # Sources
        if diff["sources"]["added"]:
            lines.append(f"\nSources to add: {len(diff['sources']['added'])}")
            for source in diff["sources"]["added"]:
                lines.append(f"  + {source}")

        if diff["sources"]["removed"]:
            lines.append(f"\nSources to remove: {len(diff['sources']['removed'])}")
            for source in diff["sources"]["removed"]:
                lines.append(f"  - {source}")

        # Tables
        if diff["tables"]["added"]:
            lines.append(f"\nTables to track: {len(diff['tables']['added'])}")
            for table in sorted(diff["tables"]["added"]):
                lines.append(f"  + {table}")

        if diff["tables"]["removed"]:
            lines.append(f"\nTables to untrack: {len(diff['tables']['removed'])}")
            for table in sorted(diff["tables"]["removed"]):
                lines.append(f"  - {table}")

        if diff["tables"]["modified"]:
            lines.append(f"\nTables to modify: {len(diff['tables']['modified'])}")
            for table in sorted(diff["tables"]["modified"]):
                lines.append(f"  ~ {table}")

        # Relationships
        if diff["relationships"]["added"]:
            lines.append(f"\nRelationships to add: {len(diff['relationships']['added'])}")
            for table, rel, rel_type in sorted(diff["relationships"]["added"]):
                lines.append(f"  + {table}.{rel} ({rel_type})")

        if diff["relationships"]["removed"]:
            lines.append(f"\nRelationships to remove: {len(diff['relationships']['removed'])}")
            for table, rel, rel_type in sorted(diff["relationships"]["removed"]):
                lines.append(f"  - {table}.{rel} ({rel_type})")

        return "\n".join(lines)

    def reload_metadata(self) -> None:
        """Reload metadata from database."""
        self.client.reload_metadata()


def export_metadata(output_path: Optional[str] = None, verbose: bool = True) -> str:
    """Convenience function to export metadata.

    Args:
        output_path: Path to save metadata
        verbose: Print progress messages

    Returns:
        Path where metadata was saved (if output_path provided)
    """
    if verbose:
        logger.info("Exporting Hasura metadata...")

    syncer = HasuraMetadataSync()
    metadata = syncer.export_metadata(output_path)

    if output_path:
        if verbose:
            logger.info("✓ Metadata exported to %s", output_path)
        return output_path
    else:
        if verbose:
            logger.info("✓ Metadata exported")
        return json.dumps(metadata, indent=2)


def apply_metadata(input_path: str, verbose: bool = True) -> None:
    """Convenience function to apply metadata.

    Args:
        input_path: Path to metadata file
        verbose: Print progress messages
    """
    if verbose:
        logger.info("Applying metadata from %s...", input_path)

    syncer = HasuraMetadataSync()
    syncer.import_metadata(input_path)

    if verbose:
        logger.info("✓ Metadata applied")
