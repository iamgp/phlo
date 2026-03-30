# selection (/docs/python-reference/core/phlo/orchestrators/selection)



Select the active orchestrator adapter.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_active_orchestrator&#x22;" type="&#x22;(name=None) -> OrchestratorAdapterPlugin&#x22;">
      Return the configured orchestrator adapter.

      <PySourceCode>
        ```python
        def get_active_orchestrator(name: str | None = None) -> OrchestratorAdapterPlugin:
            """Return the configured orchestrator adapter."""
            settings = get_settings()
            orchestrator_name = (name or settings.phlo_orchestrator or "dagster").strip()
            logger.debug("orchestrator_selection_started", requested_name=orchestrator_name)

            discover_plugins(plugin_type="orchestrators", auto_register=True)
            registry = get_global_registry()
            adapter = registry.get_orchestrator(orchestrator_name)
            if adapter is None:
                logger.warning(
                    "orchestrator_not_installed",
                    requested_name=orchestrator_name,
                    available_orchestrators=registry.list_orchestrators(),
                )
                raise PhloConfigError(
                    message=f"Orchestrator adapter '{orchestrator_name}' is not installed.",
                    suggestions=[
                        f"Install a package that provides '{orchestrator_name}'",
                        "Set PHLO_ORCHESTRATOR to an installed adapter name",
                    ],
                )
            logger.debug("orchestrator_selected", selected_name=orchestrator_name)
            return adapter
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.plugins.base.OrchestratorAdapterPlugin&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
