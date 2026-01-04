from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pandera.errors
from pandera.engines import pandas_engine
from pandera.pandas import DataFrameModel

from phlo.capabilities.specs import CheckResult
from phlo_quality.contract import PANDERA_CONTRACT_CHECK_NAME, QualityCheckContract
from phlo_quality.severity import severity_for_pandera_contract


@dataclass(frozen=True, slots=True)
class PanderaContractEvaluation:
    passed: bool
    failed_count: int
    total_count: int
    sample: list[dict[str, Any]]
    error: str | None = None


def evaluate_pandera_contract(
    df: pd.DataFrame,
    *,
    schema_class: type[DataFrameModel],
) -> PanderaContractEvaluation:
    schema = schema_class.to_schema()
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
    except Exception as exc:
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


def evaluate_pandera_contract_parquet(
    parquet_path: Path,
    *,
    schema_class: type[DataFrameModel],
) -> PanderaContractEvaluation:
    df = pd.read_parquet(parquet_path)
    return evaluate_pandera_contract(df, schema_class=schema_class)


def pandera_contract_asset_check_result(
    evaluation: PanderaContractEvaluation,
    *,
    partition_key: str | None,
    asset_key: str,
    schema_class: type[DataFrameModel],
    query_or_sql: str,
) -> CheckResult:
    contract = QualityCheckContract(
        source="pandera",
        partition_key=partition_key,
        failed_count=evaluation.failed_count,
        total_count=evaluation.total_count,
        query_or_sql=query_or_sql,
        repro_sql=None,
        sample=evaluation.sample,
    )
    metadata: dict[str, Any] = {
        **contract.to_metadata(),
        "schema": schema_class.__name__,
    }
    if evaluation.error:
        metadata["error"] = evaluation.error

    severity = severity_for_pandera_contract(passed=evaluation.passed)
    return CheckResult(
        passed=evaluation.passed,
        check_name=PANDERA_CONTRACT_CHECK_NAME,
        metadata=metadata,
        severity=severity,
        asset_key=asset_key,
    )
