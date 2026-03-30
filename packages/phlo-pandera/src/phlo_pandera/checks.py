"""Quality check classes for declarative data validation.

This module provides the core quality check classes for the Phlo Quality Framework.
These classes define validation rules that can be applied to data tables and
integrated into Dagster pipelines via the ``@phlo_pandera`` decorator.

Each check class implements the ``QualityCheck`` abstract base class and provides
a declarative way to define validation rules. Checks operate on pandas DataFrames
and return structured ``QualityCheckResult`` objects containing pass/fail status,
metrics, and metadata.

Quality Check Architecture:
    The quality check system follows a consistent pattern:

    1. **Definition**: Instantiate check classes with configuration parameters
    2. **Execution**: Check classes implement ``execute()`` method for validation
    3. **Results**: Return ``QualityCheckResult`` with pass/fail and metadata
    4. **Integration**: ``@phlo_pandera`` decorator converts checks to Dagster asset checks

Basic Usage:
    ```python
    from phlo_pandera import NullCheck, RangeCheck, phlo_pandera

    @phlo_pandera(
        table="bronze.sensor_readings",
        checks=[
            NullCheck(columns=["sensor_id", "reading_value"]),
            RangeCheck(column="reading_value", min_value=0, max_value=100),
        ],
    )
    def sensor_quality():
        pass
    ```

Available Checks:
    - **NullCheck**: Validates that specified columns contain no null values
    - **RangeCheck**: Validates that numeric column values fall within a specified range
    - **FreshnessCheck**: Validates that data is recent based on timestamp columns
    - **UniqueCheck**: Validates uniqueness constraints across specified columns
    - **CountCheck**: Validates that row count meets minimum and/or maximum bounds

Thresholds and Tolerance:
    Most checks support threshold parameters that allow a configurable percentage
    of failures before marking the check as failed:

    ```python
    # Allow up to 5% null values before failing
    NullCheck(columns=["optional_field"], allow_threshold=0.05)

    # Allow up to 1% out-of-range values
    RangeCheck(column="measurement", min_value=0, max_value=100, allow_threshold=0.01)
    ```

Type Aliases:
    - ``MetricValue``: Union of int, float, dict, or None for metric values
    - ``Metadata``: Dictionary for arbitrary metadata

See Also:
    - ``checks_extra.py``: Extended check types (SchemaCheck, CustomSQLCheck, PatternCheck)
    - ``reconciliation.py``: Cross-table reconciliation checks
    - ``decorator.py``: ``@phlo_pandera`` decorator implementation

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from phlo.capabilities.runtime import RuntimeContext

# Type aliases for clarity
MetricValue = int | float | dict[str, Any] | None
Metadata = dict[str, Any]


def extract_sample_rows(
    df: pd.DataFrame,
    mask: pd.Series,
    columns: list[str],
    max_rows: int = 20,
) -> list[dict[str, Any]]:
    """Extract sample rows matching a condition for error reporting.

    This helper function extracts a sample of rows that match a boolean mask,
    limited to a maximum number of rows. It's used to provide concrete examples
    of quality check failures for debugging and reporting purposes.

    Args:
        df: DataFrame to sample from.
        mask: Boolean Series indicating which rows to extract.
        columns: List of column names to include in the sample.
        max_rows: Maximum number of rows to return (default: 20).

    Returns:
        List of dictionaries, each representing a sampled row with its index
        and specified column values.

    Example:
        ```python
        import pandas as pd

        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "value": [100, None, 300, None]
        })

        null_mask = df["value"].isna()
        samples = extract_sample_rows(df, null_mask, ["id", "value"], max_rows=10)
        # Returns: [{"row_index": 1, "id": 2, "value": None}, ...]
        ```

    """
    rows = df.loc[mask, columns].head(max_rows)
    return [
        {"row_index": idx if isinstance(idx, int) else str(idx), **row.to_dict()}
        for idx, row in rows.iterrows()
    ]


@dataclass
class QualityCheckResult:
    """Result from executing a quality check.

    This dataclass encapsulates the outcome of a quality check execution,
    including pass/fail status, metric values, and detailed metadata for
    debugging and observability.

    Attributes:
        passed: Whether the quality check passed validation.
        metric_name: Name of the quality metric being checked.
        metric_value: Value of the quality metric (int, float, dict, or None).
        metadata: Additional metadata about the check execution (default: empty dict).
        failure_message: Human-readable failure message if check failed (default: None).

    Example:
        ```python
        result = QualityCheckResult(
            passed=False,
            metric_name="null_check",
            metric_value={"null_count": 5},
            metadata={"column": "email", "threshold": 0.0},
            failure_message="Column 'email' has 5 null values (threshold: 0.0)",
        )
        ```

    """

    passed: bool
    """Whether the quality check passed."""

    metric_name: str
    """Name of the quality metric."""

    metric_value: MetricValue
    """Value of the quality metric."""

    metadata: Metadata = field(default_factory=dict)
    """Additional metadata about the check."""

    failure_message: str | None = None
    """Human-readable failure message if check failed."""


class QualityCheck(ABC):
    """Abstract base class for all quality checks.

    All quality checks must inherit from this class and implement the
    ``execute`` method which validates data and returns a ``QualityCheckResult``.
    The ``name`` property provides a stable identifier for the check.

    Subclasses should typically use the ``@dataclass`` decorator for clean,
    declarative configuration.

    Example:
        ```python
        from dataclasses import dataclass

        @dataclass
        class CustomCheck(QualityCheck):
            column: str
            expected_value: str

            def execute(self, df, context):
                passed = (df[self.column] == self.expected_value).all()
                return QualityCheckResult(
                    passed=passed,
                    metric_name="custom_check",
                    metric_value={"matches": int(passed)},
                )

            @property
            def name(self) -> str:
                return f"custom_{self.column}"
        ```

    """

    @abstractmethod
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute the quality check on the given DataFrame.

        This method must be implemented by all subclasses to perform the actual
        validation logic. It receives a pandas DataFrame and an optional runtime
        context, and must return a ``QualityCheckResult`` with the outcome.

        Args:
            df: DataFrame to validate, containing the data loaded from the
                target table or query.
            context: Runtime context for logging and resource access. May be
                None in testing scenarios.

        Returns:
            QualityCheckResult containing pass/fail status, metric values,
            metadata, and optional failure message.

        Raises:
            Exception: Subclasses may raise exceptions for unrecoverable errors,
                though they should generally catch and return failed results.

        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this check.

        This property should return a stable, unique identifier for the check
        that can be used in logging, reporting, and metadata. It typically
        includes the check type and configuration details.

        Returns:
            String identifier for this check instance.

        """
        pass


