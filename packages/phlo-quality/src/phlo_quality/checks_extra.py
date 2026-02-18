"""
Extra quality check classes: CustomSQLCheck, PatternCheck, SchemaCheck.

Split from checks.py to keep individual modules under 500 LOC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import pandera.errors as pa_errors

from phlo.capabilities.runtime import RuntimeContext
from phlo.logging import get_logger

from phlo_quality.checks import QualityCheck, QualityCheckResult

logger = get_logger(__name__)


@dataclass
class SchemaCheck(QualityCheck):
    """
    Check that DataFrame matches a Pandera schema.

    Example:
        ```python
        from workflows.schemas.weather import WeatherObservations
        SchemaCheck(schema=WeatherObservations)
        ```
    """

    schema: Any
    """Pandera DataFrameModel or schema to validate against."""

    lazy: bool = True
    """Use lazy validation to collect all errors."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute schema check on DataFrame."""
        try:
            # Validate with Pandera
            self.schema.validate(df, lazy=self.lazy)

            return QualityCheckResult(
                passed=True,
                metric_name="schema_check",
                metric_value={"schema_valid": True},
                metadata={
                    "schema_name": getattr(self.schema, "__name__", str(type(self.schema))),
                    "rows_validated": len(df),
                    "columns_validated": len(df.columns),
                },
            )

        except pa_errors.SchemaErrors as err:
            failure_cases = err.failure_cases

            failures_by_column = failure_cases.groupby("column").size().to_dict()
            failures_by_check = failure_cases.groupby("check").size().to_dict()

            return QualityCheckResult(
                passed=False,
                metric_name="schema_check",
                metric_value={"schema_valid": False},
                metadata={
                    "schema_name": getattr(self.schema, "__name__", str(type(self.schema))),
                    "rows_evaluated": len(df),
                    "failed_checks": len(failure_cases),
                    "failures_by_column": failures_by_column,
                    "failures_by_check": failures_by_check,
                    "sample_failures": failure_cases.head(10).to_dict(orient="records"),
                },
                failure_message=f"Schema validation failed with {len(failure_cases)} errors",
            )

        except Exception as exc:
            logger.exception(
                "schema_check_execution_failed",
                schema_name=getattr(self.schema, "__name__", type(self.schema).__name__),
                row_count=len(df),
                column_count=len(df.columns),
            )
            return QualityCheckResult(
                passed=False,
                metric_name="schema_check",
                metric_value={"schema_valid": False},
                metadata={"error": str(exc)},
                failure_message=f"Unexpected error during schema validation: {exc}",
            )

    @property
    def name(self) -> str:
        """Get the check name.

        Returns:
            Stable metric name for this schema check.
        """
        schema_name = getattr(self.schema, "__name__", "schema")
        return f"schema_check_{schema_name}"


