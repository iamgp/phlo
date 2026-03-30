# create (/docs/python-reference/core/phlo/cli/commands/plugin/create)



Plugin create command.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;create_cmd&#x22;" type="&#x22;(plugin_name, plugin_type, path)&#x22;">
      Create scaffolding for a new plugin.

      <PySourceCode>
        ```python
        @click.command(name="create")
        @click.argument("plugin_name")
        @click.option(
            "--type",
            "plugin_type",
            type=click.Choice(
                [
                    "sources",
                    "quality",
                    "transforms",
                    "services",
                    "hooks",
                    "catalogs",
                    "assets",
                    "resources",
                    "orchestrators",
                ]
            ),
            default="sources",
            help="Type of plugin to create",
        )
        @click.option(
            "--path",
            type=click.Path(),
            help="Path for new plugin package (default: ./phlo-plugin-{name})",
        )
        def create_cmd(plugin_name: str, plugin_type: str, path: str | None):
            """Create scaffolding for a new plugin.

            Examples:
                phlo plugin create my-source              # Create source connector plugin
                phlo plugin create my-check --type quality # Create quality check plugin
                phlo plugin create my-transform --type transforms --path ./plugins/
            """
            try:
                plugin_type = SCAFFOLD_TYPE_MAP.get(plugin_type, plugin_type)

                # Validate plugin name
                if not plugin_name or not all(c.isalnum() or c in "-_" for c in plugin_name):
                    logger.warning("plugin_create_validation_failed", reason="invalid_name")
                    console.print("[red]Invalid plugin name. Use alphanumeric characters, - and _[/red]")
                    sys.exit(1)

                # Determine output path
                if not path:
                    path = f"phlo-plugin-{plugin_name}"

                plugin_path = Path(path)
                if plugin_path.exists():
                    logger.warning(
                        "plugin_create_validation_failed", reason="path_exists", path=str(plugin_path)
                    )
                    console.print(f"[red]Path already exists: {path}[/red]")
                    sys.exit(1)

                # Create plugin package structure
                create_plugin_package(
                    plugin_name=plugin_name,
                    plugin_type=plugin_type,
                    plugin_path=plugin_path,
                )
                logger.info(
                    "plugin_create_succeeded",
                    plugin_name=plugin_name,
                    plugin_type=plugin_type,
                    path=str(plugin_path),
                )

                console.print("\n[green]✓ Plugin created successfully![/green]")
                console.print("\nNext steps:")
                console.print(f"  1. cd {path}")
                console.print(f"  2. Edit the plugin in src/phlo_{plugin_name.replace('-', '_')}/")
                console.print("  3. Run tests: pytest tests/")
                console.print("  4. Install: pip install -e .")

            except SystemExit:
                raise
            except Exception as e:
                logger.exception("plugin_create_failed", plugin_name=plugin_name, plugin_type=plugin_type)
                console.print(f"[red]Error creating plugin: {e}[/red]")
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;path&#x22;" type="&#x22;str | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
