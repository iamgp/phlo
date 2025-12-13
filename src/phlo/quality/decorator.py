"""
@phlo_quality decorator for declarative quality checks.

This decorator reduces quality check boilerplate from 30-40 lines to 5-10 lines
by automatically generating Dagster asset checks from declarative quality check definitions.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, List, Optional

from dagster import AssetCheckResult, AssetCheckSeverity, AssetKey, MetadataValue, asset_check

from phlo.quality.checks import QualityCheck, QualityCheckResult, SchemaCheck
from phlo.quality.contract import PANDERA_CONTRACT_CHECK_NAME, QualityCheckContract

_QUALITY_CHECKS: list[Any] = []


def phlo_quality(
    table: str,
    checks: List[QualityCheck],
    asset_key: Optional[AssetKey] = None,
    group: Optional[str] = None,
    blocking: bool = True,
    warn_threshold: float = 0.0,
    description: Optional[str] = None,
    query: Optional[str] = None,
    backend: str = "trino",
) -> Callable:
    """
    Decorator that generates Dagster asset checks from quality check definitions.

    This decorator reduces quality check boilerplate by 70%, transforming verbose
    asset check implementations into concise declarative definitions.

    Args:
        table: Fully qualified table name (e.g., "bronze.weather_observations")
        checks: List of quality checks to execute
        asset_key: Optional Dagster AssetKey (derived from table if not provided)
        group: Optional asset group
        blocking: Whether check failures block downstream assets (default: True)
        warn_threshold: Fraction of checks that can fail before marking as WARN (0.0 = fail immediately)
        description: Optional description (auto-generated if not provided)
        query: Optional custom SQL query (defaults to SELECT * FROM {table})
        backend: Backend to use ("trino" or "duckdb", default: "trino")

    Returns:
        Decorated function that executes quality checks

    Example:
        ```python
        from phlo.quality import phlo_quality, NullCheck, RangeCheck

        @phlo_quality(
            table="bronze.weather_observations",
            checks=[
                NullCheck(columns=["station_id", "temperature"]),
                RangeCheck(column="temperature", min_value=-50, max_value=60),
            ],
            group="weather",
        )
        def weather_quality_check():
            '''Quality checks for weather observations.'''
            pass
        ```

        This generates a Dagster asset check that:
        - Queries the table via Trino/DuckDB
        - Executes all quality checks
        - Returns AssetCheckResult with rich metadata
        - Reduces code from ~40 lines to ~8 lines (80% reduction)
    """

    def decorator(func: Callable) -> Callable:
        # Derive asset key from table name if not provided
        nonlocal asset_key, description

        if asset_key is None:
            # Extract table name from fully qualified name
            # e.g., "bronze.weather_observations" -> "weather_observations"
            table_parts = table.split(".")
            table_name = table_parts[-1]
            asset_key = AssetKey([table_name])

        # Auto-generate description if not provided
        if description is None:
            check_names = [check.name for check in checks]
            description = f"Quality checks for {table}: {', '.join(check_names[:3])}" + (
                "..." if len(check_names) > 3 else ""
            )

        # Build the SQL query
        default_query = f"SELECT * FROM {table}"
        sql_query = query or default_query

        schema_checks = [check for check in checks if isinstance(check, SchemaCheck)]
        non_schema_checks = [check for check in checks if not isinstance(check, SchemaCheck)]

        if schema_checks:

            @asset_check(
                name=PANDERA_CONTRACT_CHECK_NAME,
                asset=asset_key,
                blocking=blocking,
                description=f"Pandera schema contract for {table}",
            )
            @wraps(func)
            def pandera_contract_check(context, **resources) -> AssetCheckResult:
                partition_key = getattr(context, "partition_key", None)
                if partition_key is None:
                    partition_key = getattr(context, "asset_partition_key", None)

                final_query = sql_query
                if partition_key:
                    final_query = f"{sql_query} WHERE partition_date = '{partition_key}'"
                    context.log.info(f"Validating partition: {partition_key}")

                try:
                    if backend == "trino":
                        df = _load_data_trino(context, final_query, resources)
                    elif backend == "duckdb":
                        df = _load_data_duckdb(context, final_query, resources)
                    else:
                        raise ValueError(f"Unknown backend: {backend}")
                except Exception as exc:
                    context.log.error(f"Failed to load data: {exc}")
                    contract = QualityCheckContract(
                        source="pandera",
                        partition_key=str(partition_key) if partition_key else None,
                        failed_count=1,
                        total_count=None,
                        query_or_sql=final_query,
                        sample=[{"error": str(exc)}],
                    )
                    return AssetCheckResult(
                        passed=False,
                        metadata={
                            **contract.to_dagster_metadata(),
                            "reason": MetadataValue.text("query_failed"),
                            "error": MetadataValue.text(str(exc)),
                        },
                    )

                if df.empty:
                    contract = QualityCheckContract(
                        source="pandera",
                        partition_key=str(partition_key) if partition_key else None,
                        failed_count=0,
                        total_count=0,
                        query_or_sql=final_query,
                        sample=[],
                    )
                    return AssetCheckResult(
                        passed=True,
                        metadata={
                            **contract.to_dagster_metadata(),
                            "note": MetadataValue.text("No data available for validation"),
                        },
                    )

                failures: list[Any] = []
                failed_count = 0
                schema_names: list[str] = []
                all_passed = True

                for check in schema_checks:
                    schema_names.append(getattr(check.schema, "__name__", str(type(check.schema))))
                    result = check.execute(df, context)
                    if not result.passed:
                        all_passed = False
                        failed_checks = int(
                            result.metadata.get("failed_checks", 0) if result.metadata else 0
                        )
                        failed_count += failed_checks
                        if result.metadata and "sample_failures" in result.metadata:
                            failures.extend(result.metadata["sample_failures"])

                contract = QualityCheckContract(
                    source="pandera",
                    partition_key=str(partition_key) if partition_key else None,
                    failed_count=failed_count,
                    total_count=len(df),
                    query_or_sql=final_query,
                    sample=failures,
                )
                return AssetCheckResult(
                    passed=all_passed,
                    metadata={
                        **contract.to_dagster_metadata(),
                        "schemas": MetadataValue.json(schema_names),
                    },
                )

        if non_schema_checks:
            # Create the Dagster asset check function
            @asset_check(
                name=func.__name__,
                asset=asset_key,
                blocking=blocking,
                description=description,
            )
            @wraps(func)
            def quality_check_wrapper(context, **resources) -> AssetCheckResult:
                """
                Execute all non-Pandera quality checks on the table.

                Pandera schema checks are emitted as a separate ``pandera/contract`` asset check when
                ``SchemaCheck`` is included in the decorator's check list.
                """
                partition_key = getattr(context, "partition_key", None)
                if partition_key is None:
                    partition_key = getattr(context, "asset_partition_key", None)

                final_query = sql_query
                if partition_key and "WHERE" not in sql_query.upper():
                    final_query = f"{sql_query}\nWHERE DATE(timestamp) = DATE '{partition_key}'"
                    context.log.info(f"Validating partition: {partition_key}")

                try:
                    if backend == "trino":
                        df = _load_data_trino(context, final_query, resources)
                    elif backend == "duckdb":
                        df = _load_data_duckdb(context, final_query, resources)
                    else:
                        raise ValueError(f"Unknown backend: {backend}")
                except Exception as exc:
                    context.log.error(f"Failed to load data: {exc}")
                    return AssetCheckResult(
                        passed=False,
                        metadata={
                            "reason": MetadataValue.text("query_failed"),
                            "error": MetadataValue.text(str(exc)),
                            "query": MetadataValue.text(final_query),
                        },
                    )

                if df.empty:
                    context.log.warning("No rows returned; marking check as skipped.")
                    return AssetCheckResult(
                        passed=True,
                        metadata={
                            "rows_validated": MetadataValue.int(0),
                            "note": MetadataValue.text("No data available for validation"),
                        },
                    )

                context.log.info(
                    f"Executing {len(non_schema_checks)} quality checks on {len(df)} rows..."
                )

                check_results: List[QualityCheckResult] = []
                all_passed = True

                for check in non_schema_checks:
                    try:
                        result = check.execute(df, context)
                        check_results.append(result)

                        if not result.passed:
                            all_passed = False
                            context.log.warning(
                                f"Quality check '{check.name}' failed: {result.failure_message}"
                            )
                        else:
                            context.log.info(f"Quality check '{check.name}' passed")
                    except Exception as exc:
                        context.log.exception(
                            f"Error executing quality check '{check.name}': {exc}"
                        )
                        check_results.append(
                            QualityCheckResult(
                                passed=False,
                                metric_name=check.name,
                                metric_value=None,
                                metadata={"error": str(exc)},
                                failure_message=f"Check execution failed: {exc}",
                            )
                        )
                        all_passed = False

                metadata = _build_metadata(df, check_results)

                passed_count = sum(1 for r in check_results if r.passed)
                failed_count = sum(1 for r in check_results if not r.passed)
                failure_fraction = failed_count / len(check_results) if check_results else 0.0

                summary = f"{passed_count}/{len(check_results)} quality checks passed"
                if failed_count > 0:
                    failed_checks = [
                        f"{r.metric_name}: {r.failure_message}"
                        for r in check_results
                        if not r.passed
                    ]
                    metadata["failures"] = MetadataValue.md(
                        "## Failed Checks\n\n" + "\n".join(f"- {f}" for f in failed_checks)
                    )
                metadata["summary"] = MetadataValue.text(summary)

                severity = AssetCheckSeverity.SUCCESS if all_passed else AssetCheckSeverity.FAILURE
                if failure_fraction > 0 and failure_fraction <= warn_threshold:
                    severity = AssetCheckSeverity.WARN
                    context.log.warning(
                        f"Quality check warning: {failure_fraction:.1%} of checks failed "
                        f"(within warn threshold of {warn_threshold:.1%})"
                    )

                return AssetCheckResult(
                    passed=all_passed or (failure_fraction <= warn_threshold),
                    severity=severity if all_passed else None,
                    metadata=metadata,
                )

            _QUALITY_CHECKS.append(quality_check_wrapper)
            if schema_checks:
                _QUALITY_CHECKS.append(pandera_contract_check)
            return quality_check_wrapper

        if schema_checks:
            _QUALITY_CHECKS.append(pandera_contract_check)
            return pandera_contract_check

        raise ValueError("phlo_quality requires at least one check")

    return decorator


def get_quality_checks() -> list[Any]:
    """
    Get all asset checks registered with @phlo_quality decorator.

    Returns:
        List of Dagster asset check definitions
    """
    return _QUALITY_CHECKS.copy()


def _load_data_trino(context: Any, query: str, resources: dict) -> Any:
    """Load data from Trino."""
    import pandas as pd

    # Get Trino resource
    trino = resources.get("trino")
    if trino is None:
        raise ValueError("Trino resource not found in context")

    # Execute query
    with trino.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

        if not cursor.description:
            raise ValueError("Trino did not return column metadata")

        columns = [desc[0] for desc in cursor.description]

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=columns)

    context.log.info(f"Loaded {len(df)} rows from Trino")

    return df


def _load_data_duckdb(context: Any, query: str, resources: dict) -> Any:
    """Load data from DuckDB."""

    # Get DuckDB connection
    duckdb_conn = resources.get("duckdb")
    if duckdb_conn is None:
        raise ValueError("DuckDB resource not found in context")

    # Execute query
    df = duckdb_conn.execute(query).fetchdf()

    context.log.info(f"Loaded {len(df)} rows from DuckDB")

    return df


def _build_metadata(df: Any, check_results: List[QualityCheckResult]) -> dict:
    """Build metadata dictionary for Dagster UI."""
    metadata = {
        "rows_validated": MetadataValue.int(len(df)),
        "columns_validated": MetadataValue.int(len(df.columns)),
        "checks_executed": MetadataValue.int(len(check_results)),
        "checks_passed": MetadataValue.int(sum(1 for r in check_results if r.passed)),
        "checks_failed": MetadataValue.int(sum(1 for r in check_results if not r.passed)),
    }

    # Add individual check results
    for result in check_results:
        # Add metric value
        if result.metric_value is not None:
            if isinstance(result.metric_value, dict):
                metadata[f"{result.metric_name}_value"] = MetadataValue.json(result.metric_value)
            else:
                metadata[f"{result.metric_name}_value"] = MetadataValue.text(
                    str(result.metric_value)
                )

        # Add check metadata
        if result.metadata:
            for key, value in result.metadata.items():
                metadata_key = f"{result.metric_name}_{key}"
                if isinstance(value, (dict, list)):
                    metadata[metadata_key] = MetadataValue.json(value)
                elif isinstance(value, (int, float)):
                    metadata[metadata_key] = MetadataValue.float(float(value))
                else:
                    metadata[metadata_key] = MetadataValue.text(str(value))

    # Build quality summary table
    summary_rows = []
    for result in check_results:
        summary_rows.append(
            f"| {result.metric_name} | {'✅ Pass' if result.passed else '❌ Fail'} | "
            f"{result.metric_value} | {result.failure_message or '-'} |"
        )

    if summary_rows:
        summary_table = (
            "## Quality Check Results\n\n"
            "| Check | Status | Value | Message |\n"
            "|-------|--------|-------|----------|\n" + "\n".join(summary_rows)
        )
        metadata["quality_summary"] = MetadataValue.md(summary_table)

    return metadata
