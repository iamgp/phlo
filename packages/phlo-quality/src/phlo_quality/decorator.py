"""
@phlo_quality decorator for declarative quality checks.

This decorator reduces quality check boilerplate from 30-40 lines to 5-10 lines
by automatically generating Dagster asset checks from declarative quality check definitions.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional

from phlo.capabilities import AssetCheckSpec, CheckResult, register_check
from phlo.capabilities.runtime import RuntimeContext

from phlo.hooks import (
    QualityResultEventContext,
    QualityResultEventEmitter,
    TelemetryEventContext,
    TelemetryEventEmitter,
)
from phlo_quality.checks import QualityCheck, QualityCheckResult, SchemaCheck
from phlo_quality.contract import PANDERA_CONTRACT_CHECK_NAME, QualityCheckContract
from phlo_quality.partitioning import PartitionScope, apply_partition_scope, get_partition_key
from phlo_quality.severity import severity_for_pandera_contract, severity_for_quality_check

_QUALITY_CHECKS: list[Any] = []


def phlo_quality(
    table: str,
    checks: List[QualityCheck],
    asset_key: Optional[str] = None,
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
        asset_key: Optional asset key string (derived from table if not provided)
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
        - Returns capability check results with rich metadata
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
            asset_key = table_parts[-1]

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

        assert asset_key is not None
        asset_key_value = asset_key

        if schema_checks:
            def pandera_contract_check(runtime: RuntimeContext) -> CheckResult:
                partition_key = get_partition_key(runtime)
                partition_key_value = str(partition_key) if partition_key else None
                emitter = QualityResultEventEmitter(
                    QualityResultEventContext(
                        asset_key=asset_key_value,
                        partition_key=partition_key_value,
                        tags={"source": "pandera", "backend": backend},
                    )
                )
                telemetry = TelemetryEventEmitter(
                    TelemetryEventContext(
                        tags={
                            "asset": asset_key_value,
                            "source": "pandera",
                            "backend": backend,
                        }
                    )
                )
                scope = PartitionScope(
                    partition_key=partition_key,
                    partition_column=partition_column,
                    rolling_window_days=rolling_window_days,
                    full_table=full_table,
                )
                final_query = apply_partition_scope(sql_query, scope=scope)
                if partition_key and not full_table:
                    runtime.logger.info(f"Validating partition: {partition_key}")

                try:
                    if backend == "trino":
                        trino = _resolve_trino_resource(runtime)
                        df = _load_data_trino(runtime, final_query, trino)
                    elif backend == "duckdb":
                        duckdb_conn = _resolve_duckdb_connection(runtime)
                        df = _load_data_duckdb(runtime, final_query, duckdb_conn)
                    else:
                        raise ValueError(f"Unknown backend: {backend}")
                except Exception as exc:
                    runtime.logger.error(f"Failed to load data: {exc}")
                    telemetry.emit_log(
                        name="quality.query_failed",
                        level="error",
                        payload={"error": str(exc), "table": table},
                    )
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
                    event_metadata.update(
                        {"reason": "query_failed", "error": str(exc), "table": table}
                    )
                    emitter.emit_result(
                        check_name=PANDERA_CONTRACT_CHECK_NAME,
                        passed=False,
                        severity="error",
                        check_type="pandera",
                        metadata=event_metadata,
                    )
                    return CheckResult(
                        passed=False,
                        check_name=PANDERA_CONTRACT_CHECK_NAME,
                        asset_key=asset_key_value,
                        severity="error",
                        metadata={
                            **contract.to_metadata(),
                            "reason": "query_failed",
                            "error": str(exc),
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
                    event_metadata["table"] = table
                    emitter.emit_result(
                        check_name=PANDERA_CONTRACT_CHECK_NAME,
                        passed=True,
                        check_type="pandera",
                        metadata=event_metadata,
                    )
                    telemetry.emit_metric(
                        name="quality.rows_validated",
                        value=0,
                        unit="rows",
                        payload={"status": "no_data", "table": table},
                    )
                    return CheckResult(
                        passed=True,
                        check_name=PANDERA_CONTRACT_CHECK_NAME,
                        asset_key=asset_key_value,
                        metadata={
                            **contract.to_metadata(),
                            "note": "No data available for validation",
                        },
                    )

                failures: list[Any] = []
                failed_count = 0
                schema_names: list[str] = []
                all_passed = True

                for check in schema_checks:
                    schema_names.append(getattr(check.schema, "__name__", str(type(check.schema))))
                    result = check.execute(df, runtime)
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
                event_metadata = _contract_metadata(contract)
                event_metadata["schemas"] = schema_names
                event_metadata["table"] = table
                emitter.emit_result(
                    check_name=PANDERA_CONTRACT_CHECK_NAME,
                    passed=all_passed,
                    severity=severity,
                    check_type="pandera",
                    metadata=event_metadata,
                )
                telemetry.emit_metric(
                    name="quality.rows_validated",
                    value=len(df),
                    unit="rows",
                    payload={"table": table},
                )
                telemetry.emit_metric(
                    name="quality.failed_count",
                    value=failed_count,
                    unit="checks",
                    payload={"table": table},
                )
                telemetry.emit_metric(
                    name="quality.schemas_checked",
                    value=len(schema_names),
                    unit="schemas",
                    payload={"table": table},
                )
                return CheckResult(
                    passed=all_passed,
                    check_name=PANDERA_CONTRACT_CHECK_NAME,
                    asset_key=asset_key_value,
                    severity=severity,
                    metadata={**contract.to_metadata(), "schemas": schema_names},
                )

            pandera_spec = AssetCheckSpec(
                name=PANDERA_CONTRACT_CHECK_NAME,
                asset_key=asset_key_value,
                fn=pandera_contract_check,
                blocking=True,
                description=f"Pandera schema contract for {table}",
            )
            _QUALITY_CHECKS.append(pandera_spec)
            register_check(pandera_spec)

        if non_schema_checks:
            def quality_check_wrapper(runtime: RuntimeContext) -> CheckResult:
                partition_key = get_partition_key(runtime)
                partition_key_value = str(partition_key) if partition_key else None
                emitter = QualityResultEventEmitter(
                    QualityResultEventContext(
                        asset_key=asset_key_value,
                        partition_key=partition_key_value,
                        tags={"source": "phlo", "backend": backend},
                    )
                )
                telemetry = TelemetryEventEmitter(
                    TelemetryEventContext(
                        tags={
                            "asset": asset_key_value,
                            "source": "phlo",
                            "backend": backend,
                        }
                    )
                )
                scope = PartitionScope(
                    partition_key=partition_key,
                    partition_column=partition_column,
                    rolling_window_days=rolling_window_days,
                    full_table=full_table,
                )
                final_query = apply_partition_scope(sql_query, scope=scope)
                if partition_key and not full_table:
                    runtime.logger.info(f"Validating partition: {partition_key}")

                try:
                    if backend == "trino":
                        trino = _resolve_trino_resource(runtime)
                        df = _load_data_trino(runtime, final_query, trino)
                    elif backend == "duckdb":
                        duckdb_conn = _resolve_duckdb_connection(runtime)
                        df = _load_data_duckdb(runtime, final_query, duckdb_conn)
                    else:
                        raise ValueError(f"Unknown backend: {backend}")
                except Exception as exc:
                    runtime.logger.error(f"Failed to load data: {exc}")
                    telemetry.emit_log(
                        name="quality.query_failed",
                        level="error",
                        payload={"error": str(exc), "table": table},
                    )
                    emitter.emit_result(
                        check_name=getattr(func, "__name__", "quality_check"),
                        passed=False,
                        severity="error",
                        check_type="phlo",
                        metadata={
                            "reason": "query_failed",
                            "error": str(exc),
                            "query_or_sql": final_query,
                            "table": table,
                        },
                    )
                    return CheckResult(
                        passed=False,
                        check_name=getattr(func, "__name__", "quality_check"),
                        asset_key=asset_key_value,
                        severity="error",
                        metadata={
                            "reason": "query_failed",
                            "error": str(exc),
                            "query": final_query,
                        },
                    )

                if df.empty:
                    runtime.logger.warning("No rows returned; marking check as skipped.")
                    emitter.emit_result(
                        check_name=getattr(func, "__name__", "quality_check"),
                        passed=True,
                        check_type="phlo",
                        metadata={
                            "note": "no_data",
                            "query_or_sql": final_query,
                            "table": table,
                        },
                    )
                    telemetry.emit_metric(
                        name="quality.rows_validated",
                        value=0,
                        unit="rows",
                        payload={"status": "no_data", "table": table},
                    )
                    return CheckResult(
                        passed=True,
                        check_name=getattr(func, "__name__", "quality_check"),
                        asset_key=asset_key_value,
                        metadata={
                            "rows_validated": 0,
                            "note": "No data available for validation",
                        },
                    )

                runtime.logger.info(
                    f"Executing {len(non_schema_checks)} quality checks on {len(df)} rows..."
                )

                check_results: List[QualityCheckResult] = []
                all_passed = True

                for check in non_schema_checks:
                    try:
                        result = check.execute(df, runtime)
                        check_results.append(result)

                        if not result.passed:
                            all_passed = False
                            runtime.logger.warning(
                                f"Quality check '{check.name}' failed: {result.failure_message}"
                            )
                        else:
                            runtime.logger.info(f"Quality check '{check.name}' passed")
                    except Exception as exc:
                        runtime.logger.exception(
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
                metadata.update(contract.to_metadata())

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
                    metadata["failures"] = "## Failed Checks\n\n" + "\n".join(
                        f"- {f}" for f in failed_checks
                    )
                metadata["summary"] = summary

                severity = severity_for_quality_check(
                    passed=all_passed,
                    failure_fraction=failure_fraction,
                    warn_threshold=warn_threshold,
                )
                if severity == "warn":
                    runtime.logger.warning(
                        f"Quality check warning: {failure_fraction:.1%} of checks failed "
                        f"(within warn threshold of {warn_threshold:.1%})"
                    )

                severity_label = severity if not all_passed else None
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
                    event_metadata["table"] = table
                    if result.metric_value is not None:
                        event_metadata["metric_value"] = result.metric_value
                    if result.failure_message:
                        event_metadata["failure_message"] = result.failure_message
                    if result.metadata:
                        event_metadata.update(result.metadata)
                    emitter.emit_result(
                        check_name=result.metric_name,
                        passed=result.passed,
                        severity=severity_label if not result.passed else None,
                        check_type=type(check).__name__,
                        metadata=event_metadata,
                    )

                telemetry.emit_metric(
                    name="quality.rows_validated",
                    value=len(df),
                    unit="rows",
                    payload={"table": table},
                )
                telemetry.emit_metric(
                    name="quality.checks_total",
                    value=len(check_results),
                    unit="checks",
                    payload={"table": table},
                )
                telemetry.emit_metric(
                    name="quality.checks_failed",
                    value=failed_count,
                    unit="checks",
                    payload={"table": table},
                )
                telemetry.emit_metric(
                    name="quality.failure_fraction",
                    value=failure_fraction,
                    unit="ratio",
                    payload={"table": table},
                )

                return CheckResult(
                    passed=all_passed,
                    check_name=getattr(func, "__name__", "quality_check"),
                    asset_key=asset_key_value,
                    severity=severity,
                    metadata=metadata,
                )

            quality_spec = AssetCheckSpec(
                name=getattr(func, "__name__", "quality_check"),
                asset_key=asset_key_value,
                fn=quality_check_wrapper,
                blocking=blocking,
                description=description,
            )
            _QUALITY_CHECKS.append(quality_spec)
            register_check(quality_spec)

        if schema_checks or non_schema_checks:
            return func

        raise ValueError("phlo_quality requires at least one check")

    return decorator


def get_quality_checks() -> list[Any]:
    """Get all asset check specs registered with @phlo_quality decorator."""
    return _QUALITY_CHECKS.copy()


def clear_quality_checks() -> None:
    """Clear registered quality check specs (useful for tests)."""
    _QUALITY_CHECKS.clear()


def _load_data_trino(context: RuntimeContext, query: str, trino: Any) -> Any:
    """Load data from Trino."""
    import pandas as pd

    # Execute query
    with trino.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

        if not cursor.description:
            raise ValueError("Trino did not return column metadata")

        columns = [desc[0] for desc in cursor.description]

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=columns)

    context.logger.info(f"Loaded {len(df)} rows from Trino")

    return df


def _resolve_trino_resource(context: RuntimeContext) -> Any:
    trino = None
    resources = context.resources
    if isinstance(resources, dict):
        trino = resources.get("trino")
    elif resources is not None:
        trino = getattr(resources, "trino", None)
    if trino is None:
        try:
            trino = context.get_resource("trino")
        except Exception:
            trino = None
    if trino is None:
        try:
            from phlo_trino.resource import TrinoResource
        except Exception as exc:  # noqa: BLE001 - surface missing backend cleanly
            raise ValueError(
                "Trino resource not found in context and phlo_trino is not available"
            ) from exc
        trino = TrinoResource()
    return trino


def _resolve_duckdb_connection(context: RuntimeContext) -> Any:
    duckdb_conn = None
    resources = context.resources
    if isinstance(resources, dict):
        duckdb_conn = resources.get("duckdb")
    elif resources is not None:
        duckdb_conn = getattr(resources, "duckdb", None)
    if duckdb_conn is None:
        try:
            duckdb_conn = context.get_resource("duckdb")
        except Exception:
            duckdb_conn = None
    if duckdb_conn is None:
        try:
            import duckdb
        except Exception as exc:  # noqa: BLE001 - surface missing backend cleanly
            raise ValueError(
                "DuckDB resource not found in context and duckdb is not available"
            ) from exc
        duckdb_conn = duckdb.connect()
    return duckdb_conn


def _load_data_duckdb(context: RuntimeContext, query: str, duckdb_conn: Any) -> Any:
    """Load data from DuckDB."""

    # Execute query
    df = duckdb_conn.execute(query).fetchdf()

    context.logger.info(f"Loaded {len(df)} rows from DuckDB")

    return df


def _build_metadata(df: Any, check_results: List[QualityCheckResult]) -> dict[str, Any]:
    """Build metadata dictionary for downstream consumers."""
    metadata: dict[str, Any] = {
        "rows_validated": len(df),
        "columns_validated": len(df.columns),
        "checks_executed": len(check_results),
        "checks_passed": sum(1 for r in check_results if r.passed),
        "checks_failed": sum(1 for r in check_results if not r.passed),
    }

    # Add individual check results
    for result in check_results:
        # Add metric value
        if result.metric_value is not None:
            metadata[f"{result.metric_name}_value"] = result.metric_value

        # Add check metadata
        if result.metadata:
            for key, value in result.metadata.items():
                metadata_key = f"{result.metric_name}_{key}"
                metadata[metadata_key] = value

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
        metadata["quality_summary"] = summary_table

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


def _repro_sql(query: str) -> str:
    return f"SELECT *\nFROM (\n{query}\n) AS phlo_quality\nLIMIT 100"
