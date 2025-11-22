"""
Quality check classes for declarative data validation.

These classes define quality checks that can be applied to tables
and automatically wrapped into Dagster asset checks via @phlo_quality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import pandera as pa


@dataclass
class QualityCheckResult:
    """Result from executing a quality check."""

    passed: bool
    """Whether the quality check passed."""

    metric_name: str
    """Name of the quality metric."""

    metric_value: Any
    """Value of the quality metric."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the check."""

    failure_message: Optional[str] = None
    """Human-readable failure message if check failed."""


class QualityCheck(ABC):
    """
    Base class for quality checks.

    All quality checks must implement the `execute` method which
    validates data and returns a QualityCheckResult.
    """

    @abstractmethod
    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """
        Execute the quality check on the given DataFrame.

        Args:
            df: DataFrame to validate
            context: Dagster context for logging

        Returns:
            QualityCheckResult with pass/fail status and metadata
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this check."""
        pass


@dataclass
class NullCheck(QualityCheck):
    """
    Check that specified columns have no null values.

    Example:
        ```python
        NullCheck(columns=["station_id", "temperature"])
        ```
    """

    columns: List[str]
    """List of columns that must not contain nulls."""

    allow_threshold: float = 0.0
    """Maximum fraction of nulls allowed (0.0 = no nulls, 0.05 = 5% nulls)."""

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Execute null check on DataFrame."""
        null_counts = {}
        null_percentages = {}
        failures = []

        for column in self.columns:
            if column not in df.columns:
                failures.append(f"Column '{column}' not found in DataFrame")
                continue

            null_count = df[column].isna().sum()
            null_pct = null_count / len(df) if len(df) > 0 else 0.0

            null_counts[column] = int(null_count)
            null_percentages[column] = float(null_pct)

            if null_pct > self.allow_threshold:
                failures.append(
                    f"Column '{column}' has {null_pct:.2%} nulls "
                    f"(threshold: {self.allow_threshold:.2%})"
                )

        passed = len(failures) == 0

        return QualityCheckResult(
            passed=passed,
            metric_name="null_check",
            metric_value=null_counts,
            metadata={
                "null_counts": null_counts,
                "null_percentages": null_percentages,
                "threshold": self.allow_threshold,
                "columns_checked": self.columns,
            },
            failure_message="; ".join(failures) if failures else None,
        )

    @property
    def name(self) -> str:
        return f"null_check_{'+'.join(self.columns)}"


@dataclass
class RangeCheck(QualityCheck):
    """
    Check that numeric column values are within specified range.

    Example:
        ```python
        RangeCheck(column="temperature", min_value=-50, max_value=60)
        ```
    """

    column: str
    """Column to check."""

    min_value: Optional[float] = None
    """Minimum allowed value (inclusive)."""

    max_value: Optional[float] = None
    """Maximum allowed value (inclusive)."""

    allow_threshold: float = 0.0
    """Maximum fraction of out-of-range values allowed."""

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Execute range check on DataFrame."""
        if self.column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="range_check",
                metric_value=None,
                failure_message=f"Column '{self.column}' not found in DataFrame",
            )

        column_data = df[self.column].dropna()

        if len(column_data) == 0:
            return QualityCheckResult(
                passed=True,
                metric_name="range_check",
                metric_value={"min": None, "max": None, "out_of_range": 0},
                metadata={"note": "No non-null values to check"},
            )

        # Check range violations
        violations = pd.Series([False] * len(column_data), index=column_data.index)

        if self.min_value is not None:
            violations |= column_data < self.min_value

        if self.max_value is not None:
            violations |= column_data > self.max_value

        violation_count = violations.sum()
        violation_pct = violation_count / len(column_data)

        passed = violation_pct <= self.allow_threshold

        actual_min = float(column_data.min())
        actual_max = float(column_data.max())

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Column '{self.column}' has {violation_pct:.2%} out-of-range values "
                f"(threshold: {self.allow_threshold:.2%}). "
                f"Expected range: [{self.min_value}, {self.max_value}], "
                f"Actual range: [{actual_min}, {actual_max}]"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="range_check",
            metric_value={
                "min": actual_min,
                "max": actual_max,
                "out_of_range": int(violation_count),
            },
            metadata={
                "expected_min": self.min_value,
                "expected_max": self.max_value,
                "actual_min": actual_min,
                "actual_max": actual_max,
                "violation_count": int(violation_count),
                "violation_percentage": float(violation_pct),
                "threshold": self.allow_threshold,
            },
            failure_message=failure_msg,
        )

    @property
    def name(self) -> str:
        return f"range_check_{self.column}"


