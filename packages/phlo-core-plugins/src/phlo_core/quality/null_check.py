"""Null check plugin."""

from phlo.plugins import PluginMetadata, QualityCheckPlugin
from phlo_quality.checks import NullCheck


class NullCheckPlugin(QualityCheckPlugin):
    """Plugin for NullCheck quality checks."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="null_check",
            version="0.1.0",
            description="Null checks for column completeness",
            author="Phlo Team",
            tags=["quality", "nulls"],
        )

    def create_check(self, columns: list[str], allow_threshold: float = 0.0) -> NullCheck:
        return NullCheck(columns=columns, allow_threshold=allow_threshold)
