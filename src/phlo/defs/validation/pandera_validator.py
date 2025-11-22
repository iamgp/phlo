"""
Pandera Validator Resource for severity-based data quality validation.

This module provides a Dagster resource for validating data against Pandera schemas
with support for severity-based blocking. Critical checks block pipeline progression,
while non-critical checks generate warnings.
"""

from typing import Any, Type

import dagster as dg
import pandas as pd
import pandera as pa
from phlo.defs.resources.trino import TrinoResource
from phlo.schemas.github import (
    FactGitHubRepoStats,
    FactGitHubUserEvents,
)
from phlo.schemas.glucose import (
    FactDailyGlucoseMetrics,
    FactGlucoseReadings,
)


class PanderaValidatorResource(dg.ConfigurableResource):
    """Validates data using Pandera schemas with severity-based blocking."""

    trino: TrinoResource
    critical_level: str = "error"  # "error" | "warning" | "info"

    def validate_table(
        self,
        table_name: str,
        schema_class: Type[pa.DataFrameModel],
        branch_name: str
    ) -> dict[str, Any]:
        """
        Validate a single table against its Pandera schema.

        Args:
            table_name: Table name (e.g., "fct_glucose_readings")
            schema_class: Pandera DataFrameModel class to validate against
            branch_name: Nessie branch name

        Returns:
            {
                "all_passed": bool,
                "table": str,
                "critical_failures": [...],
                "warnings": [...]
            }
        """
        result = self._validate_table(table_name, schema_class, branch_name)

        if not result["has_failures"]:
            return {
                "all_passed": True,
                "table": table_name,
                "critical_failures": [],
                "warnings": []
            }

        # Separate failures by severity
        critical_failures = []
        warnings = []

        for failure in result["failures"]:
            if failure["severity"] == self.critical_level:
                critical_failures.append(failure)
            else:
                warnings.append(failure)

        return {
            "all_passed": len(critical_failures) == 0,
            "table": table_name,
            "critical_failures": critical_failures,
            "warnings": warnings
        }

    def validate_all_tables(
        self,
        branch_name: str
    ) -> dict[str, Any]:
        """
        Run Pandera validation on all fact tables on given branch.

        Args:
            branch_name: Nessie branch name to validate

        Returns:
            {
                "tables_validated": int,
                "all_passed": bool,
                "critical_failures": [
                    {
                        "table": "fct_glucose_readings",
                        "severity": "error",
                        "failed_checks": [...],
                        "sample_failures": [...]
                    }
                ],
                "warnings": [...]
            }
        """
        # Define tables to validate (only used by validate_all_tables)
        # Individual checks use validate_table() and pass schema_class directly
        tables_to_validate = [
            ("fct_glucose_readings", FactGlucoseReadings),
            ("fct_daily_glucose_metrics", FactDailyGlucoseMetrics),
            ("fct_github_user_events", FactGitHubUserEvents),
            ("fct_github_repo_stats", FactGitHubRepoStats),
        ]

        critical_failures = []
        warnings = []

        for table_name, schema_class in tables_to_validate:
            result = self.validate_table(table_name, schema_class, branch_name)

            if not result["all_passed"]:
                critical_failures.extend(result["critical_failures"])
            if result["warnings"]:
                warnings.extend(result["warnings"])

        all_passed = len(critical_failures) == 0

        return {
            "tables_validated": len(tables_to_validate),
            "all_passed": all_passed,
            "critical_failures": critical_failures,
            "warnings": warnings
        }

    def _validate_table(
        self,
        table_name: str,
        schema_class: Type[pa.DataFrameModel],
        branch_name: str
    ) -> dict[str, Any]:
        """
        Validate a single table against its Pandera schema.

        Args:
            table_name: Table name (without schema prefix)
            schema_class: Pandera DataFrameModel class
            branch_name: Nessie branch name

        Returns:
            {
                "has_failures": bool,
                "failures": [{"table": str, "column": str, "severity": str, ...}]
            }
        """
        # Query table from Trino with branch session property
        conn = self.trino.get_connection(override_ref=branch_name)

        try:
            # Query data
            query = f"SELECT * FROM silver.{table_name}"
            df = pd.read_sql(query, conn)

            # Validate with Pandera (lazy=True to collect all errors)
            schema_class.validate(df, lazy=True)

            return {"has_failures": False, "failures": []}

        except pa.errors.SchemaErrors as err:
            failure_cases = err.failure_cases

            # Extract severity from field metadata
            failures = []

            # Group failures by column
            for column in failure_cases["column"].unique():
                column_failures = failure_cases[failure_cases["column"] == column]

                # Get severity from schema metadata
                try:
                    if hasattr(schema_class, column):
                        # Try to get metadata from the field
                        severity = "error"  # Default severity
                        if hasattr(schema_class, "__fields__"):
                            field = schema_class.__fields__.get(column)
                            if field and hasattr(field, "metadata"):
                                severity = field.metadata.get("severity", "error")
                    else:
                        severity = "error"
                except Exception:
                    severity = "error"

                failures.append({
                    "table": table_name,
                    "column": column,
                    "severity": severity,
                    "check": column_failures["check"].iloc[0],
                    "failure_count": len(column_failures),
                    "sample_failures": column_failures.head(5).to_dict("records")
                })

            return {
                "has_failures": True,
                "failures": failures
            }

        except Exception as e:
            # Handle other errors (e.g., table not found, connection issues)
            return {
                "has_failures": True,
                "failures": [{
                    "table": table_name,
                    "column": "N/A",
                    "severity": "error",
                    "check": "table_validation",
                    "failure_count": 1,
                    "error_message": str(e)
                }]
            }
        finally:
            conn.close()
