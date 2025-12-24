"""Uniqueness check plugin."""

from phlo.plugins import PluginMetadata, QualityCheckPlugin
from phlo_quality.checks import UniqueCheck


class UniquenessCheckPlugin(QualityCheckPlugin):
    """Plugin for uniqueness checks."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="uniqueness_check",
            version="0.1.0",
            description="Uniqueness validation for primary keys",
            author="Phlo Team",
            tags=["quality", "uniqueness"],
        )

    def create_check(self, columns: list[str], allow_threshold: float = 0.0) -> UniqueCheck:
        return UniqueCheck(columns=columns, allow_threshold=allow_threshold)
