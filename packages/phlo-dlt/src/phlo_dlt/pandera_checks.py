"""Pandera contract checks for DLT ingestion assets.

This module provides Pandera schema validation integration for DLT-based
ingestion pipelines. It handles the evaluation of data contracts against
staged Parquet files and converts validation results into Phlo-compatible
check results.

Key Components:
    - :class:`PanderaContractEvaluation`: Result container for validation outcomes
    - :class:`PanderaContractValidationError`: Exception for validation failures
    - :func:`evaluate_pandera_contract`: Validate DataFrame against schema
    - :func:`evaluate_pandera_contract_parquet`: Validate single Parquet file
    - :func:`evaluate_pandera_contract_parquet_files`: Validate multiple Parquet files
    - :func:`pandera_contract_asset_check_result`: Convert to Phlo check result
    - :func:`serialize_pandera_contract_evaluation`: Serialize evaluation to dict
    - :func:`deserialize_pandera_contract_evaluation`: Deserialize from dict

Validation Flow:
    1. DLT extracts data to Parquet files
    2. Parquet files are validated against Pandera schema
    3. Results are converted to Phlo check results
    4. In strict mode, failures abort before data is visible

See Also:
    - :mod:`phlo_dlt.decorator`: Decorator that orchestrates validation
    - :mod:`phlo_dlt.executor`: Executor that triggers validation
    - Pandera documentation: https://pandera.readthedocs.io/

"""

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
    """Result summary for Pandera schema contract evaluation.

    This dataclass captures the outcome of validating data against a Pandera
    schema, including pass/fail status, counts of failed/total records,
    sample failure cases, and any error messages.

    Attributes:
        passed: Whether validation passed (True) or failed (False).
        failed_count: Number of records that failed validation.
        total_count: Total number of records evaluated.
        sample: List of dicts containing up to 20 sample failure cases.
        error: Error message if validation raised an exception, else None.

    Example:
        ```python
        evaluation = PanderaContractEvaluation(
            passed=True,
            failed_count=0,
            total_count=1000,
            sample=[],
            error=None,
        )
        ```

    """

    passed: bool
    failed_count: int
    total_count: int
    sample: list[dict[str, Any]]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PanderaContractValidationError(RuntimeError):
    """Raised when strict Pandera validation fails before a visible write.

    This exception is raised when strict validation is enabled and the
    Pandera contract check fails. It includes the evaluation details and
    paths to the Parquet files that failed validation.

    Attributes:
        evaluation: Detailed evaluation result with failure information.
        parquet_paths: Tuple of paths to the Parquet files that were validated.

    Raises:
        RuntimeError: Base class with message "Pandera contract validation failed".

    Example:
        ```python
        try:
            evaluation = evaluate_pandera_contract_parquet(path, schema_class=MySchema)
            if not evaluation.passed:
                raise PanderaContractValidationError(
                    evaluation=evaluation,
                    parquet_paths=(path,)
                )
        except PanderaContractValidationError as e:
            print(f"Validation failed: {e.evaluation.error}")
        ```

    """

    evaluation: PanderaContractEvaluation
    parquet_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        """Initialize the RuntimeError base class with a standard message."""
        RuntimeError.__init__(self, "Pandera contract validation failed")


def evaluate_pandera_contract_parquet(
    parquet_path: Path,
    *,
    schema_class: type[DataFrameModel],
) -> PanderaContractEvaluation:
    """Load parquet data and validate it against a Pandera schema class.

    Reads a Parquet file into a pandas DataFrame and validates it against
    the provided Pandera schema class.

    Args:
        parquet_path: Path to the Parquet file to validate.
        schema_class: Pandera DataFrameModel subclass defining validation rules.

    Returns:
        PanderaContractEvaluation: Result of the validation.

    Example:
        ```python
        from pathlib import Path
        from phlo_dlt.pandera_checks import evaluate_pandera_contract_parquet

        result = evaluate_pandera_contract_parquet(
            Path("/tmp/data.parquet"),
            schema_class=UserSchema,
        )
        print(f"Passed: {result.passed}, Failed: {result.failed_count}")
        ```

    See Also:
        :func:`evaluate_pandera_contract`: Core validation logic.
        :func:`evaluate_pandera_contract_parquet_files`: For multiple files.

    """
    df = pd.read_parquet(parquet_path)
    return evaluate_pandera_contract(df, schema_class=schema_class)


