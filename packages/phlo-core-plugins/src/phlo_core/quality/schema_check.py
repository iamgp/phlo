"""Schema check plugin."""

from typing import Any

from phlo.plugins import PluginMetadata, QualityCheckPlugin
from phlo_quality.checks import SchemaCheck


class SchemaCheckPlugin(QualityCheckPlugin):
    """Plugin for schema checks."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="schema_check",
            version="0.1.0",
            description="Schema validation for expected columns and types",
            author="Phlo Team",
            tags=["quality", "schema"],
        )

    def create_check(self, schema: Any, lazy: bool = True) -> SchemaCheck:
        return SchemaCheck(schema=schema, lazy=lazy)
