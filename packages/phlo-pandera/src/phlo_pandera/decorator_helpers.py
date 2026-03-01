"""Private helper functions for the @phlo_pandera decorator."""

from __future__ import annotations

from typing import Any, List

from phlo.capabilities.runtime import RuntimeContext
from phlo.hooks import (
    QualityResultEventContext,
    QualityResultEventEmitter,
    TelemetryEventContext,
    TelemetryEventEmitter,
)

from phlo_pandera.checks import QualityCheckResult
from phlo_pandera.contract import QualityCheckContract


def _make_emitters(
    asset_key: str,
    partition_key_value: str | None,
    source: str,
    backend: str,
) -> tuple[QualityResultEventEmitter, TelemetryEventEmitter]:
    """Create quality-result and telemetry emitters."""
    emitter = QualityResultEventEmitter(
        QualityResultEventContext(
            asset_key=asset_key,
            partition_key=partition_key_value,
            tags={"source": source, "backend": backend},
        )
    )
    telemetry = TelemetryEventEmitter(
        TelemetryEventContext(
            tags={
                "asset": asset_key,
                "source": source,
                "backend": backend,
            }
        )
    )
    return emitter, telemetry


def _load_data(
    runtime: RuntimeContext,
    query: str,
    backend: str,
) -> Any:
    """Resolve the backend resource and load data as a DataFrame."""
    if backend == "trino":
        trino = _resolve_trino_resource(runtime)
        return _load_data_trino(runtime, query, trino)
    elif backend == "duckdb":
        duckdb_conn = _resolve_duckdb_connection(runtime)
        return _load_data_duckdb(runtime, query, duckdb_conn)
    else:
        raise ValueError(f"Unknown backend: {backend}")


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

    context.logger.info("loaded_rows_from_trino", row_count=len(df))

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

    context.logger.info("loaded_rows_from_duckdb", row_count=len(df))

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
    return f"SELECT *\nFROM (\n{query}\n) AS phlo_pandera\nLIMIT 100"
