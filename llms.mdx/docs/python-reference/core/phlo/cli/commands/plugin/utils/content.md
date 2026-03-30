# utils (/docs/python-reference/core/phlo/cli/commands/plugin/utils)



Shared utilities for plugin commands.

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;PLUGIN_TYPE_MAP&#x22;" type="null" value="&#x22;{'sources': 'source_connectors', 'quality': 'quality_checks', 'transforms': 'transformations', 'services': 'services', 'hooks': 'hooks', 'assets': 'asset_providers', 'resources': 'resource_providers', 'orchestrators': 'orchestrators', 'catalogs': 'catalogs'}&#x22;" />

<PyAttribute name="&#x22;PLUGIN_TYPE_CHOICES&#x22;" type="null" value="&#x22;['sources', 'quality', 'transforms', 'services', 'hooks', 'assets', 'resources', 'orchestrators', 'catalogs']&#x22;" />

<PyAttribute name="&#x22;INTERNAL_TO_REGISTRY_TYPE&#x22;" type="null" value="&#x22;{'source_connectors': 'source', 'quality_checks': 'quality', 'transformations': 'transform', 'services': 'service', 'hooks': 'hooks', 'asset_providers': 'assets', 'resource_providers': 'resources', 'orchestrators': 'orchestrators', 'catalogs': 'catalogs'}&#x22;" />

