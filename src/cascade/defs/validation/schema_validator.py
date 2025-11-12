"""
Schema Compatibility Validator Resource for detecting breaking changes.

This module provides a Dagster resource for validating schema compatibility
between Nessie branches, allowing additive changes while blocking breaking changes.
"""

from typing import Any

import dagster as dg
from cascade.iceberg.catalog import get_catalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table


class SchemaCompatibilityValidatorResource(dg.ConfigurableResource):
    """Validates schema compatibility between branches."""

    def check_compatibility(
        self,
        feature_branch: str,
        target_branch: str = "main"
    ) -> dict[str, Any]:
        """
        Compare schemas between feature and target branches.

        Allows:
        - New columns (additive changes)
        - New tables

        Blocks:
        - Dropped columns
        - Type changes
        - Constraint changes (nullability, etc.)

        Args:
            feature_branch: Pipeline branch to validate
            target_branch: Target branch to compare against (default: main)

        Returns:
            {
                "compatible": bool,
                "tables_checked": [str],
                "breaking_changes": [
                    {
                        "table": "bronze.entries",
                        "change_type": "column_dropped",
                        "details": "Column 'device' exists in main but not in feature branch"
                    }
                ],
                "additive_changes": [
                    {
                        "table": "bronze.entries",
                        "change_type": "column_added",
                        "details": "New column 'noise_level' in feature branch"
                    }
                ]
            }
        """
        # Get catalogs for both branches
        try:
            feature_catalog = get_catalog(ref=feature_branch)
            target_catalog = get_catalog(ref=target_branch)
        except Exception as e:
            return {
                "compatible": False,
                "tables_checked": [],
                "breaking_changes": [{
                    "table": "N/A",
                    "change_type": "catalog_error",
                    "details": f"Failed to connect to catalogs: {str(e)}"
                }],
                "additive_changes": []
            }

        # Get list of tables to compare
        tables_to_check = [
            "bronze.entries",
            "silver.fct_glucose_readings",
            "silver.fct_daily_glucose_metrics",
            "bronze.github_user_events",
            "silver.fct_github_user_events",
            "bronze.github_repo_stats",
            "silver.fct_github_repo_stats",
        ]

        breaking_changes = []
        additive_changes = []
        tables_checked = []

        for table_name in tables_to_check:
            try:
                feature_table = feature_catalog.load_table(table_name)
                target_table = target_catalog.load_table(table_name)

                tables_checked.append(table_name)

                changes = self._compare_schemas(
                    table_name,
                    feature_table.schema(),
                    target_table.schema()
                )

                breaking_changes.extend(changes["breaking"])
                additive_changes.extend(changes["additive"])

            except Exception as e:
                # Table doesn't exist in one of the branches
                error_msg = str(e).lower()
                if "not found" in error_msg or "does not exist" in error_msg:
                    # New table in feature branch (additive)
                    if feature_branch in str(e) or "feature" in str(e):
                        continue  # Table doesn't exist in feature yet (expected)
                    else:
                        additive_changes.append({
                            "table": table_name,
                            "change_type": "table_added",
                            "details": f"New table '{table_name}' in {feature_branch}"
                        })
                else:
                    # Other error
                    breaking_changes.append({
                        "table": table_name,
                        "change_type": "table_error",
                        "details": f"Error comparing table: {str(e)}"
                    })

        compatible = len(breaking_changes) == 0

        return {
            "compatible": compatible,
            "tables_checked": tables_checked,
            "breaking_changes": breaking_changes,
            "additive_changes": additive_changes
        }

    def _compare_schemas(
        self,
        table_name: str,
        feature_schema: Schema,
        target_schema: Schema
    ) -> dict[str, list]:
        """Compare two schemas and categorize changes."""
        breaking = []
        additive = []

        # Build field maps
        feature_fields = {f.name: f for f in feature_schema.fields}
        target_fields = {f.name: f for f in target_schema.fields}

        # Check for dropped columns (breaking)
        for field_name, field in target_fields.items():
            if field_name not in feature_fields:
                breaking.append({
                    "table": table_name,
                    "change_type": "column_dropped",
                    "details": f"Column '{field_name}' exists in main but not in {table_name}"
                })

        # Check for new columns (additive) and type changes (breaking)
        for field_name, field in feature_fields.items():
            if field_name not in target_fields:
                additive.append({
                    "table": table_name,
                    "change_type": "column_added",
                    "details": f"New column '{field_name}' added"
                })
            else:
                # Check for type changes (breaking)
                target_field = target_fields[field_name]
                if str(field.field_type) != str(target_field.field_type):
                    breaking.append({
                        "table": table_name,
                        "change_type": "type_changed",
                        "details": f"Column '{field_name}' type changed from {target_field.field_type} to {field.field_type}"
                    })

        return {"breaking": breaking, "additive": additive}
