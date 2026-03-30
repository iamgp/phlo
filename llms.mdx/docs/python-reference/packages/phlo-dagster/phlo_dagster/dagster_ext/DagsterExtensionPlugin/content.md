# DagsterExtensionPlugin (/docs/python-reference/packages/phlo-dagster/phlo_dagster/dagster_ext/DagsterExtensionPlugin)



Base class for Dagster extension plugins.

These plugins contribute Dagster definitions (assets/resources/schedules/sensors/etc.)
to the running Phlo instance.

Functions [#functions]

<PyFunction name="&#x22;get_definitions&#x22;" type="&#x22;(self) -> Any&#x22;">
  Return Dagster definitions to merge into the global Definitions.

  <PySourceCode>
    ```python
    def get_definitions(self) -> Any:
        """Return Dagster definitions to merge into the global Definitions."""
        try:
            import dagster as dg
        except Exception as exc:  # noqa: BLE001 - optional dependency
            logger.error(
                "dagster_extension_definitions_import_failed",
                plugin_class=self.__class__.__name__,
                exc_info=True,
            )
            raise RuntimeError("Dagster is required for DagsterExtensionPlugin") from exc
        return dg.Definitions()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_exports&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Return exported symbols to attach to the `phlo` public API.

  Example: \{"ingestion": phlo\_ingestion}

  <PySourceCode>
    ```python
    def get_exports(self) -> dict[str, Any]:
        """
        Return exported symbols to attach to the `phlo` public API.

        Example: {"ingestion": phlo_ingestion}
        """
        return {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;clear_registries&#x22;" type="&#x22;(self) -> None&#x22;">
  Clear any global registries used by this plugin (primarily for module reload and tests).

  <PySourceCode>
    ```python
    def clear_registries(self) -> None:
        """
        Clear any global registries used by this plugin (primarily for module reload and tests).
        """
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
