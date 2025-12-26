"""
@phlo_quality decorator for declarative quality checks.

This decorator reduces quality check boilerplate from 30-40 lines to 5-10 lines
by automatically generating Dagster asset checks from declarative quality check definitions.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, List, Optional

from dagster import AssetCheckResult, AssetCheckSeverity, AssetKey, MetadataValue, asset_check

from phlo.hooks import QualityResultEvent, get_hook_bus
from phlo_quality.checks import QualityCheck, QualityCheckResult, SchemaCheck
from phlo_quality.contract import PANDERA_CONTRACT_CHECK_NAME, QualityCheckContract
from phlo_quality.partitioning import PartitionScope, apply_partition_scope, get_partition_key
from phlo_quality.severity import severity_for_pandera_contract, severity_for_quality_check

_QUALITY_CHECKS: list[Any] = []


def phlo_quality(
    table: str,
    checks: List[QualityCheck],
    asset_key: Optional[AssetKey] = None,
    group: Optional[str] = None,
    blocking: bool = True,
    partition_aware: bool = True,
    warn_threshold: float = 0.0,
    partition_column: str = "_phlo_partition_date",
    rolling_window_days: int | None = 7,
    full_table: bool = False,
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
        partition_aware: Whether to apply partition scoping (default: True)
        warn_threshold: Max fraction of failed checks to mark as WARN (otherwise ERROR)
        partition_column: Partition column name used for scoping queries
        rolling_window_days: When unpartitioned, optionally scope to last N days
        full_table: Disable partition scoping (use with care)
        description: Optional description (auto-generated if not provided)
        query: Optional custom SQL query (defaults to SELECT * FROM {table})
        backend: Backend to use ("trino" or "duckdb", default: "trino")

    Returns:
        Decorated function that executes quality checks

    Example:
        ```python
        from phlo_quality import phlo_quality, NullCheck, RangeCheck

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
        nonlocal asset_key, description, full_table

        if not partition_aware:
            full_table = True

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
                blocking=True,
                description=f"Pandera schema contract for {table}",
            )
            @wraps(func)
            def pandera_contract_check(context, **resources) -> AssetCheckResult:
                partition_key = get_partition_key(context)
                partition_key_value = str(partition_key) if partition_key else None
                asset_name = _asset_key_to_str(asset_key)
                scope = PartitionScope(
                    partition_key=partition_key,
                    partition_column=partition_column,
                    rolling_window_days=rolling_window_days,
                    full_table=full_table,
                )
                final_query = apply_partition_scope(sql_query, scope=scope)
                if partition_key and not full_table:
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
                        partition_key=partition_key_value,
                        failed_count=1,
                        total_count=None,
                        query_or_sql=final_query,
                        repro_sql=_repro_sql(final_query),
                        sample=[{"error": str(exc)}],
                    )
                    event_metadata = _contract_metadata(contract)
                    event_metadata.update({"reason": "query_failed", "error": str(exc)})
                    _emit_quality_event(
                        QualityResultEvent(
                            event_type="quality.result",
                            asset_key=asset_name,
                            check_name=PANDERA_CONTRACT_CHECK_NAME,
                            passed=False,
                            severity=AssetCheckSeverity.ERROR.value,
                            check_type="pandera",
                            partition_key=partition_key_value,
                            metadata=event_metadata,
                            tags={"source": "pandera", "backend": backend},
                        )
                    )
                    return AssetCheckResult(
                        passed=False,
                        severity=AssetCheckSeverity.ERROR,
                        metadata={
                            **contract.to_dagster_metadata(),
                            "reason": MetadataValue.text("query_failed"),
                            "error": MetadataValue.text(str(exc)),
                        },
                    )

                if df.empty:
                    contract = QualityCheckContract(
                        source="pandera",
                        partition_key=partition_key_value,
                        failed_count=0,
                        total_count=0,
                        query_or_sql=final_query,
                        repro_sql=_repro_sql(final_query),
                        sample=[],
                    )
                    event_metadata = _contract_metadata(contract)
                    event_metadata["note"] = "no_data"
                    _emit_quality_event(
                        QualityResultEvent(
                            event_type="quality.result",
                            asset_key=asset_name,
                            check_name=PANDERA_CONTRACT_CHECK_NAME,
                            passed=True,
                            check_type="pandera",
                            partition_key=partition_key_value,
                            metadata=event_metadata,
                            tags={"source": "pandera", "backend": backend},
                        )
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
                    partition_key=partition_key_value,
                    failed_count=failed_count,
                    total_count=len(df),
                    query_or_sql=final_query,
                    repro_sql=_repro_sql(final_query),
                    sample=failures,
                )
                severity = severity_for_pandera_contract(passed=all_passed)
                result_kwargs = {
                    "passed": all_passed,
                    "metadata": {
                        **contract.to_dagster_metadata(),
                        "schemas": MetadataValue.json(schema_names),
                    },
                }
                if severity is not None:
                    result_kwargs["severity"] = severity
                event_metadata = _contract_metadata(contract)
                event_metadata["schemas"] = schema_names
                _emit_quality_event(
                    QualityResultEvent(
                        event_type="quality.result",
                        asset_key=asset_name,
                        check_name=PANDERA_CONTRACT_CHECK_NAME,
                        passed=all_passed,
                        severity=severity.value if severity else None,
                        check_type="pandera",
                        partition_key=partition_key_value,
                        metadata=event_metadata,
                        tags={"source": "pandera", "backend": backend},
                    )
                )
                return AssetCheckResult(**result_kwargs)

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

                Pandera schema checks are emitted as a separate ``pandera_contract`` asset check when
                ``SchemaCheck`` is included in the decorator's check list.
                """
                partition_key = get_partition_key(context)
                partition_key_value = str(partition_key) if partition_key else None
                asset_name = _asset_key_to_str(asset_key)
                scope = PartitionScope(
                    partition_key=partition_key,
                    partition_column=partition_column,
                    rolling_window_days=rolling_window_days,
                    full_table=full_table,
                )
                final_query = apply_partition_scope(sql_query, scope=scope)
                if partition_key and not full_table:
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
                    _emit_quality_event(
                        QualityResultEvent(
                            event_type="quality.result",
                            asset_key=asset_name,
                            check_name=func.__name__,
                            passed=False,
                            severity=AssetCheckSeverity.ERROR.value,
                            check_type="phlo",
                            partition_key=partition_key_value,
                            metadata={
                                "reason": "query_failed",
                                "error": str(exc),
                                "query_or_sql": final_query,
                            },
                            tags={"source": "phlo", "backend": backend},
                        )
                    )
                    return AssetCheckResult(
                        passed=False,
                        severity=AssetCheckSeverity.ERROR,
                        metadata={
                            "reason": MetadataValue.text("query_failed"),
                            "error": MetadataValue.text(str(exc)),
                            "query": MetadataValue.text(final_query),
                        },
                    )

                if df.empty:
                    context.log.warning("No rows returned; marking check as skipped.")
                    _emit_quality_event(
                        QualityResultEvent(
                            event_type="quality.result",
                            asset_key=asset_name,
                            check_name=func.__name__,
                            passed=True,
                            check_type="phlo",
                            partition_key=partition_key_value,
                            metadata={"note": "no_data", "query_or_sql": final_query},
                            tags={"source": "phlo", "backend": backend},
                        )
                    )
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
                contract = QualityCheckContract(
                    source="phlo",
                    partition_key=str(partition_key) if partition_key else None,
                    failed_count=_estimate_failed_count(check_results),
                    total_count=len(df),
                    query_or_sql=final_query,
                    repro_sql=_repro_sql(final_query),
                    sample=_collect_failure_sample(check_results),
                )
                metadata.update(contract.to_dagster_metadata())

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

                severity = severity_for_quality_check(
                    passed=all_passed,
                    failure_fraction=failure_fraction,
                    warn_threshold=warn_threshold,
                )
                if severity == AssetCheckSeverity.WARN:
                    context.log.warning(
                        f"Quality check warning: {failure_fraction:.1%} of checks failed "
                        f"(within warn threshold of {warn_threshold:.1%})"
                    )

                severity_label = severity.value if severity else None
                for check, result in zip(non_schema_checks, check_results):
                    failed_count = _estimate_failed_count([result])
                    contract = QualityCheckContract(
                        source="phlo",
                        partition_key=partition_key_value,
                        failed_count=failed_count,
                        total_count=len(df),
                        query_or_sql=final_query,
                        repro_sql=_repro_sql(final_query),
                        sample=_collect_failure_sample([result]),
                    )
                    event_metadata = _contract_metadata(contract)
                    if result.metric_value is not None:
                        event_metadata["metric_value"] = result.metric_value
                    if result.failure_message:
                        event_metadata["failure_message"] = result.failure_message
                    if result.metadata:
                        event_metadata.update(result.metadata)
                    _emit_quality_event(
                        QualityResultEvent(
                            event_type="quality.result",
                            asset_key=asset_name,
                            check_name=result.metric_name,
                            passed=result.passed,
                            severity=severity_label if not result.passed else None,
                            check_type=type(check).__name__,
                            partition_key=partition_key_value,
                            metadata=event_metadata,
                            tags={"source": "phlo", "backend": backend},
                        )
                    )

                result_kwargs = {"passed": all_passed, "metadata": metadata}
                if severity is not None:
                    result_kwargs["severity"] = severity
                return AssetCheckResult(**result_kwargs)

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