def evaluate_pandera_contract_parquet_files(
    parquet_paths: list[Path],
    *,
    schema_class: type[DataFrameModel],
) -> PanderaContractEvaluation:
    """Load one or more parquet files and validate them as a single staged dataset.

    Reads multiple Parquet files, concatenates them into a single DataFrame,
    and validates against the provided schema. This is useful when DLT
    produces multiple Parquet files for a single ingestion run.

    Args:
        parquet_paths: List of paths to Parquet files to validate.
        schema_class: Pandera DataFrameModel subclass defining validation rules.

    Returns:
        PanderaContractEvaluation: Combined result of the validation.

    Raises:
        FileNotFoundError: If parquet_paths is empty.

    Example:
        ```python
        from pathlib import Path
        from phlo_dlt.pandera_checks import evaluate_pandera_contract_parquet_files

        paths = [Path("/tmp/part1.parquet"), Path("/tmp/part2.parquet")]
        result = evaluate_pandera_contract_parquet_files(
            paths,
            schema_class=UserSchema,
        )
        ```

    See Also:
        :func:`evaluate_pandera_contract_parquet`: For single file validation.

    """
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
    """Validate a dataframe against a Pandera schema class.

    Performs comprehensive validation of a pandas DataFrame against a
    Pandera schema. Handles datetime coercion, nullable column defaults,
    and provides detailed failure information.

    Args:
        df: pandas DataFrame to validate.
        schema_class: Pandera DataFrameModel subclass defining validation rules.

    Returns:
        PanderaContractEvaluation: Detailed validation result.

    Validation Steps:
        1. Add null columns for missing nullable fields
        2. Coerce datetime columns to proper type
        3. Run Pandera validation
        4. Capture any SchemaErrors or exceptions

    Example:
        ```python
        import pandas as pd
        from phlo_dlt.pandera_checks import evaluate_pandera_contract

        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        result = evaluate_pandera_contract(df, schema_class=UserSchema)
        ```

    """
    schema = schema_class.to_schema()
    missing_nullable = [
        name for name, col in schema.columns.items() if col.nullable and name not in df.columns
    ]
    if missing_nullable:
        validated_df = df.copy()
        for column_name in missing_nullable:
            validated_df[column_name] = None
    else:
        validated_df = df

    datetime_columns = [
        name
        for name, column in schema.columns.items()
        if isinstance(column.dtype, pandas_engine.DateTime)
    ]
    for column_name in datetime_columns:
        if column_name not in validated_df.columns:
            continue
        series = validated_df[column_name]
        if pd.api.types.is_datetime64_any_dtype(series):
            continue
        if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
            continue
        try:
            if validated_df is df:
                validated_df = df.copy()
            validated_df[column_name] = pd.to_datetime(series)
        except (ValueError, TypeError):
            pass

    try:
        schema_class.validate(validated_df, lazy=True)
    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        sample = failure_cases.head(20).to_dict(orient="records")
        return PanderaContractEvaluation(
            passed=False,
            failed_count=len(failure_cases),
            total_count=len(validated_df),
            sample=sample,
            error=str(err),
        )
    except Exception as exc:  # noqa: BLE001 - surface validation errors in check metadata
        return PanderaContractEvaluation(
            passed=False,
            failed_count=1,
            total_count=len(validated_df),
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
    """Build a normalized Phlo check result from Pandera evaluation output.

    Converts a PanderaContractEvaluation into a Phlo CheckResult that can
    be consumed by the Phlo orchestrator and displayed in the UI.

    Args:
        evaluation: The Pandera validation evaluation to convert.
        partition_key: Optional partition key for the check context.
        asset_key: Asset identifier (e.g., "dlt_users").
        schema_class: Pandera schema class used for validation.
        query_or_sql: Query string or SQL describing the data source.

    Returns:
        CheckResult: Normalized Phlo check result.

    Example:
        ```python
        from phlo_dlt.pandera_checks import (
            evaluate_pandera_contract_parquet,
            pandera_contract_asset_check_result,
        )

        evaluation = evaluate_pandera_contract_parquet(path, schema_class=MySchema)
        check_result = pandera_contract_asset_check_result(
            evaluation,
            partition_key="2024-01-01",
            asset_key="dlt_users",
            schema_class=MySchema,
            query_or_sql="parquet:///tmp/data.parquet",
        )
        ```

    """
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
    """Convert a Pandera contract evaluation to metadata-safe primitives.

    Serializes the evaluation for storage in ingestion metadata, allowing
    results to be passed between pipeline stages or stored for auditing.

    Args:
        evaluation: The evaluation to serialize.

    Returns:
        dict[str, Any]: Dictionary with primitive values suitable for metadata.

    Example:
        ```python
        evaluation = PanderaContractEvaluation(
            passed=True, failed_count=0, total_count=100, sample=[], error=None
        )
        metadata = serialize_pandera_contract_evaluation(evaluation)
        # Can now be stored in JSON/YAML metadata
        ```

    See Also:
        :func:`deserialize_pandera_contract_evaluation`: Reverse operation.

    """
    return {
        "passed": evaluation.passed,
        "failed_count": evaluation.failed_count,
        "total_count": evaluation.total_count,
        "sample": evaluation.sample,
        "error": evaluation.error,
    }


def deserialize_pandera_contract_evaluation(payload: Any) -> PanderaContractEvaluation | None:
    """Convert metadata payload back into a Pandera contract evaluation.

    Deserializes an evaluation from metadata storage. Handles type coercion
    and validation of the payload structure.

    Args:
        payload: Dictionary from metadata storage, typically from
            :func:`serialize_pandera_contract_evaluation`.

    Returns:
        PanderaContractEvaluation | None: The deserialized evaluation, or None
        if payload is not a valid dictionary.

    Example:
        ```python
        metadata = {"passed": True, "failed_count": 0, "total_count": 100, "sample": []}
        evaluation = deserialize_pandera_contract_evaluation(metadata)
        if evaluation:
            print(f"Validation passed: {evaluation.passed}")
        ```

    See Also:
        :func:`serialize_pandera_contract_evaluation`: Forward operation.

    """
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