@dataclass
class NullCheck(QualityCheck):
    """Check that specified columns have no null values.

    This check validates that one or more columns contain no null (NaN/None)
    values, or that the percentage of null values does not exceed a configurable
    threshold.

    Attributes:
        columns: List of column names that must not contain nulls.
        allow_threshold: Maximum fraction of nulls allowed (0.0 = no nulls allowed,
            0.05 = up to 5% nulls allowed). Defaults to 0.0.

    Example:
        ```python
        # Strict check: no nulls allowed
        NullCheck(columns=["station_id", "temperature"])

        # Permissive check: allow up to 5% nulls in optional fields
        NullCheck(columns=["phone", "address"], allow_threshold=0.05)
        ```

    Returns:
        QualityCheckResult with:
            - ``metric_name``: "null_check"
            - ``metric_value``: Dict mapping column names to null counts
            - ``metadata``: Includes null_counts, null_percentages, columns_checked

    """

    columns: list[str]
    """List of columns that must not contain nulls."""

    allow_threshold: float = 0.0
    """Maximum fraction of nulls allowed (0.0 = no nulls, 0.05 = 5% nulls)."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute null check on DataFrame.

        Iterates through all specified columns, checking for null values and
        calculating null percentages. Returns detailed metadata about null
        counts per column and sample rows containing nulls.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether all columns pass the null
            check within the specified threshold.

        """
        null_counts = {}
        null_percentages = {}
        failures = []
        sample_rows: list[dict[str, Any]] = []

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

                if not sample_rows:
                    existing_columns = [c for c in self.columns if c in df.columns]
                    if existing_columns:
                        sample_rows = extract_sample_rows(df, df[column].isna(), existing_columns)

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
                "sample_rows": sample_rows,
            },
            failure_message="; ".join(failures) if failures else None,
        )

    @property
    def name(self) -> str:
        """Get the check name.

        Returns:
            Stable metric name for this null check, incorporating column names.

        """
        return f"null_check_{'+'.join(self.columns)}"


