# CliCommandPlugin (/docs/python-reference/core/phlo/plugins/base/cli/CliCommandPlugin)



Base class for CLI command plugins.

These plugins contribute Click commands/groups to the `phlo` CLI at runtime.

Intended use:

* Capability packages (e.g., `phlo-nessie`, `phlo-openmetadata`) provide their own CLI surface.
* `phlo` core stays lightweight and only provides the CLI glue + shared utilities.

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return Click commands/groups to register on the root CLI.

  <PySourceCode>
    ```python
    @abstractmethod
    def get_cli_commands(self) -> list[click.Command]:
        """Return Click commands/groups to register on the root CLI."""
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[click.click.Command]&#x22;" />
</PyFunction>
