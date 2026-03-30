# list (/docs/python-reference/core/phlo/cli/commands/plugin/list)



List plugin command.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;list_cmd&#x22;" type="&#x22;(plugin_type, include_registry, output_json)&#x22;">
      List all discovered plugins.

      <PySourceCode>
        ```python
        @click.command(name="list")
        @click.option(
            "--type",
            "plugin_type",
            type=click.Choice([*PLUGIN_TYPE_CHOICES, "all"]),
            default="all",
            help="Filter by plugin type",
        )
        @click.option(
            "--all",
            "include_registry",
            is_flag=True,
            default=False,
            help="Include registry plugins in output",
        )
        @click.option(
            "--json",
            "output_json",
            is_flag=True,
            default=False,
            help="Output as JSON",
        )
        def list_cmd(plugin_type: str, include_registry: bool, output_json: bool):
            """List all discovered plugins.

            Examples:
                phlo plugin list                    # List all plugins
                phlo plugin list --type sources     # List source connectors only
                phlo plugin list --json             # Output as JSON
                phlo plugin list --all              # Include registry plugins
            """
            try:
                logger.info(
                    "plugin_list_started",
                    plugin_type=plugin_type,
                    include_registry=include_registry,
                    output_json=output_json,
                )
                installed = collect_installed_plugins(plugin_type)
                available = collect_registry_plugins(plugin_type) if include_registry else []

                if output_json:
                    output = {"installed": installed}
                    if include_registry:
                        output["available"] = available
                    console.print(json.dumps(output, indent=2))
                    logger.info(
                        "plugin_list_succeeded",
                        installed_count=len(installed),
                        available_count=len(available),
                        output_json=True,
                    )
                    return

                render_plugin_table("Installed", installed)
                if include_registry:
                    render_plugin_table("Available", available)
                logger.info(
                    "plugin_list_succeeded",
                    installed_count=len(installed),
                    available_count=len(available),
                    output_json=False,
                )

            except Exception as e:
                logger.exception(
                    "plugin_list_failed",
                    plugin_type=plugin_type,
                    include_registry=include_registry,
                    output_json=output_json,
                )
                console.print(f"[red]Error listing plugins: {e}[/red]")
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;include_registry&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;output_json&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
