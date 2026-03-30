# capabilities (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/capabilities)



Capability resolution helpers for phlo-openmetadata.

This module provides utilities for resolving phlo capability providers
needed by OpenMetadata integration, specifically catalog scanners and
query engine metadata.

Example:

> > > from phlo\_openmetadata.capabilities import resolve\_catalog\_scanner
> > > scanner = resolve\_catalog\_scanner()
> > > tables = scanner.scan\_all\_tables()

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_discover_capabilities&#x22;" type="&#x22;() -> None&#x22;">
      Trigger capability discovery to populate the registry.

      This internal function ensures all capability providers are loaded
      before attempting to resolve specific capabilities.

      <PySourceCode>
        ```python
        def _discover_capabilities() -> None:
            """Trigger capability discovery to populate the registry.

            This internal function ensures all capability providers are loaded
            before attempting to resolve specific capabilities.
            """
            from phlo.capabilities.discovery import discover_capabilities

            discover_capabilities()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;resolve_catalog_scanner&#x22;" type="&#x22;(name=None) -> CatalogScanner&#x22;">
      Resolve a catalog scanner capability for metadata sync flows.

      <PySourceCode>
        ```python
        def resolve_catalog_scanner(name: str | None = None) -> CatalogScanner:
            """Resolve a catalog scanner capability for metadata sync flows.

            Args:
                name: Optional name of a specific scanner to resolve. If None,
                    returns the first available scanner.

            Returns:
                CatalogScanner: A catalog scanner capability provider.

            Raises:
                RuntimeError: If the specified scanner or any scanner is not available.

            """
            _discover_capabilities()
            resolution = resolve_capability("catalog_scanner", name)
            if resolution is None:
                if name:
                    raise RuntimeError(f"Catalog scanner capability '{name}' is not available.")
                raise RuntimeError("No catalog scanner capability is available.")
            return resolution.provider
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional name of a specific scanner to resolve. If None,
          returns the first available scanner.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.CatalogScanner&#x22;">
        A catalog scanner capability provider.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;resolve_query_engine_catalog&#x22;" type="&#x22;(name=None) -> str&#x22;">
      Resolve the default catalog name from query-engine capability metadata.

      <PySourceCode>
        ```python
        def resolve_query_engine_catalog(name: str | None = None) -> str:
            """Resolve the default catalog name from query-engine capability metadata.

            Args:
                name: Optional name of a specific query engine to resolve. If None,
                    uses the first available query engine.

            Returns:
                str: The catalog name from the query engine metadata.

            Raises:
                RuntimeError: If the query engine is not available or lacks catalog metadata.

            """
            _discover_capabilities()
            resolution = resolve_capability("query_engine", name)
            if resolution is None:
                if name:
                    raise RuntimeError(f"Query engine capability '{name}' is not available.")
                raise RuntimeError("No query engine capability is available.")

            metadata = resolution.metadata
            for key in ("catalog", "default_catalog", "catalog_name"):
                catalog = metadata.get(key)
                if isinstance(catalog, str) and catalog:
                    return catalog

            provider_name = name or getattr(resolution, "name", None) or "resolved query engine"
            raise RuntimeError(
                f"Query engine capability '{provider_name}' does not declare catalog metadata."
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional name of a specific query engine to resolve. If None,
          uses the first available query engine.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        The catalog name from the query engine metadata.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;resolve_query_engine_service_type&#x22;" type="&#x22;(name=None) -> str&#x22;">
      Resolve the OpenMetadata service type from query-engine capability metadata.

      <PySourceCode>
        ```python
        def resolve_query_engine_service_type(name: str | None = None) -> str:
            """Resolve the OpenMetadata service type from query-engine capability metadata.

            Args:
                name: Optional name of a specific query engine to resolve. If None,
                    uses the first available query engine.

            Returns:
                str: The OpenMetadata service type (e.g., 'Trino', 'Snowflake').

            Raises:
                RuntimeError: If the query engine is not available or lacks service_type metadata.

            """
            _discover_capabilities()
            resolution = resolve_capability("query_engine", name)
            if resolution is None:
                if name:
                    raise RuntimeError(f"Query engine capability '{name}' is not available.")
                raise RuntimeError("No query engine capability is available.")

            metadata = resolution.metadata
            for key in ("service_type", "openmetadata_service_type"):
                service_type = metadata.get(key)
                if isinstance(service_type, str) and service_type:
                    return service_type

            provider_name = name or getattr(resolution, "name", None) or "resolved query engine"
            raise RuntimeError(
                f"Query engine capability '{provider_name}' does not declare service_type metadata."
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional name of a specific query engine to resolve. If None,
          uses the first available query engine.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        The OpenMetadata service type (e.g., 'Trino', 'Snowflake').
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
