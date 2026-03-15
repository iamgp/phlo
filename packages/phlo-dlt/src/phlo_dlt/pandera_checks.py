"""Pandera contract checks for DLT ingestion assets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pandera.errors
from pandera.engines import pandas_engine
from pandera.pandas import DataFrameModel

from phlo.capabilities.specs import CheckResult

PANDERA_CONTRACT_CHECK_NAME = "pandera_contract"


@dataclass(frozen=True, slots=True)
class PanderaContractEvaluation:
    """Result summary for Pandera schema contract evaluation."""

    passed: bool
    failed_count: int
    total_count: int
    sample: list[dict[str, Any]]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PanderaContractValidationError(RuntimeError):
    """Raised when strict Pandera validation fails before a visible write."""

    evaluation: PanderaContractEvaluation
    parquet_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, "Pandera contract validation failed")


def evaluate_pandera_contract_parquet(
    parquet_path: Path,
    *,
    schema_class: type[DataFrameModel],
) -> PanderaContractEvaluation:
    """Load parquet data and validate it against a Pandera schema class."""
    df = pd.read_parquet(parquet_path)
    return evaluate_pandera_contract(df, schema_class=schema_class)


def evaluate_pandera_contract_parquet_files(
    parquet_paths: list[Path],
    *,
    schema_class: type[DataFrameModel],
) -> PanderaContractEvaluation:
    """Load one or more parquet files and validate them as a single staged dataset."""
    if not parquet_paths:
        raise FileNotFoundError("Missing parquet_paths in ingestion metadata")
    frames = [pd.read_parquet(parquet_path) for parquet_path in parquet_paths]
    return evaluate_pandera_contract(
        pd.concat(frames, ignore_index=True), schema_class=schema_class
    )


def evaluate_pandera_contract(
    df: pd.DataFrame,
    *,
    schema_class: type[DataFrameModel],
) -> PanderaContractEvaluation:
    """Validate a dataframe against a Pandera schema class."""
    schema = schema_class.to_schema()
    for column_name, column in schema.columns.items():
        if column_name in df.columns or not column.nullable:
            continue
        df[column_name] = None

    datetime_columns = [
        name
        for name, column in schema.columns.items()
        if isinstance(column.dtype, pandas_engine.DateTime)
    ]
    for column_name in datetime_columns:
        if column_name not in df.columns:
            continue
        series = df[column_name]
        if pd.api.types.is_datetime64_any_dtype(series):
            continue
        if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
            continue
        try:
            df[column_name] = pd.to_datetime(series)
        except (ValueError, TypeError):
            pass

    try:
        schema_class.validate(df, lazy=True)
    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        sample = failure_cases.head(20).to_dict(orient="records")
        return PanderaContractEvaluation(
            passed=False,
            failed_count=len(failure_cases),
            total_count=len(df),
            sample=sample,
            error=str(err),
        )
    except Exception as exc:  # noqa: BLE001 - surface validation errors in check metadata
        return PanderaContractEvaluation(
            passed=False,
            failed_count=1,
            total_count=len(df),
            sample=[{"error": str(exc)}],
            error=str(exc),
        )

    return PanderaContractEvaluation(
        passed=True,
        failed_count=0,
        total_count=len(df),
        sample=[],
    )


def pandera_contract_asset_check_result(
    evaluation: PanderaContractEvaluation,
    *,
    partition_key: str | None,
    asset_key: str,
    schema_class: type[DataFrameModel],
    query_or_sql: str,
) -> CheckResult:
    """Build a normalized Phlo check result from Pandera evaluation output."""
    metadata: dict[str, Any] = {
        "source": "pandera",
        "partition_key": partition_key,
        "failed_count": evaluation.failed_count,
        "total_count": evaluation.total_count,
        "query_or_sql": query_or_sql,
        "sample": evaluation.sample[:20],
        "schema": schema_class.__name__,
    }
    if evaluation.error:
        metadata["error"] = evaluation.error

    return CheckResult(
        passed=evaluation.passed,
        check_name=PANDERA_CONTRACT_CHECK_NAME,
        metadata=metadata,
        severity=None if evaluation.passed else "error",
        asset_key=asset_key,
    )


def serialize_pandera_contract_evaluation(
    evaluation: PanderaContractEvaluation,
) -> dict[str, Any]:
    """Convert a Pandera contract evaluation to metadata-safe primitives."""
    return {
        "passed": evaluation.passed,
        "failed_count": evaluation.failed_count,
        "total_count": evaluation.total_count,
        "sample": evaluation.sample,
        "error": evaluation.error,
    }


def deserialize_pandera_contract_evaluation(payload: Any) -> PanderaContractEvaluation | None:
    """Convert metadata payload back into a Pandera contract evaluation."""
    if not isinstance(payload, dict):
        return None
    sample = payload.get("sample")
    return PanderaContractEvaluation(
        passed=bool(payload.get("passed")),
        failed_count=int(payload.get("failed_count", 0)),
        total_count=int(payload.get("total_count", 0)),
        sample=sample if isinstance(sample, list) else [],
        error=str(payload["error"]) if payload.get("error") is not None else None,
    )
