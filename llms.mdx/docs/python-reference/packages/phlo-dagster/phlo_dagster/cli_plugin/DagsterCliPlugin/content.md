# DagsterCliPlugin (/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_plugin/DagsterCliPlugin)



Expose Dagster workflow commands to the Phlo CLI plugin system.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin identity metadata for discovery.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands provided by the Dagster plugin.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands provided by the Dagster plugin.

        Returns:
            Ordered list of Dagster-related Click commands.

        """
        return [dev, logs, status, backfill, materialize]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Ordered list of Dagster-related Click commands.
  </PyFunctionReturn>
</PyFunction>
