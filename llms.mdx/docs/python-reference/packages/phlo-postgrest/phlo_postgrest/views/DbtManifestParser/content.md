# DbtManifestParser (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/DbtManifestParser)



Parser for dbt manifest.json files.

Extracts model metadata from dbt's compilation output, supporting
schema filtering and dependency graph construction for view
generation and ordering.

Attributes [#attributes]

<PyAttribute name="&#x22;manifest_path&#x22;" type="null" value="&#x22;Path(manifest_path)&#x22;">
  Path to manifest.json file.
</PyAttribute>

<PyAttribute name="&#x22;source_schema&#x22;" type="null" value="&#x22;source_schema&#x22;">
  Schema to filter models (e.g., 'marts').
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, manifest_path=None, source_schema=None)&#x22;">
  Initialize manifest parser with configuration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > parser = DbtManifestParser(
    > > > ...     "workflows/transforms/dbt/target/manifest.json",
    > > > ...     "marts"
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def __init__(self, manifest_path: Optional[str] = None, source_schema: Optional[str] = None):
        """Initialize manifest parser with configuration.

        Args:
            manifest_path: Path to manifest.json. Uses settings if None.
            source_schema: Schema to filter models. Uses settings if None.

        Raises:
            FileNotFoundError: If manifest.json doesn't exist at specified path.

        Example:
            >>> parser = DbtManifestParser(
            ...     "workflows/transforms/dbt/target/manifest.json",
            ...     "marts"
            ... )

        """
        settings = PostgrestViewsSettings()
        if manifest_path is None:
            manifest_path = settings.dbt_manifest_path
        if source_schema is None:
            source_schema = settings.dbt_api_source_schema

        self.manifest_path = Path(manifest_path)
        self.source_schema = source_schema

        if not self.manifest_path.exists():
            raise FileNotFoundError(f"dbt manifest not found at {manifest_path}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;manifest_path&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Path to manifest.json. Uses settings if None.
    </PyParameter>

    <PyParameter name="&#x22;source_schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Schema to filter models. Uses settings if None.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;parse&#x22;" type="&#x22;(self) -> dict[str, DbtModel]&#x22;">
  Parse manifest and extract filtered models.

  Reads manifest.json and extracts all model nodes matching the
  configured source\_schema, constructing DbtModel instances.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > parser = DbtManifestParser(source\_schema="marts")
    > > > models = parser.parse()
    > > > list(models.keys())
    > > > \['mrt\_orders', 'mrt\_customers']
  </Callout>

  <PySourceCode>
    ```python
    def parse(self) -> dict[str, DbtModel]:
        """Parse manifest and extract filtered models.

        Reads manifest.json and extracts all model nodes matching the
        configured source_schema, constructing DbtModel instances.

        Returns:
            dict[str, DbtModel]: Mapping of model names to DbtModel objects.

        Raises:
            FileNotFoundError: If manifest file is missing.
            json.JSONDecodeError: If manifest contains invalid JSON.

        Example:
            >>> parser = DbtManifestParser(source_schema="marts")
            >>> models = parser.parse()
            >>> list(models.keys())
            ['mrt_orders', 'mrt_customers']

        """
        with open(self.manifest_path) as f:
            manifest = json.load(f)

        source_schema = self.source_schema or self._infer_source_schema(manifest)

        models = {}
        for unique_id, node in manifest.get("nodes", {}).items():
            if not unique_id.startswith("model."):
                continue

            if node.get("schema") != source_schema:
                continue

            model = DbtModel(
                name=node.get("name"),
                schema=node.get("schema"),
                description=node.get("description", ""),
                columns=node.get("columns", {}),
                tags=node.get("tags", []),
                unique_id=unique_id,
            )

            models[model.name] = model

        return models
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, DbtModel]: Mapping of model names to DbtModel objects.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_infer_source_schema&#x22;" type="&#x22;(self, manifest) -> str&#x22;">
  Infer source schema when not explicitly configured.

  Analyzes all models in manifest and determines schema when only
  one unique schema is present. Raises error if multiple schemas
  exist and none is specified.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > schema = parser.\_infer\_source\_schema(manifest)
    > > > print(schema)
    > > > 'marts'
  </Callout>

  <PySourceCode>
    ```python
    def _infer_source_schema(self, manifest: dict) -> str:
        """Infer source schema when not explicitly configured.

        Analyzes all models in manifest and determines schema when only
        one unique schema is present. Raises error if multiple schemas
        exist and none is specified.

        Args:
            manifest: Parsed manifest.json dictionary.

        Returns:
            str: The inferred schema name.

        Raises:
            ValueError: If multiple schemas exist without explicit configuration.

        Example:
            >>> schema = parser._infer_source_schema(manifest)
            >>> print(schema)
            'marts'

        """
        schemas = {
            node.get("schema")
            for unique_id, node in manifest.get("nodes", {}).items()
            if unique_id.startswith("model.") and isinstance(node.get("schema"), str)
        }
        if len(schemas) == 1:
            return next(iter(schemas))
        raise ValueError(
            "dbt_api_source_schema is not configured and manifest contains multiple model "
            f"schemas: {sorted(schemas)}"
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;manifest&#x22;" type="&#x22;dict&#x22;" value="undefined">
      Parsed manifest.json dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    The inferred schema name.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;build_dependency_graph&#x22;" type="&#x22;(self) -> dict[str, list[str]]&#x22;">
  Build model dependency graph from manifest.

  Constructs a directed graph of model dependencies for topological
  sorting during view generation, ensuring views are created in
  correct order.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > graph = parser.build\_dependency\_graph()
    > > > graph.get("mrt\_orders")
    > > > \['stg\_orders', 'stg\_customers']
  </Callout>

  <PySourceCode>
    ```python
    def build_dependency_graph(self) -> dict[str, list[str]]:
        """Build model dependency graph from manifest.

        Constructs a directed graph of model dependencies for topological
        sorting during view generation, ensuring views are created in
        correct order.

        Returns:
            dict[str, list[str]]: Mapping of model names to their dependencies.

        Example:
            >>> graph = parser.build_dependency_graph()
            >>> graph.get("mrt_orders")
            ['stg_orders', 'stg_customers']

        """
        with open(self.manifest_path) as f:
            manifest = json.load(f)

        graph = {}
        for unique_id, node in manifest.get("nodes", {}).items():
            if not unique_id.startswith("model."):
                continue

            model_name = node.get("name")
            depends_on = []

            for dep_id in node.get("depends_on", {}).get("nodes", []):
                if dep_id.startswith("model."):
                    dep_name = dep_id.split(".")[-1]
                    depends_on.append(dep_name)

            graph[model_name] = depends_on

        return graph
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, list\[str]]: Mapping of model names to their dependencies.
  </PyFunctionReturn>
</PyFunction>
