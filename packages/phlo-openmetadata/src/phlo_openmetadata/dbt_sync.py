"""
dbt manifest parser and synchronizer.

Parses dbt manifest.json and catalog.json to extract model documentation,
column descriptions, and tests for syncing to OpenMetadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from phlo.config import get_settings
from phlo.logging import get_logger

from phlo_openmetadata.openmetadata import OpenMetadataColumn, OpenMetadataTable

logger = get_logger(__name__)


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
        Get column information for a model from catalog.json.

        Args:
            model_name: Model name
            schema_name: Schema name
            catalog: Parsed catalog dict (uses loaded catalog if not provided)

        Returns:
            Dictionary mapping column name to column metadata
        """
        if catalog is None:
            catalog = self.catalog or self.load_catalog()

        if not catalog:
            return {}

        def normalize_columns(columns: Any) -> dict[str, dict[str, Any]]:
            if isinstance(columns, dict):
                return columns
            if isinstance(columns, list):
                normalized: dict[str, dict[str, Any]] = {}
                for entry in columns:
                    if not isinstance(entry, dict):
                        continue
                    name = entry.get("name")
                    if isinstance(name, str) and name:
                        normalized[name] = entry
                return normalized
            return {}

        if isinstance(catalog.get("nodes"), dict):
            nodes: dict[str, Any] = catalog.get("nodes", {})
            for node in nodes.values():
                if not isinstance(node, dict):
                    continue
                metadata = node.get("metadata") or {}
                if not isinstance(metadata, dict):
                    continue
                if metadata.get("name") != model_name or metadata.get("schema") != schema_name:
                    continue
                return normalize_columns(node.get("columns"))

            return {}

        key = f"{schema_name}.{model_name}"
        model_entry = catalog.get(key, {})
        return (
            normalize_columns(model_entry.get("columns")) if isinstance(model_entry, dict) else {}
        )

    def get_model_tests(
        self,
        model_unique_id: str,
        manifest: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Extract tests associated with a model.

        Args:
            model_unique_id: Model unique_id (e.g., model.project.table)
            manifest: Parsed manifest dict

        Returns:
            List of test metadata dicts
        """
        if manifest is None:
            manifest = self.manifest or self.load_manifest()

        tests = []
        for unique_id, node in manifest.get("nodes", {}).items():
            if unique_id.startswith("test.") and "test_metadata" in node:
                depends = node.get("depends_on", {}).get("nodes", [])
                if model_unique_id in depends:
                    tests.append(node)
        return tests

    def extract_openmetadata_table(
        self,
        model: dict[str, Any],
        schema_name: str,
        columns_info: Optional[dict[str, Any]] = None,
    ) -> OpenMetadataTable:
        """
        Convert dbt model metadata to OpenMetadataTable format.

        Args:
            model: dbt model metadata
            schema_name: Schema name
            columns_info: Optional column info from catalog.json

        Returns:
            OpenMetadataTable object
        """
        name = model.get("name", "unknown")
        description = model.get("description")

        columns = []
        model_columns = model.get("columns", {}) or {}

        for idx, (col_name, col_meta) in enumerate(model_columns.items()):
            col_desc = col_meta.get("description")
            data_type = "UNKNOWN"

            if columns_info and col_name in columns_info:
                data_type = columns_info[col_name].get("type", "UNKNOWN")

            columns.append(
                OpenMetadataColumn(
                    name=col_name,
                    description=col_desc,
                    dataType=data_type,
                    ordinalPosition=idx,
                )
            )

        tags = []
        for tag in model.get("tags", []) or []:
            tags.append({"name": tag})

        freshness = model.get("freshness")
        if freshness and isinstance(freshness, dict):
            warn_after = freshness.get("warn_after", {})
            if isinstance(warn_after, dict):
                count = warn_after.get("count")
                period = warn_after.get("period")
                if count and period:
                    tags.append({"name": f"freshness_warn_after_{count}_{period}"})

        return OpenMetadataTable(
            name=name,
            description=description,
            columns=columns if columns else None,
            tags=tags if tags else None,
        )

    def sync_to_openmetadata(
        self,
        om_client: Any,  # OpenMetadataClient
        schema_name: str,
        model_filter: Optional[list[str]] = None,
    ) -> dict[str, int]:
        """
        Sync dbt models to OpenMetadata.

        Args:
            om_client: OpenMetadataClient instance
            schema_name: Target OpenMetadata schema name
            model_filter: Optional list of dbt model names to sync

        Returns:
            Stats dict with created/failed counts
        """
        stats = {"created": 0, "failed": 0}

        manifest = self.load_manifest()
        catalog = self.load_catalog()

        models = self.get_models(manifest)
        for unique_id, model in models.items():
            model_name = model.get("name")
            if model_filter and model_name not in model_filter:
                continue

            try:
                columns_info = self.get_model_columns(model_name, schema_name, catalog)
                om_table = self.extract_openmetadata_table(model, schema_name, columns_info)
                om_client.create_or_update_table(schema_name, om_table)
                stats["created"] += 1
            except Exception as e:
                logger.error(f"Failed to sync model {model_name}: {e}")
                stats["failed"] += 1

        return stats
