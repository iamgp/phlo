# catalog_generator (/docs/python-reference/packages/phlo-trino/phlo_trino/catalog_generator)



Trino catalog generator from discovered plugins.

This module generates Trino catalog configuration files (.properties)
from discovered catalog plugins. It supports both modern plugin discovery
and legacy entry-point based catalog loading.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;output&#x22;" type="null" value="&#x22;sys.argv[1] if len(sys.argv) > 1 else None&#x22;" />

<PyAttribute name="&#x22;result&#x22;" type="null" value="&#x22;generate_catalog_files(output)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_entry_points&#x22;" type="&#x22;(group) -> list[CatalogPlugin]&#x22;">
      Load catalog plugins from a Python entry-point group.

      <PySourceCode>
        ```python
        def _load_entry_points(group: str) -> list[CatalogPlugin]:
            """Load catalog plugins from a Python entry-point group.

            Args:
                group: Entry-point group name to resolve.

            Returns:
                Instantiated catalog plugins that inherit from ``CatalogPlugin``.

            """
            try:
                entry_points = importlib.metadata.entry_points(group=group)
            except TypeError:
                all_entry_points = importlib.metadata.entry_points()
                entry_points = all_entry_points.get(group, [])

            catalogs: list[CatalogPlugin] = []
            for entry_point in entry_points:
                try:
                    plugin_class = entry_point.load()
                    plugin = plugin_class() if isinstance(plugin_class, type) else plugin_class
                    if isinstance(plugin, CatalogPlugin):
                        catalogs.append(plugin)
                    else:
                        logger.error(
                            "Catalog plugin %s does not inherit from CatalogPlugin",
                            entry_point.name,
                        )
                except Exception as exc:
                    logger.error("Failed to instantiate catalog plugin %s: %s", entry_point.name, exc)

            return catalogs
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;group&#x22;" type="&#x22;str&#x22;" value="undefined">
          Entry-point group name to resolve.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Instantiated catalog plugins that inherit from `CatalogPlugin`.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_filter_catalogs&#x22;" type="&#x22;(catalogs, target) -> list[CatalogPlugin]&#x22;">
      Filter catalogs to those that support a target runtime.

      <PySourceCode>
        ```python
        def _filter_catalogs(catalogs: list[CatalogPlugin], target: str) -> list[CatalogPlugin]:
            """Filter catalogs to those that support a target runtime.

            Args:
                catalogs: Candidate catalog plugins.
                target: Target runtime identifier, for example ``"trino"``.

            Returns:
                Catalog plugins compatible with the requested target.

            """
            filtered: list[CatalogPlugin] = []
            for catalog in catalogs:
                if catalog.supports_target(target):
                    filtered.append(catalog)
                    logger.info("Discovered %s catalog: %s", target, catalog.catalog_name)
                else:
                    logger.debug(
                        "Skipping catalog %s (targets=%s) for target=%s",
                        catalog.catalog_name,
                        catalog.targets,
                        target,
                    )
            return filtered
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;catalogs&#x22;" type="&#x22;list[CatalogPlugin]&#x22;" value="undefined">
          Candidate catalog plugins.
        </PyParameter>

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target runtime identifier, for example `"trino"`.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Catalog plugins compatible with the requested target.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;discover_trino_catalogs&#x22;" type="&#x22;() -> list[CatalogPlugin]&#x22;">
      Discover Trino-compatible catalog plugins via entry points.

      <PySourceCode>
        ```python
        def discover_trino_catalogs() -> list[CatalogPlugin]:
            """Discover Trino-compatible catalog plugins via entry points."""
            plugins = discover_plugins(plugin_type="catalogs", auto_register=False)
            catalogs: list[CatalogPlugin] = []
            for plugin in plugins.get("catalogs", []):
                if isinstance(plugin, CatalogPlugin):
                    catalogs.append(plugin)

            legacy_catalogs = _load_entry_points("phlo.plugins.trino_catalogs")
            if legacy_catalogs:
                logger.warning(
                    "Detected legacy phlo.plugins.trino_catalogs entry points. "
                    "Please migrate to phlo.plugins.catalogs."
                )

            combined = catalogs + legacy_catalogs
            unique: dict[str, CatalogPlugin] = {}
            for catalog in combined:
                if catalog.catalog_name not in unique:
                    unique[catalog.catalog_name] = catalog

            return _filter_catalogs(list(unique.values()), "trino")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[phlo.plugins.base.CatalogPlugin]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_to_properties_file&#x22;" type="&#x22;(properties) -> str&#x22;">
      Serialize catalog properties to Java `.properties` text.

      <PySourceCode>
        ```python
        def _to_properties_file(properties: dict[str, object]) -> str:
            """Serialize catalog properties to Java ``.properties`` text.

            Args:
                properties: Catalog key/value properties.

            Returns:
                Newline-delimited ``key=value`` content with escaped values.

            """

            def escape_value(value: object) -> str:
                """Escape a value for Java ``.properties`` output.

                Args:
                    value: Property key or value to escape.

                Returns:
                    Escaped text safe for ``.properties`` files.

                """
                text = str(value)
                text = text.replace("\\", "\\\\")
                text = text.replace("\t", "\\t")
                text = text.replace("\n", "\\n")
                text = text.replace("\r", "\\r")
                text = text.replace("\f", "\\f")
                if text and text[0] in (" ", "\t", "#", "!"):
                    text = f"\\{text}"
                text = text.replace("=", "\\=")
                text = text.replace(":", "\\:")
                return text

            lines = [f"{escape_value(key)}={escape_value(value)}" for key, value in properties.items()]
            return "\n".join(lines) + "\n"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;properties&#x22;" type="&#x22;dict[str, object]&#x22;" value="undefined">
          Catalog key/value properties.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Newline-delimited `key=value` content with escaped values.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;generate_catalog_files&#x22;" type="&#x22;(output_dir=None) -> dict[str, Path]&#x22;">
      Generate Trino catalog .properties files from discovered plugins.

      <PySourceCode>
        ```python
        def generate_catalog_files(output_dir: str | Path | None = None) -> dict[str, Path]:
            """Generate Trino catalog .properties files from discovered plugins.

            Args:
                output_dir: Directory to write catalog files. Defaults to ./trino/catalog/

            Returns:
                Dictionary mapping catalog name to generated file path

            """
            if output_dir is None:
                output_dir = Path(os.environ.get("TRINO_CATALOG_DIR", "./trino/catalog"))
            else:
                output_dir = Path(output_dir)

            output_dir.mkdir(parents=True, exist_ok=True)

            catalogs = discover_trino_catalogs()
            generated = {}

            for catalog in catalogs:
                try:
                    filename = f"{catalog.catalog_name}.properties"
                    filepath = output_dir / filename
                    content = _to_properties_file(catalog.get_properties())

                    filepath.write_text(content)
                    generated[catalog.catalog_name] = filepath
                    logger.info("Generated catalog file: %s", filepath)
                except Exception as exc:
                    logger.error("Failed to generate catalog %s: %s", catalog.catalog_name, exc)

            return generated
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output_dir&#x22;" type="&#x22;str | Path | None&#x22;" value="&#x22;None&#x22;">
          Directory to write catalog files. Defaults to ./trino/catalog/
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary mapping catalog name to generated file path
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