@dataclass
class FreshnessCheck(QualityCheck):
    """
    Check that data is fresh (not stale).

    Example:
        ```python
        FreshnessCheck(timestamp_column="observation_time", max_age_hours=2)
        ```
    """

    timestamp_column: str
    """Column containing timestamps to check."""

    max_age_hours: float
    """Maximum age in hours for data to be considered fresh."""

    reference_time: Optional[datetime] = None
    """Reference time to compare against (defaults to now)."""

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Execute freshness check on DataFrame."""
        if self.timestamp_column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="freshness_check",
                metric_value=None,
                failure_message=f"Column '{self.timestamp_column}' not found in DataFrame",
            )

        # Convert to datetime if needed
        timestamp_data = pd.to_datetime(df[self.timestamp_column])

        if len(timestamp_data.dropna()) == 0:
            return QualityCheckResult(
                passed=True,
                metric_name="freshness_check",
                metric_value={"max_age_hours": None},
                metadata={"note": "No non-null timestamps to check"},
            )

        # Get most recent timestamp
        max_timestamp = timestamp_data.max()

        # Calculate age
        reference = self.reference_time or datetime.now(tz=max_timestamp.tzinfo)
        age = reference - max_timestamp
        age_hours = age.total_seconds() / 3600

        passed = age_hours <= self.max_age_hours

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Data is stale. Most recent timestamp is {age_hours:.2f} hours old "
                f"(threshold: {self.max_age_hours:.2f} hours)"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="freshness_check",
            metric_value={"max_age_hours": float(age_hours)},
            metadata={
                "max_timestamp": str(max_timestamp),
                "reference_time": str(reference),
                "age_hours": float(age_hours),
                "threshold_hours": self.max_age_hours,
            },
            failure_message=failure_msg,
        )

    @property
    def name(self) -> str:
        return f"freshness_check_{self.timestamp_column}"


@dataclass
class UniqueCheck(QualityCheck):
    """
    Check that specified columns have unique values (no duplicates).

    Example:
        ```python
        UniqueCheck(columns=["station_id"])
        ```
    """

    columns: List[str]
    """List of columns that must have unique combinations."""

    allow_threshold: float = 0.0
    """Maximum fraction of duplicates allowed."""

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Execute uniqueness check on DataFrame."""
        missing_columns = [col for col in self.columns if col not in df.columns]

        if missing_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="unique_check",
                metric_value=None,
                failure_message=f"Columns not found: {', '.join(missing_columns)}",
            )

        # Check for duplicates
        duplicates = df.duplicated(subset=self.columns, keep=False)
        duplicate_count = duplicates.sum()
        duplicate_pct = duplicate_count / len(df) if len(df) > 0 else 0.0

        passed = duplicate_pct <= self.allow_threshold

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Found {duplicate_count} duplicate rows ({duplicate_pct:.2%}) "
                f"in columns {self.columns} (threshold: {self.allow_threshold:.2%})"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="unique_check",
            metric_value={"duplicate_count": int(duplicate_count)},
            metadata={
                "duplicate_count": int(duplicate_count),
                "duplicate_percentage": float(duplicate_pct),
                "threshold": self.allow_threshold,
                "columns_checked": self.columns,
                "total_rows": len(df),
            },
            failure_message=failure_msg,
        )

    @property
    def name(self) -> str:
        return f"unique_check_{'+'.join(self.columns)}"


@dataclass
class CountCheck(QualityCheck):
    """
    Check that row count meets expectations.

    Example:
        ```python
        CountCheck(min_rows=100)
        CountCheck(min_rows=100, max_rows=10000)
        ```
    """

    min_rows: Optional[int] = None
    """Minimum expected row count."""

    max_rows: Optional[int] = None
    """Maximum expected row count."""

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Execute count check on DataFrame."""
        row_count = len(df)

        failures = []

        if self.min_rows is not None and row_count < self.min_rows:
            failures.append(f"Row count {row_count} is below minimum {self.min_rows}")

        if self.max_rows is not None and row_count > self.max_rows:
            failures.append(f"Row count {row_count} is above maximum {self.max_rows}")

        passed = len(failures) == 0

        return QualityCheckResult(
            passed=passed,
            metric_name="count_check",
            metric_value={"row_count": row_count},
            metadata={
                "row_count": row_count,
                "min_rows": self.min_rows,
                "max_rows": self.max_rows,
            },
            failure_message="; ".join(failures) if failures else None,
        )

    @property
    def name(self) -> str:
        return "count_check"


@dataclass
class SchemaCheck(QualityCheck):
    """
    Check that DataFrame matches a Pandera schema.

    Example:
        ```python
        from phlo.schemas.weather import WeatherObservations
        SchemaCheck(schema=WeatherObservations)
        ```
    """

    schema: Any
    """Pandera DataFrameModel or schema to validate against."""

    lazy: bool = True
    """Use lazy validation to collect all errors."""

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Execute schema check on DataFrame."""
        try:
            # Validate with Pandera
            self.schema.validate(df, lazy=self.lazy)

            return QualityCheckResult(
                passed=True,
                metric_name="schema_check",
                metric_value={"schema_valid": True},
                metadata={
                    "schema_name": getattr(
                        self.schema, "__name__", str(type(self.schema))
                    ),
                    "rows_validated": len(df),
                    "columns_validated": len(df.columns),
                },
            )

        except pa.errors.SchemaErrors as err:
            failure_cases = err.failure_cases

            failures_by_column = failure_cases.groupby("column").size().to_dict()
            failures_by_check = failure_cases.groupby("check").size().to_dict()

            return QualityCheckResult(
                passed=False,
                metric_name="schema_check",
                metric_value={"schema_valid": False},
                metadata={
                    "schema_name": getattr(
                        self.schema, "__name__", str(type(self.schema))
                    ),
                    "rows_evaluated": len(df),
                    "failed_checks": len(failure_cases),
                    "failures_by_column": failures_by_column,
                    "failures_by_check": failures_by_check,
                    "sample_failures": failure_cases.head(10).to_dict(orient="records"),
                },
                failure_message=f"Schema validation failed with {len(failure_cases)} errors",
            )

        except Exception as exc:
            return QualityCheckResult(
                passed=False,
                metric_name="schema_check",
                metric_value={"schema_valid": False},
                metadata={"error": str(exc)},
                failure_message=f"Unexpected error during schema validation: {exc}",
            )

    @property
    def name(self) -> str:
        schema_name = getattr(self.schema, "__name__", "schema")
        return f"schema_check_{schema_name}"
