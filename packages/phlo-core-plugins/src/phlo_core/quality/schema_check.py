"""Schema check plugin."""

from typing import Any

from phlo.plugins import PluginMetadata, QualityCheckPlugin


class SchemaCheckPlugin(QualityCheckPlugin[Any]):
    """Plugin for schema checks."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the schema-check plugin."""
        return PluginMetadata(
            name="schema_check",
            version="0.1.0",
            description="Schema validation for expected columns and types",
            author="Phlo Team",
            tags=["quality", "schema"],
        )

    def create_check(self, schema: Any, lazy: bool = True) -> Any:
        """Create a schema check instance.

        Args:
            schema: Expected schema object for validation.
            lazy: Whether to collect all validation errors before failing.

        Returns:
            Configured schema-check instance.
        """
        from phlo_quality.checks_extra import SchemaCheck

        return SchemaCheck(schema=schema, lazy=lazy)