@dataclass
class RangeCheck(QualityCheck):
    """Check that numeric column values are within specified range.

    This check validates that all values in a numeric column fall within
    an inclusive range defined by minimum and maximum values. It supports
    optional thresholds that allow a percentage of out-of-range values.

    Attributes:
        column: Column name to validate.
        min_value: Minimum allowed value (inclusive). None disables lower bound.
        max_value: Maximum allowed value (inclusive). None disables upper bound.
        allow_threshold: Maximum fraction of out-of-range values allowed
            (0.0 = no violations allowed, 0.01 = 1% allowed). Defaults to 0.0.

    Example:
        ```python
        # Temperature should be between -50 and 60 degrees
        RangeCheck(column="temperature", min_value=-50, max_value=60)

        # Allow up to 1% of values to be out of range (measurement errors)
        RangeCheck(column="pressure", min_value=0, max_value=100, allow_threshold=0.01)

        # Only minimum bound
        RangeCheck(column="age", min_value=0)
        ```

    Returns:
        QualityCheckResult with:
            - ``metric_name``: "range_check"
            - ``metric_value``: Dict with actual min, max, and out_of_range count
            - ``metadata``: Includes expected bounds, actual bounds, violation count

    """

    column: str
    """Column to check."""

    min_value: float | None = None
    """Minimum allowed value (inclusive)."""

    max_value: float | None = None
    """Maximum allowed value (inclusive)."""

    allow_threshold: float = 0.0
    """Maximum fraction of out-of-range values allowed."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute range check on DataFrame.

        Validates that values in the specified column fall within the defined
        range. Calculates actual min/max values and counts violations.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether the column values are within
            range, with detailed statistics about violations.

        """
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

        sample_rows = (
            extract_sample_rows(df, violations, [self.column]) if violation_count > 0 else []
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
                "out_of_range": int(violation_count),
                "threshold": self.allow_threshold,
                "sample_rows": sample_rows,
            },
            failure_message=failure_msg,
        )

    @property
    def name(self) -> str:
        """Get the check name.

        Returns:
            Stable metric name for this range check, incorporating column name.

        """
        return f"range_check_{self.column}"


@dataclass
class FreshnessCheck(QualityCheck):
    """Check that data is fresh (not stale).

    This check validates that the most recent timestamp in a specified column
    is within a maximum age threshold. It's useful for detecting stale data
    or pipeline delays.

    Attributes:
        timestamp_column: Column name containing timestamps to check.
        max_age_hours: Maximum age in hours for data to be considered fresh.
        reference_time: Reference time to compare against. Defaults to the
            current time (datetime.now()).

    Example:
        ```python
        # Data should be no more than 2 hours old
        FreshnessCheck(timestamp_column="observation_time", max_age_hours=2)

        # Check against a specific reference time
        from datetime import datetime
        reference = datetime(2024, 1, 15, 12, 0, 0)
        FreshnessCheck(
            timestamp_column="created_at",
            max_age_hours=24,
            reference_time=reference
        )
        ```

    Returns:
        QualityCheckResult with:
            - ``metric_name``: "freshness_check"
            - ``metric_value``: Dict with max_age_hours
            - ``metadata``: Includes max_timestamp, reference_time, age_hours

    """

    timestamp_column: str
    """Column containing timestamps to check."""

    max_age_hours: float
    """Maximum age in hours for data to be considered fresh."""

    reference_time: datetime | None = None
    """Reference time to compare against (defaults to now)."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute freshness check on DataFrame.

        Converts the timestamp column to datetime, finds the most recent value,
        and calculates its age relative to the reference time.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether the data is fresh within
            the specified maximum age.

        """
        if self.timestamp_column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="freshness_check",
                metric_value=None,
                failure_message=f"Column '{self.timestamp_column}' not found in DataFrame",
            )

        # Convert to datetime if needed
        timestamp_data = pd.Series(pd.to_datetime(df[self.timestamp_column], errors="coerce"))

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
        """Get the check name.

        Returns:
            Stable metric name for this freshness check, incorporating timestamp column.

        """
        return f"freshness_check_{self.timestamp_column}"


