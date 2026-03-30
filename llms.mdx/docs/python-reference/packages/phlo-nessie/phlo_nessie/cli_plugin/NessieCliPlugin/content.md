# NessieCliPlugin (/docs/python-reference/packages/phlo-nessie/phlo_nessie/cli_plugin/NessieCliPlugin)



Register Nessie CLI commands with the Phlo plugin system.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for Nessie CLI integration.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return CLI commands exposed by this plugin.

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Registered Nessie command groups.

        """
        return [catalog, branch]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[click.Command]: Registered Nessie command groups.
  </PyFunctionReturn>
</PyFunction>
