# install (/docs/python-reference/core/phlo/cli/commands/plugin/install)



Plugin install command.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_install_target&#x22;" type="&#x22;(plugin_name) -> tuple[str, str]&#x22;">
      Resolve plugin name to package spec and display name.

      <PySourceCode>
        ```python
        def resolve_install_target(plugin_name: str) -> tuple[str, str]:
            """Resolve plugin name to package spec and display name."""
            if "==" in plugin_name:
                name_part, version_part = plugin_name.split("==", 1)
            else:
                name_part, version_part = plugin_name, None

            registry_plugin = get_registry_plugin(name_part)
            if registry_plugin:
                if version_part:
                    package_spec = f"{registry_plugin.package}=={version_part}"
                elif registry_plugin.version:
                    package_spec = f"{registry_plugin.package}=={registry_plugin.version}"
                else:
                    package_spec = registry_plugin.package
                display_name = f"{registry_plugin.name} ({registry_plugin.package})"
                return package_spec, display_name

            return plugin_name, plugin_name
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[str, str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;install_cmd&#x22;" type="&#x22;(plugin_name)&#x22;">
      Install a plugin from the registry (wraps pip).

      <PySourceCode>
        ```python
        @click.command(name="install")
        @click.argument("plugin_name")
        def install_cmd(plugin_name: str):
            """Install a plugin from the registry (wraps pip)."""
            try:
                name_part = plugin_name.split("==", 1)[0]
                package_spec, display_name = resolve_install_target(plugin_name)
                logger.info(
                    "plugin_install_started",
                    plugin_name=plugin_name,
                    package_spec=package_spec,
                )
                console.print(f"Installing {display_name}...")
                run_pip(["install", package_spec])
                installed = collect_installed_plugins("all")
                maybe_installed = [
                    plugin
                    for plugin in installed
                    if plugin["name"] == name_part or package_spec.startswith(plugin["name"])
                ]
                logger.info(
                    "plugin_install_succeeded",
                    plugin_name=plugin_name,
                    package_spec=package_spec,
                )
                console.print(f"[green]✓ Installed {display_name}[/green]")
                for plugin in maybe_installed:
                    missing_capabilities = plugin.get("missing_capabilities") or []
                    if missing_capabilities:
                        console.print(
                            "[yellow]Installed plugin has unmet capabilities:[/yellow] "
                            + f"{plugin['name']} -> {', '.join(missing_capabilities)}"
                        )
            except Exception as e:
                logger.exception("plugin_install_failed", plugin_name=plugin_name)
                console.print(f"[red]Error installing plugin: {e}[/red]")
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
