# ServiceDiscovery (/docs/python-reference/core/phlo/plugins/discovery/services/ServiceDiscovery)



Discovers and manages service definitions.

Attributes [#attributes]

<PyAttribute name="&#x22;services_dir&#x22;" type="null" value="&#x22;services_dir&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, services_dir=None)&#x22;">
  Initialize with an optional services directory.

  <PySourceCode>
    ```python
    def __init__(self, services_dir: Path | None = None):
        """Initialize with an optional services directory.

        Args:
            services_dir: Optional path to additional service.yaml files. If None,
                services are discovered exclusively from installed service plugins.
        """
        self.services_dir = services_dir
        self._services: dict[str, ServiceDefinition] = {}
        self._loaded = False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;services_dir&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;">
      Optional path to additional service.yaml files. If None,
      services are discovered exclusively from installed service plugins.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;discover&#x22;" type="&#x22;(self, refresh=False) -> dict[str, ServiceDefinition]&#x22;">
  Discover all service definitions.

  <PySourceCode>
    ```python
    def discover(self, refresh: bool = False) -> dict[str, ServiceDefinition]:
        """Discover all service definitions.

        Args:
            refresh: If ``True``, clear cached state and re-run discovery.

        Returns:
            Dictionary mapping service names to their definitions.
        """
        if refresh:
            _emit_service_discovery_signal(
                event_name="service_discovery_refresh_requested",
                level="info",
                services_dir=self.services_dir,
                cached_service_count=len(self._services),
                cache_loaded=self._loaded,
            )
            self.clear_cache()

        if self._loaded:
            _emit_service_discovery_signal(
                event_name="service_discovery_cache_hit",
                level="debug",
                services_dir=self.services_dir,
                service_count=len(self._services),
            )
            return self._services

        _emit_service_discovery_signal(
            event_name="service_discovery_cache_miss",
            level="debug",
            services_dir=self.services_dir,
            refresh=refresh,
        )

        self._services = {}
        plugin_service_count = self._load_service_plugins()
        file_service_count = 0

        # Then load filesystem services
        if self.services_dir and self.services_dir.exists():
            # Search for service.yaml files in all subdirectories
            for yaml_path in self.services_dir.rglob("*.yaml"):
                # Skip schema files and non-service files
                if ".schema" in str(yaml_path):
                    continue
                if not self._is_service_yaml(yaml_path.name):
                    continue

                try:
                    service = ServiceDefinition.from_yaml(yaml_path)
                    if service.name in self._services:
                        continue
                    self._services[service.name] = service
                    file_service_count += 1
                except (yaml.YAMLError, KeyError) as e:
                    _emit_service_discovery_signal(
                        event_name="service_discovery_file_load_failed",
                        level="warning",
                        services_dir=self.services_dir,
                        yaml_path=str(yaml_path),
                        error=str(e),
                        error_type=type(e).__name__,
                    )

        self._loaded = True
        _emit_service_discovery_signal(
            event_name="service_discovery_completed",
            level="info",
            services_dir=self.services_dir,
            service_count=len(self._services),
            plugin_service_count=plugin_service_count,
            file_service_count=file_service_count,
        )
        return self._services
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;refresh&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
      If `True`, clear cached state and re-run discovery.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary mapping service names to their definitions.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;clear_cache&#x22;" type="&#x22;(self) -> None&#x22;">
  Clear cached discovery state.

  The next :meth:`discover` call will perform a full rediscovery.

  <PySourceCode>
    ```python
    def clear_cache(self) -> None:
        """Clear cached discovery state.

        The next :meth:`discover` call will perform a full rediscovery.
        """
        registry = get_global_registry()
        for service_name in list(registry.list_services()):
            registry._services.pop(service_name, None)  # noqa: SLF001
            registry._all_plugins.pop(f"service:{service_name}", None)  # noqa: SLF001

        cached_service_count = len(self._services)
        was_loaded = self._loaded
        self._services = {}
        self._loaded = False
        _emit_service_discovery_signal(
            event_name="service_discovery_cache_cleared",
            level="info",
            services_dir=self.services_dir,
            cached_service_count=cached_service_count,
            cache_was_loaded=was_loaded,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;refresh&#x22;" type="&#x22;(self) -> dict[str, ServiceDefinition]&#x22;">
  Force rediscovery and return refreshed service definitions.

  <PySourceCode>
    ```python
    def refresh(self) -> dict[str, ServiceDefinition]:
        """Force rediscovery and return refreshed service definitions."""
        return self.discover(refresh=True)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, phlo.plugins.discovery._service_definition.ServiceDefinition]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_load_service_plugins&#x22;" type="&#x22;(self) -> int&#x22;">
  Load services from installed plugins.

  <PySourceCode>
    ```python
    def _load_service_plugins(self) -> int:
        """Load services from installed plugins."""
        loaded_count = 0
        registry = get_global_registry()
        discover_plugins(plugin_type="services", auto_register=True)
        for name in registry.list_services():
            plugin = registry.get_service(name)
            if not plugin:
                continue
            # Skip if already loaded as core service
            if name in self._services:
                logger.debug("plugin_service_skipped_core_exists", service_name=name)
                continue
            service_definition = plugin.service_definition
            source_path = _resolve_plugin_source_path(plugin)
            try:
                service = ServiceDefinition.from_dict(service_definition, source_path)
                self._services[service.name] = service
                loaded_count += 1
                loaded_count += self._load_companion_service_files(source_path)
            except KeyError as exc:
                _emit_service_discovery_signal(
                    event_name="service_discovery_plugin_load_failed",
                    level="warning",
                    services_dir=self.services_dir,
                    plugin_name=name,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
        return loaded_count
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_is_service_yaml&#x22;" type="&#x22;(filename) -> bool&#x22;">
  Check if filename is a recognized service YAML pattern.

  <PySourceCode>
    ```python
    @staticmethod
    def _is_service_yaml(filename: str) -> bool:
        """Check if filename is a recognized service YAML pattern."""
        return filename == "service.yaml" or filename.endswith(("-setup.yaml", "-daemon.yaml"))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;filename&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_load_companion_service_files&#x22;" type="&#x22;(self, source_path) -> int&#x22;">
  Load companion service YAMLs (e.g., \*-setup.yaml, \*-daemon.yaml) from a package.

  <PySourceCode>
    ```python
    def _load_companion_service_files(self, source_path: Path | None) -> int:
        """Load companion service YAMLs (e.g., *-setup.yaml, *-daemon.yaml) from a package."""
        if not source_path or not source_path.exists():
            return 0

        loaded_count = 0
        for yaml_path in source_path.rglob("*.yaml"):
            filename = yaml_path.name
            if filename == "service.yaml":
                continue
            if not filename.endswith(("-setup.yaml", "-daemon.yaml")):
                continue
            try:
                service = ServiceDefinition.from_yaml(yaml_path)
                if service.name in self._services:
                    continue
                self._services[service.name] = service
                loaded_count += 1
            except (yaml.YAMLError, KeyError) as exc:
                _emit_service_discovery_signal(
                    event_name="service_discovery_companion_file_load_failed",
                    level="warning",
                    services_dir=self.services_dir,
                    yaml_path=str(yaml_path),
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
        return loaded_count
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_path&#x22;" type="&#x22;Path | None&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_service&#x22;" type="&#x22;(self, name) -> ServiceDefinition | None&#x22;">
  Get a service definition by name.

  <PySourceCode>
    ```python
    def get_service(self, name: str) -> ServiceDefinition | None:
        """Get a service definition by name."""
        self.discover()
        return self._services.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery._service_definition.ServiceDefinition | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_default_services&#x22;" type="&#x22;(self, disabled_services=None) -> list[ServiceDefinition]&#x22;">
  Get all services marked as default, excluding disabled ones.

  <PySourceCode>
    ```python
    def get_default_services(
        self, disabled_services: set[str] | None = None
    ) -> list[ServiceDefinition]:
        """Get all services marked as default, excluding disabled ones.

        Args:
            disabled_services: Set of service names to exclude.
        """
        self.discover()
        disabled = disabled_services or set()
        return [s for s in self._services.values() if s.default and s.name not in disabled]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;disabled_services&#x22;" type="&#x22;set[str] | None&#x22;" value="&#x22;None&#x22;">
      Set of service names to exclude.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.plugins.discovery._service_definition.ServiceDefinition]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_services_by_profile&#x22;" type="&#x22;(self, profile) -> list[ServiceDefinition]&#x22;">
  Get all services in a specific profile.

  <PySourceCode>
    ```python
    def get_services_by_profile(self, profile: str) -> list[ServiceDefinition]:
        """Get all services in a specific profile."""
        self.discover()
        return [s for s in self._services.values() if s.profile == profile]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;profile&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.plugins.discovery._service_definition.ServiceDefinition]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_services_by_category&#x22;" type="&#x22;(self, category) -> list[ServiceDefinition]&#x22;">
  Get all services in a specific category.

  <PySourceCode>
    ```python
    def get_services_by_category(self, category: str) -> list[ServiceDefinition]:
        """Get all services in a specific category."""
        self.discover()
        return [s for s in self._services.values() if s.category == category]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;category&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.plugins.discovery._service_definition.ServiceDefinition]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_available_profiles&#x22;" type="&#x22;(self) -> set[str]&#x22;">
  Get all available profile names.

  <PySourceCode>
    ```python
    def get_available_profiles(self) -> set[str]:
        """Get all available profile names."""
        self.discover()
        return {s.profile for s in self._services.values() if s.profile}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;set[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;resolve_dependencies&#x22;" type="&#x22;(self, services) -> list[ServiceDefinition]&#x22;">
  Resolve and sort services by dependencies (topological sort).

  <PySourceCode>
    ```python
    def resolve_dependencies(self, services: list[ServiceDefinition]) -> list[ServiceDefinition]:
        """Resolve and sort services by dependencies (topological sort).

        Args:
            services: List of services to sort.

        Returns:
            List of services in dependency order (dependencies first).

        Raises:
            ValueError: If circular dependencies are detected.
        """
        self.discover()

        return resolve_service_dependencies(services)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;services&#x22;" type="&#x22;list[ServiceDefinition]&#x22;" value="undefined">
      List of services to sort.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of services in dependency order (dependencies first).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_all&#x22;" type="&#x22;(self) -> list[dict[str, Any]]&#x22;">
  List all services with their metadata.

  <PySourceCode>
    ```python
    def list_all(self) -> list[dict[str, Any]]:
        """List all services with their metadata.

        Returns:
            List of service info dictionaries.
        """
        self.discover()
        return [
            {
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "default": s.default,
                "profile": s.profile,
                "depends_on": s.depends_on,
            }
            for s in sorted(self._services.values(), key=lambda x: (x.category, x.name))
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of service info dictionaries.
  </PyFunctionReturn>
</PyFunction>
