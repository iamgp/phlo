# MinioCliPlugin (/docs/python-reference/packages/phlo-minio/phlo_minio/cli_plugin/MinioCliPlugin)



CLI plugin that registers MinIO commands with the Phlo CLI.

This plugin implements the CliCommandPlugin interface to expose
MinIO operations through the Phlo CLI framework. It provides
access to S3-compatible storage operations via the 'minio' command
group.

The plugin supports:

* Bucket and object listing
* Administrative operations
* Direct mc (MinIO Client) command passthrough

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata containing name, version, and description.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_cli_commands&#x22;" type="&#x22;(self) -> list[click.Command]&#x22;">
  Return the list of CLI commands exposed by this plugin.

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    The returned list contains the top-level minio command group
    which itself contains subcommands (ls, admin info, etc.).
  </Callout>

  <PySourceCode>
    ```python
    def get_cli_commands(self) -> list[click.Command]:
        """Return the list of CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: List containing the minio command group.

        Examples:
            Retrieve commands:
                >>> plugin = MinioCliPlugin()
                >>> commands = plugin.get_cli_commands()
                >>> len(commands)
                1
                >>> commands[0].name
                'minio'
                >>> commands[0].help
                'Run MinIO client (mc) commands...'

        Note:
            The returned list contains the top-level minio command group
            which itself contains subcommands (ls, admin info, etc.).

        """
        return [minio_group]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[click.Command]: List containing the minio command group.
  </PyFunctionReturn>
</PyFunction>
