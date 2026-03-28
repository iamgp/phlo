"""Extended quality check classes: SchemaCheck, CustomSQLCheck, PatternCheck.

This module provides additional quality check types that extend the core checks
from ``checks.py``. These checks support more advanced validation scenarios
including schema validation, custom SQL assertions, and pattern matching.

These checks are split into a separate module to keep individual files under
500 lines as per project conventions, while maintaining a clean organization
of related functionality.

Available Extended Checks:
    - **SchemaCheck**: Validates DataFrame against a Pandera DataFrameModel schema,
        including type checking, constraint validation, and nullability checks.
    - **CustomSQLCheck**: Executes arbitrary SQL queries against the data using
        DuckDB, enabling complex business rule validation.
    - **PatternCheck**: Validates that string column values match regular
        expression patterns, useful for format validation (emails, postal codes, etc.).

Example Usage:
    ```python
    from phlo_pandera import SchemaCheck, CustomSQLCheck, PatternCheck, phlo_pandera
    from my_schemas import CustomerSchema

    @phlo_pandera(
        table="bronze.customers",
        checks=[
            # Validate against Pandera schema
            SchemaCheck(schema=CustomerSchema),
            # Custom SQL validation
            CustomSQLCheck(
                name_="valid_email",
                sql="SELECT email LIKE '%@%.%' FROM data",
            ),
            # Pattern matching for postal codes
            PatternCheck(
                column="postal_code",
                pattern=r"^\d{5}(-\d{4})?$",
            ),
        ],
    )
    def customer_quality():
        pass
    ```

See Also:
    - ``checks.py``: Core quality check implementations
    - ``reconciliation.py``: Cross-table reconciliation checks
    - ``decorator.py``: ``@phlo_pandera`` decorator for integration

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import pandera.errors as pa_errors

from phlo.capabilities.runtime import RuntimeContext
from phlo.logging import get_logger

from phlo_pandera.checks import QualityCheck, QualityCheckResult

logger = get_logger(__name__)


@dataclass
class SchemaCheck(QualityCheck):
    """Check that DataFrame matches a Pandera schema.

    This check validates that a DataFrame conforms to a Pandera DataFrameModel
    schema, including type validation, constraint checking (min, max, regex, etc.),
    and nullability verification. It uses lazy validation to collect all errors
    rather than failing on the first issue.

    Attributes:
        schema: Pandera DataFrameModel class to validate against (not an instance).
        lazy: Whether to use lazy validation to collect all errors. Default True.
            When True, all schema violations are collected and reported.
            When False, validation stops at the first error.

    Example:
        ```python
        from pandera.pandas import DataFrameModel, Field
        from phlo_pandera import SchemaCheck, phlo_pandera

        class CustomerSchema(DataFrameModel):
            customer_id: int = Field(gt=0)
            email: str = Field(nullable=True)
            age: int = Field(ge=0, le=150)

        @phlo_pandera(
            table="bronze.customers",
            checks=[SchemaCheck(schema=CustomerSchema)],
        )
        def customer_quality():
            pass
        ```

    Returns:
        QualityCheckResult with:
            - ``metric_name``: "schema_check"
            - ``metric_value``: Dict with schema_valid boolean
            - ``metadata``: Includes schema_name, rows_evaluated, failed_checks,
                failures_by_column, failures_by_check, sample_failures

    Note:
        The schema parameter should be the class (e.g., ``CustomerSchema``),
        not an instance (e.g., ``CustomerSchema()``).

    """

    schema: Any
    """Pandera DataFrameModel or schema to validate against."""

    lazy: bool = True
    """Use lazy validation to collect all errors."""

    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute schema check on DataFrame.

        Validates the DataFrame against the configured Pandera schema using
        lazy validation to collect all validation errors. Groups failures by
        column and check type for detailed reporting.

        Args:
            df: DataFrame to validate against the schema.
            context: Runtime context for logging and resources.

        Returns:
            QualityCheckResult indicating schema validity with detailed failure
            information when validation fails.

        Raises:
            Exception: Catches and logs unexpected errors, returning a failed result.

        """
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
            Stable metric name incorporating the schema class name.

        """
        schema_name = getattr(self.schema, "__name__", "schema")
        return f"schema_check_{schema_name}"


@dataclass
class CustomSQLCheck(QualityCheck):
    """Execute arbitrary SQL to validate data.

    This check enables complex validation logic by executing custom SQL queries
    against the data using DuckDB. The SQL should return a single boolean column
    where True indicates a valid row and False indicates a violation.

    This is useful for cross-column validations, business rule checks, or any
    validation that cannot be expressed with the standard check types.

    Attributes:
        name_: Name of this check for identification in results.
        sql: SQL query that returns a boolean column. True = valid, False = violation.
            The DataFrame is registered as a table named "data".
        expected: Expected boolean result for valid rows. Default True.
        allow_threshold: Maximum fraction of failures allowed (0.0 = no failures
            allowed, 0.05 = 5% allowed). Default 0.0.

    Example:
        ```python
        # Simple positive value check
        CustomSQLCheck(
            name_="positive_amount",
            sql="SELECT (amount > 0) AS is_valid FROM data",
        )

        # Cross-column validation
        CustomSQLCheck(
            name_="date_consistency",
            sql="SELECT (end_date >= start_date) AS is_valid FROM data",
        )

        # Complex business rule
        CustomSQLCheck(
            name_="valid_discount",
            sql="SELECT (discount >= 0 AND discount <= original_price) FROM data",
            allow_threshold=0.01,  # Allow 1% violations
        )
        ```

    Returns:
        QualityCheckResult with:
            - ``metric_name``: The provided ``name_`` parameter
            - ``metric_value``: Dict with failures count and total rows
            - ``metadata``: Includes failure_percentage, threshold

    Note:
        This check requires DuckDB to be installed. It registers the DataFrame
        as a DuckDB table named "data" for querying.

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
        """Execute custom SQL check on DataFrame.

        Registers the DataFrame as a DuckDB table named "data" and executes the
        provided SQL query. Counts rows where the result doesn't match the expected
        value and determines pass/fail based on the threshold.

        Args:
            df: DataFrame to validate. Registered as "data" table in DuckDB.
            context: Runtime context for logging.

        Returns:
            QualityCheckResult with failure counts and statistics.

        Raises:
            ImportError: If DuckDB is not available.
            Exception: Catches SQL execution errors and returns failed result.

        """
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
            Check name with "custom_sql_" prefix for identification.

        """
        return f"custom_sql_{self.name_}"


@dataclass
class PatternCheck(QualityCheck):
    """Check that string column values match a regex pattern.

    This check validates that all non-null values in a string column match
    a specified regular expression pattern. It's useful for format validation
    such as email addresses, phone numbers, postal codes, IDs, etc.

    Supports configurable thresholds to allow a percentage of non-matching
    values, and case sensitivity can be controlled via a flag.

    Attributes:
        column: Column name to validate.
        pattern: Regular expression pattern that values must match.
        allow_threshold: Maximum fraction of non-matching values allowed
            (0.0 = all values must match, 0.05 = 5% can fail). Default 0.0.
        case_sensitive: Whether pattern matching is case sensitive. Default True.

    Example:
        ```python
        # Email format validation
        PatternCheck(
            column="email",
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        # US postal code (ZIP or ZIP+4)
        PatternCheck(
            column="postal_code",
            pattern=r"^\d{5}(-\d{4})?$",
            allow_threshold=0.01  # Allow 1% invalid postal codes
        )

        # Case-insensitive country code
        PatternCheck(
            column="country_code",
            pattern=r"^[A-Z]{2}$",
            case_sensitive=False
        )

        # UUID format
        PatternCheck(
            column="uuid",
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        ```

    Returns:
        QualityCheckResult with:
            - ``metric_name``: "pattern_check"
            - ``metric_value``: Dict with match_count and non_match_count
            - ``metadata``: Includes pattern, match_percentage, sample non-matches

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
        """Execute pattern check on DataFrame.

        Compiles the regex pattern (with optional case insensitivity) and matches
        it against all non-null string values in the specified column. Calculates
        match statistics and provides sample non-matching values for debugging.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context for logging.

        Returns:
            QualityCheckResult indicating whether the pattern matches the
            configured percentage of values.

        """
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
            Stable metric name incorporating the column name.

        """
        return f"pattern_check_{self.column}"
