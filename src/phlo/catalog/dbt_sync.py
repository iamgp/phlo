"""
dbt manifest parser and synchronizer.

Parses dbt manifest.json and catalog.json to extract model documentation,
column descriptions, and tests for syncing to OpenMetadata.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from phlo.catalog.openmetadata import OpenMetadataColumn, OpenMetadataTable
from phlo.config import get_settings

logger = logging.getLogger(__name__)


class DbtManifestParser:
    """
    Parses dbt manifest.json for metadata extraction.

    Extracts model descriptions, column-level documentation, tests,
    and freshness policies for syncing to OpenMetadata.
    """

    def __init__(self, manifest_path: str, catalog_path: Optional[str] = None):
        """
        Initialize dbt manifest parser.

        Args:
            manifest_path: Path to dbt manifest.json
            catalog_path: Path to dbt catalog.json (optional, for column docs)
        """
        self.manifest_path = Path(manifest_path)
        self.catalog_path = Path(catalog_path) if catalog_path else None
        self.manifest = None
        self.catalog = None

    @classmethod
    def from_config(cls) -> DbtManifestParser:
        """Create parser from application config."""
        config = get_settings()
        return cls(
            manifest_path=config.dbt_manifest_path,
            catalog_path=config.dbt_catalog_path,
        )

    def load_manifest(self) -> dict[str, Any]:
        """
        Load and parse dbt manifest.json.

        Returns:
            Parsed manifest dictionary

        Raises:
            FileNotFoundError: If manifest file not found
            json.JSONDecodeError: If manifest is invalid JSON
        """
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"dbt manifest not found: {self.manifest_path}")

        try:
            with open(self.manifest_path) as f:
                self.manifest = json.load(f)
            logger.info(f"Loaded dbt manifest from {self.manifest_path}")
            return self.manifest
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest: {e}")
            raise

    def load_catalog(self) -> dict[str, Any]:
        """
        Load and parse dbt catalog.json for column documentation.

        Returns:
            Parsed catalog dictionary, or empty dict if not found

        Raises:
            json.JSONDecodeError: If catalog is invalid JSON
        """
        if not self.catalog_path or not self.catalog_path.exists():
            logger.warning(
                f"dbt catalog not found at {self.catalog_path}, "
                "column-level docs will not be available"
            )
            return {}

        try:
            with open(self.catalog_path) as f:
                self.catalog = json.load(f)
            logger.info(f"Loaded dbt catalog from {self.catalog_path}")
            return self.catalog
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in catalog: {e}")
            raise

    def get_models(self, manifest: Optional[dict[str, Any]] = None) -> dict[str, dict[str, Any]]:
        """
        Extract all models from manifest.

        Args:
            manifest: Parsed manifest dict (uses loaded manifest if not provided)

        Returns:
            Dictionary mapping model unique_id to model metadata
        """
        if manifest is None:
            manifest = self.manifest or self.load_manifest()

        models = {}
        for unique_id, model in manifest.get("nodes", {}).items():
            if unique_id.startswith("model."):
                models[unique_id] = model
                logger.debug(f"Found model: {model.get('name')}")

        return models

    def get_model_columns(
        self,
        model_name: str,
        schema_name: str,
        catalog: Optional[dict[str, Any]] = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Extract column documentation for a model.

        Args:
            model_name: dbt model name
            schema_name: dbt schema name
            catalog: Parsed catalog dict (uses loaded catalog if not provided)

        Returns:
            Dictionary mapping column names to column documentation
        """
        if catalog is None:
            catalog = self.catalog or self.load_catalog()

        # Find model in catalog using schema.table format
        catalog_key = f"{schema_name}.{model_name}"

        if catalog_key not in catalog:
            logger.debug(f"Model not found in catalog: {catalog_key}")
            return {}

        model_catalog = catalog[catalog_key]
        columns = {}

        for col_name, col_info in model_catalog.get("columns", {}).items():
            columns[col_name] = {
                "description": col_info.get("description"),
                "type": col_info.get("type"),
                "index": col_info.get("index"),
            }

        return columns

    def get_model_tests(
        self,
        model_unique_id: str,
        manifest: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Get all tests associated with a model.

        Args:
            model_unique_id: Unique ID of the model
            manifest: Parsed manifest dict

        Returns:
            List of test metadata
        """
        if manifest is None:
            manifest = self.manifest or self.load_manifest()

        tests = []
        model_name = manifest["nodes"][model_unique_id].get("name")

        # Find all tests that reference this model
        for unique_id, test in manifest.get("nodes", {}).items():
            if unique_id.startswith("test.") and test.get("fqn"):
                # Check if this test applies to our model
                fqn = test["fqn"]
                if model_name in fqn or any(
                    dep.endswith(model_unique_id) for dep in test.get("depends_on", {}).get("nodes", [])
                ):
                    tests.append({
                        "name": test.get("name"),
                        "type": test.get("test_metadata", {}).get("name"),
                        "description": test.get("description"),
                        "kwargs": test.get("test_metadata", {}).get("kwargs", {}),
                    })

        return tests

    def extract_openmetadata_table(
        self,
        model: dict[str, Any],
        schema_name: str,
        columns_info: Optional[dict[str, dict[str, Any]]] = None,
    ) -> OpenMetadataTable:
        """
        Convert dbt model to OpenMetadata table format.

        Args:
            model: dbt model metadata from manifest
            schema_name: dbt schema name
            columns_info: Column documentation from catalog

        Returns:
            OpenMetadataTable object
        """
        model_name = model.get("name", "unknown")
        columns_info = columns_info or {}

        # Extract columns from dbt model
        columns = []
        order = 0

        if "columns" in model:
            # Use documented columns from dbt
            for col_name, col_meta in model["columns"].items():
                column = OpenMetadataColumn(
                    name=col_name,
                    description=col_meta.get("description"),
                    dataType=columns_info.get(col_name, {}).get("type", "UNKNOWN"),
                    ordinalPosition=order,
                )
                columns.append(column)
                order += 1
        elif columns_info:
            # Use columns from catalog if available
            for col_name, col_info in sorted(
                columns_info.items(),
                key=lambda x: x[1].get("index", 999),
            ):
                column = OpenMetadataColumn(
                    name=col_name,
                    description=col_info.get("description"),
                    dataType=col_info.get("type", "UNKNOWN"),
                    ordinalPosition=order,
                )
                columns.append(column)
                order += 1

        # Build tags
        tags = []
        if "tags" in model:
            for tag in model["tags"]:
                tags.append({"name": tag, "source": "dbt"})

        # Check freshness
        freshness = model.get("freshness", {})
        if freshness:
            tags.append({
                "name": f"freshness-{freshness.get('warn_after', 'unknown')}",
                "source": "dbt",
            })

        table = OpenMetadataTable(
            name=model_name,
            description=model.get("description"),
            columns=columns if columns else None,
            tableType="Regular",
            tags=tags if tags else None,
        )

        return table

    def sync_to_openmetadata(
        self,
        om_client: Any,  # OpenMetadataClient
        schema_name: str = "marts",
        model_filter: Optional[list[str]] = None,
    ) -> dict[str, int]:
        """
        Sync dbt models to OpenMetadata.

        Args:
            om_client: OpenMetadataClient instance
            schema_name: dbt schema name (default: marts)
            model_filter: List of model names to sync (if None, sync all)

        Returns:
            Dictionary with sync statistics
        """
        stats = {"created": 0, "updated": 0, "failed": 0}

        try:
            # Load manifest and catalog
            manifest = self.load_manifest()
            catalog = self.load_catalog()

            models = self.get_models(manifest)
            logger.info(f"Found {len(models)} dbt models")

            for model_id, model in models.items():
                model_name = model.get("name")

                # Filter models if specified
                if model_filter and model_name not in model_filter:
                    continue

                try:
                    # Get column documentation
                    columns_info = self.get_model_columns(
                        model_name, schema_name, catalog
                    )

                    # Convert to OpenMetadata format
                    om_table = self.extract_openmetadata_table(
                        model, schema_name, columns_info
                    )

                    # Sync to OpenMetadata
                    om_client.create_or_update_table(schema_name, om_table)
                    stats["created"] += 1

                except Exception as e:
                    logger.error(f"Failed to sync model {model_name}: {e}")
                    stats["failed"] += 1

        except Exception as e:
            logger.error(f"Error during dbt sync: {e}")

        logger.info(
            f"dbt sync completed: {stats['created']} created, "
            f"{stats['updated']} updated, {stats['failed']} failed"
        )

        return stats