@dataclass
class UniqueCheck(QualityCheck):
    """Check that specified columns have unique values (no duplicates).

    This check validates that the combination of values across one or more
    columns is unique across all rows. It supports threshold parameters that
    allow a configurable percentage of duplicate rows.

    Attributes:
        columns: List of column names that must have unique combinations.
        allow_threshold: Maximum fraction of duplicates allowed (0.0 = exact
            uniqueness required, 0.05 = 5% duplicates allowed). Defaults to 0.0.

    Example:
        ```python
        # Each station_id should appear only once
        UniqueCheck(columns=["station_id"])

        # Combination of station_id and timestamp should be unique
        UniqueCheck(columns=["station_id", "timestamp"])

        # Allow up to 0.5% duplicates (e.g., for idempotent ingestion)
        UniqueCheck(columns=["event_id"], allow_threshold=0.005)
        ```

    Returns:
        QualityCheckResult with:
            - ``metric_name``: "unique_check"
            - ``metric_value``: Dict with duplicate_count
            - ``metadata``: Includes duplicate_percentage, columns_checked, sample_rows

    """

    columns: list[str]
    """List of columns that must have unique combinations."""

    allow_threshold: float = 0.0
    """Maximum fraction of duplicates allowed."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute uniqueness check on DataFrame.

        Uses pandas ``duplicated()`` method to identify duplicate rows based
        on the specified column combination. Calculates duplicate percentage
        and provides sample duplicate rows for debugging.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether the columns have unique
            values within the specified threshold.

        """
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
                "sample_rows": [
                    {"row_index": idx if isinstance(idx, int) else str(idx), **row.to_dict()}
                    for idx, row in df.loc[duplicates, self.columns].head(20).iterrows()
                ],
            },
            failure_message=failure_msg,
        )

    @property
    def name(self) -> str:
        """Get the check name.

        Returns:
            Stable metric name for this uniqueness check, incorporating column names.

        """
        return f"unique_check_{'+'.join(self.columns)}"


@dataclass
class CountCheck(QualityCheck):
    """Check that row count meets expectations.

    This check validates that the number of rows in a dataset falls within
    expected bounds. It's useful for detecting empty datasets, unexpected
    data volumes, or significant data loss.

    Attributes:
        min_rows: Minimum expected row count. None disables minimum check.
        max_rows: Maximum expected row count. None disables maximum check.

    Example:
        ```python
        # At least 100 rows expected
        CountCheck(min_rows=100)

        # Row count should be between 100 and 10000
        CountCheck(min_rows=100, max_rows=10000)

        # No more than 1 million rows
        CountCheck(max_rows=1000000)

        # Exactly 24 rows expected (hourly data for one day)
        CountCheck(min_rows=24, max_rows=24)
        ```

    Returns:
        QualityCheckResult with:
            - ``metric_name``: "count_check"
            - ``metric_value``: Dict with row_count
            - ``metadata``: Includes min_rows, max_rows bounds

    """

    min_rows: int | None = None
    """Minimum expected row count."""

    max_rows: int | None = None
    """Maximum expected row count."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute count check on DataFrame.

        Counts total rows in the DataFrame and validates against configured
        minimum and maximum bounds.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether the row count is within
            the specified bounds.

        """
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
        """Get the check name.

        Returns:
            Stable metric name for this count check.

        """
        return "count_check"