@dataclass
class CustomSQLCheck(QualityCheck):
    """
    Execute arbitrary SQL to validate data.

    The SQL should return a single boolean column (or NULL for skipped rows).
    Rows that are FALSE indicate quality violations.

    Example:
        ```python
        CustomSQLCheck(
            name="temperature_consistency",
            sql="SELECT (max_temp >= min_temp) FROM weather_observations"
        )
        ```
    """

    name_: str
    """Name of this check."""

    sql: str
    """SQL query that returns TRUE for valid rows, FALSE for invalid rows."""

    expected: bool = True
    """Expected result (default: TRUE for all rows valid)."""

    allow_threshold: float = 0.0
    """Maximum fraction of failures allowed."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute custom SQL check on DataFrame."""
        try:
            # Execute SQL in pandas context
            # This requires DuckDB or similar for SQL execution
            import duckdb

            # Register DataFrame as a view
            conn = duckdb.connect(":memory:")
            conn.register("data", df)

            # Execute the check query
            result = conn.execute(self.sql).fetchall()

            if not result:
                return QualityCheckResult(
                    passed=True,
                    metric_name=self.name_,
                    metric_value={"rows_checked": 0},
                    metadata={"note": "No data returned from check query"},
                )

            # Count failures (where result is False or not expected value)
            failures = sum(1 for (row_result,) in result if row_result != self.expected)
            failure_pct = failures / len(result) if result else 0.0

            passed = failure_pct <= self.allow_threshold

            failure_msg = None
            if not passed:
                failure_msg = (
                    f"Custom SQL check failed: {failure_pct:.2%} of rows failed validation "
                    f"(threshold: {self.allow_threshold:.2%})"
                )

            return QualityCheckResult(
                passed=passed,
                metric_name=self.name_,
                metric_value={"failures": failures, "total": len(result)},
                metadata={
                    "failure_count": failures,
                    "total_rows": len(result),
                    "failure_percentage": float(failure_pct),
                    "threshold": self.allow_threshold,
                },
                failure_message=failure_msg,
            )

        except ImportError:
            logger.warning(
                "custom_sql_check_duckdb_missing",
                check_name=self.name_,
            )
            return QualityCheckResult(
                passed=False,
                metric_name=self.name_,
                metric_value=None,
                failure_message="DuckDB not available for custom SQL check",
            )
        except Exception as exc:
            logger.exception(
                "custom_sql_check_execution_failed",
                check_name=self.name_,
                expected=self.expected,
                sql_length=len(self.sql),
            )
            return QualityCheckResult(
                passed=False,
                metric_name=self.name_,
                metric_value=None,
                metadata={"error": str(exc)},
                failure_message=f"Custom SQL check failed: {exc}",
            )

    @property
    def name(self) -> str:
        """Get the check name.

        Returns:
            Stable metric name for this custom SQL check.
        """
        return f"custom_sql_{self.name_}"


@dataclass
class PatternCheck(QualityCheck):
    r"""
    Check that string column values match a regex pattern.

    Example:
        ```python
        PatternCheck(
            column="email",
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        PatternCheck(
            column="postal_code",
            pattern=r"^\d{5}(-\d{4})?$",
            allow_threshold=0.05  # Allow 5% invalid
        )
        ```
    """

    column: str
    """Column to check."""

    pattern: str
    """Regex pattern that values must match."""

    allow_threshold: float = 0.0
    """Maximum fraction of non-matching values allowed."""

    case_sensitive: bool = True
    """Whether pattern matching is case sensitive."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute pattern check on DataFrame."""
        if self.column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="pattern_check",
                metric_value=None,
                failure_message=f"Column '{self.column}' not found in DataFrame",
            )

        column_data = df[self.column].dropna().astype(str)

        if len(column_data) == 0:
            return QualityCheckResult(
                passed=True,
                metric_name="pattern_check",
                metric_value={"matches": 0, "non_matches": 0},
                metadata={"note": "No non-null values to check"},
            )

        import re

        flags = 0 if self.case_sensitive else re.IGNORECASE
        pattern_compiled = re.compile(self.pattern, flags)

        matches = column_data.str.match(pattern_compiled, na=False)
        non_match_count = (~matches).sum()
        non_match_pct = non_match_count / len(column_data)

        passed = non_match_pct <= self.allow_threshold

        failure_msg = None
        if not passed:
            sample_non_matches = column_data[~matches].head(5).tolist()
            failure_msg = (
                f"Column '{self.column}' has {non_match_pct:.2%} values not matching pattern "
                f"(threshold: {self.allow_threshold:.2%}). "
                f"Sample non-matches: {sample_non_matches}"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="pattern_check",
            metric_value={
                "matches": int(matches.sum()),
                "non_matches": int(non_match_count),
            },
            metadata={
                "pattern": self.pattern,
                "case_sensitive": self.case_sensitive,
                "match_count": int(matches.sum()),
                "non_match_count": int(non_match_count),
                "non_match_percentage": float(non_match_pct),
                "threshold": self.allow_threshold,
                "total_rows": len(column_data),
                "sample_rows": [
                    {"row_index": idx if isinstance(idx, int) else str(idx), self.column: value}
                    for idx, value in column_data[~matches].head(20).items()
                ],
            },
            failure_message=failure_msg,
        )

    @property
    def name(self) -> str:
        """Get the check name.

        Returns:
            Stable metric name for this pattern check.
        """
        return f"pattern_check_{self.column}"
