"""
Example quality check plugin.

Demonstrates:
- Creating custom quality checks
- Threshold-based validation
- Tolerance thresholds
- Custom result formatting
"""

from typing import Any

import pandas as pd

from phlo.plugins import PluginMetadata, QualityCheckPlugin


class ThresholdCheckPlugin(QualityCheckPlugin):
    """
    Quality check plugin for threshold validation.

    Creates checks that verify numeric values fall within specified thresholds.

    Configuration:
        {
            "column": "value",  # Column to validate
            "min": 0,           # Minimum allowed value
            "max": 100,         # Maximum allowed value
            "tolerance": 0.05,  # Allow 5% of rows to fail (0.0 = strict)
        }
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="threshold_check",
            version="1.0.0",
            description="Validate numeric values within thresholds",
            author="Phlo Team",
            homepage="https://github.com/iamgp/phlo",
            tags=["validation", "numeric", "example"],
            license="MIT",
        )

    def create_check(self, **kwargs) -> "ThresholdCheck":
        """
        Create a threshold check instance.

        Args:
            column: Column name to validate
            min: Minimum value (inclusive)
            max: Maximum value (inclusive)
            tolerance: Fraction of rows allowed to fail (0.0 = strict, 1.0 = allow all)

        Returns:
            ThresholdCheck instance
        """
        return ThresholdCheck(
            column=kwargs.get("column"),
            min_value=kwargs.get("min"),
            max_value=kwargs.get("max"),
            tolerance=kwargs.get("tolerance", 0.0),
        )


class ThresholdCheck:
    """
    Threshold-based quality check.

    Validates that numeric values in a column fall within specified bounds.
    """

    def __init__(
        self,
        column: str,
        min_value: float | None = None,
        max_value: float | None = None,
        tolerance: float = 0.0,
    ):
        """
        Initialize threshold check.

        Args:
            column: Column to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            tolerance: Fraction of rows allowed to fail (0.0-1.0)
        """
        self.column = column
        self.min_value = min_value
        self.max_value = max_value
        self.tolerance = max(0.0, min(1.0, tolerance))  # Clamp to 0.0-1.0

    def execute(self, df: pd.DataFrame, context: Any = None) -> dict:
        """
        Execute the quality check.

        Args:
            df: DataFrame to validate
            context: Optional execution context

        Returns:
            Dictionary with check results:
            {
                "passed": bool,
                "violations": int,
                "total": int,
                "violation_rate": float,
            }
        """
        if self.column not in df.columns:
            return {
                "passed": False,
                "violations": len(df),
                "total": len(df),
                "violation_rate": 1.0,
                "error": f"Column '{self.column}' not found",
            }

        # Count violations
        violations = 0
        for value in df[self.column]:
            if pd.isna(value):
                violations += 1
                continue

            if self.min_value is not None and value < self.min_value:
                violations += 1
                continue

            if self.max_value is not None and value > self.max_value:
                violations += 1

        total = len(df)
        violation_rate = violations / total if total > 0 else 0.0

        # Check if within tolerance
        passed = violation_rate <= self.tolerance

        return {
            "passed": passed,
            "violations": violations,
            "total": total,
            "violation_rate": violation_rate,
        }

    @property
    def name(self) -> str:
        """Return check name."""
        bounds = []
        if self.min_value is not None:
            bounds.append(f"min={self.min_value}")
        if self.max_value is not None:
            bounds.append(f"max={self.max_value}")

        bound_str = ",".join(bounds) if bounds else "unbounded"
        return f"threshold_check({self.column},{bound_str})"
