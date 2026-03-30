# UniquenessCheckPlugin (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/uniqueness_check/UniquenessCheckPlugin)



Plugin for performing uniqueness validation on data columns.

This plugin creates uniqueness check instances that validate whether
specified columns contain unique values. It supports both strict uniqueness
(no duplicates allowed) and lenient uniqueness (allows a configurable
percentage of duplicates).

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata containing name, version, description,
  author, and tags for this plugin.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;create_check&#x22;" type="&#x22;(self, columns, allow_threshold=0.0) -> Any&#x22;">
  Create a uniqueness check instance.

  Creates and returns a configured UniqueCheck instance from phlo\_pandera
  that validates uniqueness constraints on specified columns.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Strict uniqueness check on single column::

    from phlo\_core.quality.uniqueness\_check import UniquenessCheckPlugin

    plugin = UniquenessCheckPlugin()
    check = plugin.create\_check(
    columns=\["order\_id"],
    allow\_threshold=0.0
    )

    Allow some duplicates::

    check = plugin.create\_check(
    columns=\["session\_id"],
    allow\_threshold=0.02  # 2% tolerance
    )

    Composite uniqueness check::

    check = plugin.create\_check(
    columns=\["category", "subcategory"],
    allow\_threshold=0.0
    )
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      List of column names that must contain unique values.
      For composite uniqueness, provide multiple column names.
      The check validates that the combination of values across
      these columns is unique.
    </PyParameter>

    <PyParameter name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
      Maximum allowed ratio of duplicate rows as a
      float between 0.0 and 1.0. Defaults to 0.0 (strict uniqueness,
      no duplicates allowed). A threshold of 0.05 allows up to 5%
      of rows to be duplicates.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Configured UniqueCheck instance ready to validate data.
  </PyFunctionReturn>
</PyFunction>
