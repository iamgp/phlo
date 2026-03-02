"""Null check plugin."""

from typing import Any

from phlo.plugins import PluginMetadata, QualityCheckPlugin


class NullCheckPlugin(QualityCheckPlugin[Any]):
    """Plugin for NullCheck quality checks."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the null-check quality plugin."""
        return PluginMetadata(
            name="null_check",
            version="0.1.0",
            description="Null checks for column completeness",
            author="Phlo Team",
            tags=["quality", "nulls"],
        )

    def create_check(self, columns: list[str], allow_threshold: float = 0.0) -> Any:
        """Create a null check instance.

        Args:
            columns: Column names to validate for null values.
            allow_threshold: Maximum allowed null ratio per column.

        Returns:
            Configured null-check instance.
        """
        from phlo_pandera.checks import NullCheck

        return NullCheck(columns=columns, allow_threshold=allow_threshold)
