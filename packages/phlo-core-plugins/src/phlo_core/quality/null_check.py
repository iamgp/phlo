"""Null check plugin for validating column completeness.

This module provides the NullCheckPlugin, which enables validation of
null value presence in specified columns. It helps ensure data completeness
by detecting missing values and enforcing thresholds for acceptable null rates.

Example:
    Using the null check plugin::

        from phlo_core.quality.null_check import NullCheckPlugin

        # Create the plugin
        plugin = NullCheckPlugin()

        # Strict null check (no nulls allowed)
        strict_check = plugin.create_check(
            columns=["id", "email", "created_at"],
            allow_threshold=0.0
        )

        # Lenient null check (allow up to 10% nulls in optional fields)
        lenient_check = plugin.create_check(
            columns=["middle_name", "phone_number"],
            allow_threshold=0.10
        )

        # Mixed columns with different requirements
        mixed_check = plugin.create_check(
            columns=["required_field", "optional_field"],
            allow_threshold=0.0  # Applies to all columns
        )

"""

from typing import Any

from phlo.plugins import PluginMetadata, QualityCheckPlugin


class NullCheckPlugin(QualityCheckPlugin[Any]):
    """Plugin for performing null value validation on data columns.

        This plugin creates null check instances that validate whether specified
    columns contain null values within acceptable thresholds. It supports both
    strict validation (no nulls allowed) and lenient validation (allows a
    configurable percentage of nulls per column).

        The null check is particularly useful for:
            - Validating required field completeness
            - Detecting data quality issues in ETL pipelines
            - Enforcing data completeness SLAs
            - Identifying sparse columns that may need attention

    Attributes:
            metadata: PluginMetadata containing name, version, description,
                author, and tags for this plugin.

    Example:
            Strict null check for required fields::

                from phlo_core.quality.null_check import NullCheckPlugin

                plugin = NullCheckPlugin()
                check = plugin.create_check(
                    columns=["user_id", "email", "registration_date"],
                    allow_threshold=0.0  # No nulls allowed
                )

            Lenient null check for optional fields::

                check = plugin.create_check(
                    columns=["phone", "address_line_2"],
                    allow_threshold=0.20  # Allow up to 20% nulls
                )

            Using with Pandera schema::

                import pandera as pa

                schema = pa.DataFrameSchema(
                    columns={
                        "id": pa.Column(pa.Int64, checks=check),
                        "name": pa.Column(pa.String, checks=check),
                    }
                )

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the null-check quality plugin.

        Returns:
            PluginMetadata: Metadata including name ("null_check"),
                version ("0.1.0"), description ("Null checks for column completeness"),
                author ("Phlo Team"), and tags (["quality", "nulls"]).

        """
        return PluginMetadata(
            name="null_check",
            version="0.1.0",
            description="Null checks for column completeness",
            author="Phlo Team",
            tags=["quality", "nulls"],
        )

    def create_check(self, columns: list[str], allow_threshold: float = 0.0) -> Any:
        """Create a null check instance.

        Creates and returns a configured NullCheck instance from phlo_pandera
        that validates null value presence in specified columns.

        Args:
            columns: List of column names to validate for null values.
                Each column in the list will be checked individually for
                null value presence against the threshold.
            allow_threshold: Maximum allowed null ratio per column as a float
                between 0.0 and 1.0. Defaults to 0.0 (strict validation, no
                nulls allowed). A threshold of 0.10 allows up to 10% of values
                in each column to be null.

        Returns:
            Any: Configured NullCheck instance ready to validate data.
            The returned object can be used with Pandera schemas or called
            directly with DataFrames.

        Raises:
            ValueError: If allow_threshold is not between 0.0 and 1.0.

        Example:
            Create a strict null check::

                from phlo_core.quality.null_check import NullCheckPlugin

                plugin = NullCheckPlugin()
                check = plugin.create_check(
                    columns=["customer_id", "order_date"],
                    allow_threshold=0.0
                )

            Create a lenient null check for optional fields::

                check = plugin.create_check(
                    columns=["middle_name", "secondary_email"],
                    allow_threshold=0.15  # 15% tolerance
                )

            Apply to DataFrame directly::

                result = check.validate(df)

        """
        from phlo_pandera.checks import NullCheck

        return NullCheck(columns=columns, allow_threshold=allow_threshold)