<PyAttribute name="&#x22;SCAFFOLD_TYPE_MAP&#x22;" type="null" value="&#x22;{'sources': 'source', 'quality': 'quality', 'transforms': 'transform', 'services': 'service', 'hooks': 'hook', 'catalogs': 'catalog', 'assets': 'asset', 'resources': 'resource', 'orchestrators': 'orchestrator'}&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;run_pip&#x22;" type="&#x22;(args, *, timeout=300) -> None&#x22;">
      Install packages using pip, with uv fallback for uv-managed environments.

      <PySourceCode>
        ```python
        def run_pip(args: list[str], *, timeout: float = 300) -> None:
            """Install packages using pip, with uv fallback for uv-managed environments."""
            operation = args[0] if args else "unknown"
            if importlib.util.find_spec("pip") is not None:
                command = [sys.executable, "-m", "pip", *args]
                installer = "pip"
            else:
                if shutil.which("uv") is None:
                    raise RuntimeError(
                        "pip module is unavailable and 'uv' is not installed; cannot install packages."
                    )
                command = ["uv", "pip", *args]
                installer = "uv"

            try:
                logger.info("plugin_pip_command_started", operation=operation, installer=installer)
                subprocess.run(command, check=True, timeout=timeout)
                logger.info("plugin_pip_command_succeeded", operation=operation, installer=installer)
            except subprocess.CalledProcessError as exc:
                logger.error(
                    "plugin_pip_command_failed",
                    operation=operation,
                    installer=installer,
                    return_code=exc.returncode,
                )
                raise
            except subprocess.TimeoutExpired as exc:
                message = f"Install command timed out after {timeout}s: {' '.join(command)}"
                logger.error(
                    "plugin_pip_command_timed_out",
                    operation=operation,
                    installer=installer,
                    timeout_seconds=timeout,
                )
                raise RuntimeError(message) from exc
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;args&#x22;" type="&#x22;list[str]&#x22;" value="null" />

        <PyParameter name="&#x22;timeout&#x22;" type="&#x22;float&#x22;" value="&#x22;300&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;registry_plugin_to_dict&#x22;" type="&#x22;(plugin) -> dict&#x22;">
      Convert registry plugin to dictionary.

      <PySourceCode>
        ```python
        def registry_plugin_to_dict(plugin) -> dict:
            """Convert registry plugin to dictionary."""
            return {
                "name": plugin.name,
                "type": plugin.type,
                "package": plugin.package,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "homepage": plugin.homepage,
                "tags": plugin.tags,
                "verified": plugin.verified,
                "core": plugin.core,
            }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin&#x22;" type="null" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;collect_installed_plugins&#x22;" type="&#x22;(plugin_type) -> list[dict]&#x22;">
      Collect installed plugins of given type.

      <PySourceCode>
        ```python
        def collect_installed_plugins(plugin_type: str) -> list[dict]:
            """Collect installed plugins of given type."""
            registry = get_global_registry()
            installed: list[dict] = []

            def add_plugin(plugin_key: str, name: str) -> None:
                """Append discovered plugin metadata for one registry entry."""
                info = get_plugin_info(plugin_key, name)
                if not info:
                    return
                required_capabilities = info.get("requires_capabilities", [])
                optional_capabilities = info.get("optional_capabilities", [])
                support = coerce_capability_support(info.get("support"))
                missing_capabilities = missing_required_capabilities(
                    PluginMetadata(
                        name=info["name"],
                        version=info["version"],
                        requires_capabilities=list(required_capabilities),
                        optional_capabilities=list(optional_capabilities),
                        support=support,
                    )
                )
                installed.append(
                    {
                        "name": info["name"],
                        "type": INTERNAL_TO_REGISTRY_TYPE.get(plugin_key, plugin_key),
                        "version": info["version"],
                        "description": info.get("description", ""),
                        "author": info.get("author", ""),
                        "homepage": info.get("homepage", ""),
                        "tags": info.get("tags", []),
                        "installed": True,
                        "required_capabilities": required_capabilities,
                        "optional_capabilities": optional_capabilities,
                        "support": support.to_dict(),
                        "missing_capabilities": missing_capabilities,
                        "ready": len(missing_capabilities) == 0,
                    }
                )

            for type_key, names in registry.list_all_plugins().items():
                if plugin_type != "all" and PLUGIN_TYPE_MAP.get(plugin_type) != type_key:
                    continue
                if type_key == "services":
                    for name in names:
                        service = get_service(name)
                        if not service:
                            continue
                        metadata = service.metadata
                        missing_capabilities = missing_required_capabilities(metadata)
                        installed.append(
                            {
                                "name": metadata.name,
                                "type": "service",
                                "version": metadata.version,
                                "description": metadata.description,
                                "author": metadata.author,
                                "homepage": metadata.homepage,
                                "tags": metadata.tags,
                                "installed": True,
                                "category": service.category,
                                "profile": service.profile,
                                "default": service.is_default,
                                "required_capabilities": metadata.requires_capabilities,
                                "optional_capabilities": metadata.optional_capabilities,
                                "support": metadata.support.to_dict(),
                                "missing_capabilities": missing_capabilities,
                                "ready": len(missing_capabilities) == 0,
                            }
                        )
                    continue

                for name in names:
                    add_plugin(type_key, name)

            return installed
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.cli.commands.plugin.list[dict]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;collect_registry_plugins&#x22;" type="&#x22;(plugin_type) -> list[dict]&#x22;">
      Collect registry plugins of given type.

      <PySourceCode>
        ```python
        def collect_registry_plugins(plugin_type: str) -> list[dict]:
            """Collect registry plugins of given type."""
            from phlo.plugins.registry_client import list_registry_plugins

            registry_plugins = list_registry_plugins()
            if plugin_type != "all":
                # Translate CLI type to internal type first, then to registry type
                internal_type = PLUGIN_TYPE_MAP.get(plugin_type, plugin_type)
                registry_type = INTERNAL_TO_REGISTRY_TYPE.get(internal_type)
                registry_plugins = [plugin for plugin in registry_plugins if plugin.type == registry_type]
            return [registry_plugin_to_dict(plugin) for plugin in registry_plugins]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.cli.commands.plugin.list[dict]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;render_plugin_table&#x22;" type="&#x22;(title, plugins) -> None&#x22;">
      Render a table of plugins.

      <PySourceCode>
        ```python
        def render_plugin_table(title: str, plugins: list[dict]) -> None:
            """Render a table of plugins."""
            console.print(f"\n{title}:")
            if not plugins:
                console.print("  (none)")
                return

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Version", style="yellow")
            table.add_column("Author", style="white")
            table.add_column("Ready", style="magenta")

            for plugin in plugins:
                ready = plugin.get("ready")
                ready_label = "yes" if ready is True else ("no" if ready is False else "n/a")
                missing = plugin.get("missing_capabilities") or []
                if ready is False and missing:
                    ready_label = f"no ({', '.join(missing)})"
                table.add_row(
                    plugin["name"],
                    plugin["type"],
                    plugin["version"],
                    plugin.get("author", "unknown") or "unknown",
                    ready_label,
                )

            console.print(table)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;title&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugins&#x22;" type="&#x22;list[dict]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_installed_version&#x22;" type="&#x22;(package) -> str | None&#x22;">
      Get installed version of a package.

      <PySourceCode>
        ```python
        def get_installed_version(package: str) -> str | None:
            """Get installed version of a package."""
            try:
                return importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;package&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;version_tuple&#x22;" type="&#x22;(version) -> tuple[int, object]&#x22;">
      Convert version string to tuple for comparison.

      <PySourceCode>
        ```python
        def version_tuple(version: str) -> tuple[int, object]:
            """Convert version string to tuple for comparison."""
            try:
                return (0, parse(version))
            except Exception:
                return (0, parse("0"))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[int, object]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;is_version_newer&#x22;" type="&#x22;(installed, available) -> bool&#x22;">
      Check if available version is newer than installed.

      <PySourceCode>
        ```python
        def is_version_newer(installed: str, available: str) -> bool:
            """Check if available version is newer than installed."""
            try:
                return parse(available) > parse(installed)
            except Exception:
                return available != installed
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;installed&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;available&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;find_available_updates&#x22;" type="&#x22;(registry_plugins) -> list[dict]&#x22;">
      Find available updates for installed plugins.

      <PySourceCode>
        ```python
        def find_available_updates(registry_plugins) -> list[dict]:
            """Find available updates for installed plugins."""
            updates = []
            for plugin in registry_plugins:
                installed_version = get_installed_version(plugin.package)
                if not installed_version:
                    continue
                if is_version_newer(installed_version, plugin.version):
                    updates.append(
                        {
                            "name": plugin.name,
                            "package": plugin.package,
                            "installed_version": installed_version,
                            "available_version": plugin.version,
                        }
                    )
            return updates
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;registry_plugins&#x22;" type="null" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.cli.commands.plugin.list[dict]&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