def _estimate_failed_count(check_results: List[QualityCheckResult]) -> int:
    failed_count = 0
    for result in check_results:
        if result.passed:
            continue
        metadata = result.metadata or {}
        for key in (
            "failed_rows",
            "failure_count",
            "duplicate_count",
            "out_of_range",
            "non_match_count",
        ):
            value = metadata.get(key)
            if isinstance(value, int):
                failed_count += value
                break
    if failed_count > 0:
        return failed_count
    return sum(1 for r in check_results if not r.passed)


def _collect_failure_sample(check_results: List[QualityCheckResult]) -> list[dict[str, Any]]:
    sample: list[dict[str, Any]] = []
    for result in check_results:
        if result.passed:
            continue
        rows = result.metadata.get("sample_rows") if result.metadata else None
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            sample.append({"check": result.metric_name, **row})
            if len(sample) >= 20:
                return sample
    return sample


def _asset_key_to_str(asset_key: AssetKey) -> str:
    if hasattr(asset_key, "path") and asset_key.path:
        return "/".join(str(part) for part in asset_key.path)
    return str(asset_key)


def _contract_metadata(contract: QualityCheckContract) -> dict[str, Any]:
    metadata: dict[str, Any] = {"source": contract.source, "failed_count": contract.failed_count}
    if contract.partition_key is not None:
        metadata["partition_key"] = contract.partition_key
    if contract.total_count is not None:
        metadata["total_count"] = contract.total_count
    if contract.query_or_sql is not None:
        metadata["query_or_sql"] = contract.query_or_sql
    if contract.repro_sql is not None:
        metadata["repro_sql"] = contract.repro_sql
    if contract.sample is not None:
        metadata["sample"] = contract.sample[:20]
    return metadata


def _emit_quality_event(event: QualityResultEvent) -> None:
    get_hook_bus().emit(event)


def _repro_sql(query: str) -> str:
    return f"SELECT *\nFROM (\n{query}\n) AS phlo_quality\nLIMIT 100"
