# DbtCliPlugin (/docs/python-reference/packages/phlo-dbt/phlo_dbt/cli_plugin/DbtCliPlugin)



CLI plugin exposing dbt-related commands.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands contributed by this plugin.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin.

        Returns:
            List of click commands to register.

        """
        return [dbt_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of click commands to register.
  </PyFunctionReturn>
</PyFunction>
