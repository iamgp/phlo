# services (/docs/python-reference/core/phlo/plugins/discovery/services)



Service Discovery Module

Discovers and loads service definitions from installed plugins and optional directories.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ServiceDiscovery&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/services/ServiceDiscovery&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_services_dir_label&#x22;" type="&#x22;(services_dir) -> str&#x22;">
      Normalize the services directory path for structured observability fields.

      <PySourceCode>
        ```python
        def _services_dir_label(services_dir: Path | None) -> str:
            """Normalize the services directory path for structured observability fields."""
            return str(services_dir) if services_dir else "<plugins-only>"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;services_dir&#x22;" type="&#x22;Path | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_emit_service_discovery_signal&#x22;" type="&#x22;(*, event_name, level, services_dir, **fields) -> None&#x22;">
      Emit a structured observability event for service discovery flows.

      <PySourceCode>
        ```python
        def _emit_service_discovery_signal(
            *,
            event_name: str,
            level: str,
            services_dir: Path | None,
            **fields: Any,
        ) -> None:
            """Emit a structured observability event for service discovery flows."""
            log_event(
                logger,
                level,
                event_name,
                services_dir=_services_dir_label(services_dir),
                **fields,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;services_dir&#x22;" type="&#x22;Path | None&#x22;" value="null" />

        <PyParameter name="&#x22;fields&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;discover_plugins&#x22;" type="&#x22;(plugin_type='services', auto_register=True)&#x22;">
      Compatibility wrapper for tests and service discovery call sites.

      <PySourceCode>
        ```python
        def discover_plugins(plugin_type: str = "services", auto_register: bool = True):
            """Compatibility wrapper for tests and service discovery call sites."""
            return _service_loading.discover_plugins(plugin_type=plugin_type, auto_register=auto_register)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'services'&#x22;" />

        <PyParameter name="&#x22;auto_register&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;_find_cycles&#x22;" type="&#x22;(nodes, graph) -> list[list[str]]&#x22;">
      Compatibility wrapper around shared cycle-detection utilities.

      <PySourceCode>
        ```python
        def _find_cycles(nodes: set[str], graph: dict[str, set[str]]) -> list[list[str]]:
            """Compatibility wrapper around shared cycle-detection utilities."""
            return _find_cycles_impl(nodes, graph)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;nodes&#x22;" type="&#x22;set[str]&#x22;" value="null" />

        <PyParameter name="&#x22;graph&#x22;" type="&#x22;dict[str, set[str]]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[list[str]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_plugin_source_path&#x22;" type="&#x22;(plugin) -> Path | None&#x22;">
      <PySourceCode>
        ```python
        def _resolve_plugin_source_path(plugin: Any) -> Path | None:
            module_name = plugin.__class__.__module__
            package_name = module_name.split(".", 1)[0]
            spec = find_spec(package_name)
            if not spec or not spec.origin:
                return None
            return Path(spec.origin).parent
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path | None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
