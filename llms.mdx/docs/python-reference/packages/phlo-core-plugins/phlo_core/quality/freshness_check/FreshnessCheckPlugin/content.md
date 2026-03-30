# FreshnessCheckPlugin (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/freshness_check/FreshnessCheckPlugin)



Plugin for performing freshness validation on timestamped data.

This plugin creates freshness check instances that validate whether data
is within an acceptable age based on a timestamp column. It compares
the maximum timestamp value in the data against a reference time (defaults
to current time) to ensure data is fresh enough for use.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata containing name, version, description,
  author, and tags for this plugin.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;create_check&#x22;" type="&#x22;(self, timestamp_column, max_age_hours, reference_time=None) -> Any&#x22;">
  Create a freshness check instance.

  Creates and returns a configured FreshnessCheck instance from phlo\_pandera
  that validates data freshness based on timestamps.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Create a freshness check for recent data::

    from phlo\_core.quality.freshness\_check import FreshnessCheckPlugin

    plugin = FreshnessCheckPlugin()
    check = plugin.create\_check(
    timestamp\_column="created\_at",
    max\_age\_hours=24.0
    )

    Create a freshness check with custom reference::

    from datetime import datetime, timedelta

    check\_time = datetime.now() - timedelta(hours=12)
    check = plugin.create\_check(
    timestamp\_column="updated\_at",
    max\_age\_hours=6.0,
    reference\_time=check\_time
    )
  </Callout>

  <PySourceCode>
    ```python
    def create_check(
        self,
        timestamp_column: str,
        max_age_hours: float,
        reference_time: datetime | None = None,
    ) -> Any:
        """Create a freshness check instance.

        Creates and returns a configured FreshnessCheck instance from phlo_pandera
        that validates data freshness based on timestamps.

        Args:
            timestamp_column: Name of the timestamp column used for freshness
                calculations. This column must exist in the data and contain
                datetime values.
            max_age_hours: Maximum allowed age of data in hours. If the data's
                newest timestamp is older than this threshold relative to the
                reference time, the check fails.
            reference_time: Optional reference datetime for age evaluation.
                If None, uses the current time. Useful for testing or when
                validating against a specific point in time.

        Returns:
            Any: Configured FreshnessCheck instance ready to validate data.
            The returned object can be used with Pandera schemas or called
            directly with DataFrames.

        Example:
            Create a freshness check for recent data::

                from phlo_core.quality.freshness_check import FreshnessCheckPlugin

                plugin = FreshnessCheckPlugin()
                check = plugin.create_check(
                    timestamp_column="created_at",
                    max_age_hours=24.0
                )

            Create a freshness check with custom reference::

                from datetime import datetime, timedelta

                check_time = datetime.now() - timedelta(hours=12)
                check = plugin.create_check(
                    timestamp_column="updated_at",
                    max_age_hours=6.0,
                    reference_time=check_time
                )

        """
        from phlo_pandera.checks import FreshnessCheck

        return FreshnessCheck(
            timestamp_column=timestamp_column,
            max_age_hours=max_age_hours,
            reference_time=reference_time,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;timestamp_column&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the timestamp column used for freshness
      calculations. This column must exist in the data and contain
      datetime values.
    </PyParameter>

    <PyParameter name="&#x22;max_age_hours&#x22;" type="&#x22;float&#x22;" value="undefined">
      Maximum allowed age of data in hours. If the data's
      newest timestamp is older than this threshold relative to the
      reference time, the check fails.
    </PyParameter>

    <PyParameter name="&#x22;reference_time&#x22;" type="&#x22;datetime | None&#x22;" value="&#x22;None&#x22;">
      Optional reference datetime for age evaluation.
      If None, uses the current time. Useful for testing or when
      validating against a specific point in time.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Configured FreshnessCheck instance ready to validate data.
  </PyFunctionReturn>
</PyFunction>
