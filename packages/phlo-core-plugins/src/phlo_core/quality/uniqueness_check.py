"""Uniqueness check plugin for validating primary key integrity.

This module provides the UniquenessCheckPlugin, which enables validation of
uniqueness constraints on specified columns. It helps ensure data integrity
by detecting duplicate values in columns that should contain unique identifiers,
such as primary keys or natural keys.

Example:
    Using the uniqueness check plugin::

        from phlo_core.quality.uniqueness_check import UniquenessCheckPlugin

        # Create the plugin
        plugin = UniquenessCheckPlugin()

        # Strict uniqueness check (no duplicates allowed)
        strict_check = plugin.create_check(
            columns=["user_id"],
            allow_threshold=0.0
        )

        # Lenient uniqueness check (allow up to 5% duplicates)
        lenient_check = plugin.create_check(
            columns=["session_id"],
            allow_threshold=0.05
        )

        # Multi-column uniqueness check
        composite_check = plugin.create_check(
            columns=["first_name", "last_name", "date_of_birth"],
            allow_threshold=0.0
        )

"""

from typing import Any

from phlo.plugins import PluginMetadata, QualityCheckPlugin


class UniquenessCheckPlugin(QualityCheckPlugin[Any]):
    """Plugin for performing uniqueness validation on data columns.

    This plugin creates uniqueness check instances that validate whether
    specified columns contain unique values. It supports both strict uniqueness
    (no duplicates allowed) and lenient uniqueness (allows a configurable
    percentage of duplicates).

    The uniqueness check is particularly useful for:
        - Validating primary key integrity
        - Detecting duplicate records in data imports
        - Ensuring natural key uniqueness
        - Validating composite keys across multiple columns

    Attributes:
        metadata: PluginMetadata containing name, version, description,
            author, and tags for this plugin.

    Example:
        Strict uniqueness check for primary keys::

            from phlo_core.quality.uniqueness_check import UniquenessCheckPlugin

            plugin = UniquenessCheckPlugin()
            check = plugin.create_check(
                columns=["customer_id"],
                allow_threshold=0.0  # No duplicates allowed
            )

        Lenient uniqueness check with duplicate tolerance::

            check = plugin.create_check(
                columns=["transaction_id"],
                allow_threshold=0.01  # Allow up to 1% duplicates
            )

        Composite uniqueness check::

            check = plugin.create_check(
                columns=["product_id", "warehouse_id"],
                allow_threshold=0.0
            )

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the uniqueness-check plugin.

        Returns:
            PluginMetadata: Metadata including name ("uniqueness_check"),
                version ("0.1.0"), description ("Uniqueness validation for primary keys"),
                author ("Phlo Team"), and tags (["quality", "uniqueness"]).

        """
        return PluginMetadata(
            name="uniqueness_check",
            version="0.1.0",
            description="Uniqueness validation for primary keys",
            author="Phlo Team",
            tags=["quality", "uniqueness"],
        )

    def create_check(self, columns: list[str], allow_threshold: float = 0.0) -> Any:
        """Create a uniqueness check instance.

        Creates and returns a configured UniqueCheck instance from phlo_pandera
        that validates uniqueness constraints on specified columns.

        Args:
            columns: List of column names that must contain unique values.
                For composite uniqueness, provide multiple column names.
                The check validates that the combination of values across
                these columns is unique.
            allow_threshold: Maximum allowed ratio of duplicate rows as a
                float between 0.0 and 1.0. Defaults to 0.0 (strict uniqueness,
                no duplicates allowed). A threshold of 0.05 allows up to 5%
                of rows to be duplicates.

        Returns:
            Any: Configured UniqueCheck instance ready to validate data.
            The returned object can be used with Pandera schemas or called
            directly with DataFrames.

        Raises:
            ValueError: If allow_threshold is not between 0.0 and 1.0.

        Example:
            Strict uniqueness check on single column::

                from phlo_core.quality.uniqueness_check import UniquenessCheckPlugin

                plugin = UniquenessCheckPlugin()
                check = plugin.create_check(
                    columns=["order_id"],
                    allow_threshold=0.0
                )

            Allow some duplicates::

                check = plugin.create_check(
                    columns=["session_id"],
                    allow_threshold=0.02  # 2% tolerance
                )

            Composite uniqueness check::

                check = plugin.create_check(
                    columns=["category", "subcategory"],
                    allow_threshold=0.0
                )

        """
        from phlo_pandera.checks import UniqueCheck

        return UniqueCheck(columns=columns, allow_threshold=allow_threshold)
