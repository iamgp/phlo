"""Custom quality checks using phlo plugins.

Demonstrates how to use third-party plugins to extend phlo's quality check capabilities.
This example uses the phlo-plugin-example package to create custom threshold checks
with tolerance levels for glucose data validation.
"""

from __future__ import annotations

import pandas as pd
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
from phlo_trino.resource import TrinoResource

# Import the plugin - phlo-plugin-example must be installed
try:
    from phlo_example.quality import ThresholdCheck

    PLUGIN_AVAILABLE = True
except ImportError:
    PLUGIN_AVAILABLE = False
    print("Warning: phlo-plugin-example not installed. Install with: uv sync --group plugins")


# ---------------------------------------------------------------------------
# Plugin-based quality checks
# ---------------------------------------------------------------------------

if PLUGIN_AVAILABLE:

    @asset_check(
        name="glucose_consecutive_highs_plugin",
        asset=AssetKey(["fct_glucose_readings"]),
        blocking=False,
        description=(
            "Verify glucose readings don't have excessive consecutive high values. "
            "Uses plugin-based threshold check with 5% tolerance."
        ),
    )
    def glucose_consecutive_highs_plugin_check(context, trino: TrinoResource) -> AssetCheckResult:
        """
        Check for excessive high glucose readings using plugin threshold check.

        Uses ThresholdCheck from phlo-plugin-example with tolerance to allow
        some natural variation while catching concerning patterns.

        This demonstrates:
        - Installing and using third-party plugins
        - Custom threshold validation
        - Tolerance-based quality checks
        """
        query = """
        SELECT
            glucose_mg_dl,
            reading_timestamp,
            direction
        FROM iceberg_dev.silver.fct_glucose_readings
        ORDER BY reading_timestamp DESC
        LIMIT 1000
        """

        try:
            with trino.cursor(schema="silver") as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

            df = pd.DataFrame(rows, columns=columns)

            if df.empty:
                return AssetCheckResult(
                    passed=True,
                    metadata={
                        "rows_validated": MetadataValue.int(0),
                        "note": MetadataValue.text("No data available"),
                    },
                )

            # Create plugin check: glucose should be below 250 mg/dL
            # Allow 5% tolerance (5 out of 100 readings can be higher)
            check = ThresholdCheck(
                column="glucose_mg_dl",
                min_value=None,  # No minimum check
                max_value=250,  # Flag readings above 250 mg/dL
                tolerance=0.05,  # Allow 5% violation rate
            )

            # Execute the check
            result = check.execute(df)

            context.log.info(
                f"Plugin check results: {result['violations']}/{result['total']} "
                f"violations ({result['violation_rate']:.1%})"
            )

            return AssetCheckResult(
                passed=result["passed"],
                metadata={
                    "rows_validated": MetadataValue.int(result["total"]),
                    "violations": MetadataValue.int(result["violations"]),
                    "violation_rate": MetadataValue.float(result["violation_rate"]),
                    "threshold": MetadataValue.text("250 mg/dL with 5% tolerance"),
                    "check_name": MetadataValue.text(check.name),
                },
            )

        except Exception as exc:
            context.log.error(f"Plugin check failed: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={
                    "error": MetadataValue.text(str(exc)),
                    "reason": MetadataValue.text("check_execution_failed"),
                },
            )

    @asset_check(
        name="glucose_variability_plugin",
        asset=AssetKey(["fct_daily_glucose_metrics"]),
        blocking=False,
        description="Check glucose variability coefficient using plugin threshold check",
    )
    def glucose_variability_plugin_check(context, trino: TrinoResource) -> AssetCheckResult:
        """
        Validate coefficient of variation stays within acceptable bounds.

        CV (Coefficient of Variation) measures glucose variability:
        - < 36%: Good glucose stability
        - 36-40%: Acceptable
        - > 40%: High variability (concern)

        Uses plugin to check with 10% tolerance (some high CV days are normal).
        """
        query = """
        SELECT
            reading_date,
            avg_glucose_mg_dl,
            stddev_glucose_mg_dl,
            ROUND(100.0 * stddev_glucose_mg_dl / NULLIF(avg_glucose_mg_dl, 0), 1) as cv
        FROM iceberg_dev.gold.fct_daily_glucose_metrics
        WHERE stddev_glucose_mg_dl IS NOT NULL
        ORDER BY reading_date DESC
        LIMIT 90
        """

        try:
            with trino.cursor(schema="gold") as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

            df = pd.DataFrame(rows, columns=columns)

            if df.empty:
                return AssetCheckResult(passed=True)

            # Check CV with plugin: should be below 40% with 10% tolerance
            check = ThresholdCheck(
                column="cv",
                max_value=40.0,
                tolerance=0.10,  # Max 40% CV  # Allow 10% of days
            )

            result = check.execute(df)

            return AssetCheckResult(
                passed=result["passed"],
                metadata={
                    "days_validated": MetadataValue.int(result["total"]),
                    "high_cv_days": MetadataValue.int(result["violations"]),
                    "high_cv_rate": MetadataValue.float(result["violation_rate"]),
                    "threshold": MetadataValue.text("CV < 40% with 10% tolerance"),
                    "plugin_name": MetadataValue.text("phlo-plugin-example"),
                },
            )

        except Exception as exc:
            context.log.error(f"Variability check failed: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={"error": MetadataValue.text(str(exc))},
            )
