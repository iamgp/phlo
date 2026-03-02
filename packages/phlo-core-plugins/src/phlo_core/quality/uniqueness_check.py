"""Uniqueness check plugin."""

from typing import Any

from phlo.plugins import PluginMetadata, QualityCheckPlugin


class UniquenessCheckPlugin(QualityCheckPlugin[Any]):
    """Plugin for uniqueness checks."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the uniqueness-check plugin."""
        return PluginMetadata(
            name="uniqueness_check",
            version="0.1.0",
            description="Uniqueness validation for primary keys",
            author="Phlo Team",
            tags=["quality", "uniqueness"],
        )

    def create_check(self, columns: list[str], allow_threshold: float = 0.0) -> Any:
        """Create a uniqueness check instance.

        Args:
            columns: Column names that must be unique.
            allow_threshold: Maximum allowed duplicate ratio.

        Returns:
            Configured uniqueness-check instance.
        """
        from phlo_pandera.checks import UniqueCheck

        return UniqueCheck(columns=columns, allow_threshold=allow_threshold)
