# DbtManifestParser (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/dbt_sync/DbtManifestParser)



Parses dbt manifest.json for metadata extraction.

Extracts model descriptions, column-level documentation, tests,
and freshness policies for syncing to OpenMetadata.

Attributes [#attributes]

<PyAttribute name="&#x22;manifest_path&#x22;" type="null" value="&#x22;Path(manifest_path)&#x22;">
  Path to dbt manifest.json file.
</PyAttribute>

<PyAttribute name="&#x22;catalog_path&#x22;" type="null" value="&#x22;Path(catalog_path) if catalog_path else None&#x22;">
  Path to dbt catalog.json file (optional).
</PyAttribute>

<PyAttribute name="&#x22;manifest&#x22;" type="null" value="&#x22;None&#x22;">
  Cached manifest dictionary.
</PyAttribute>

<PyAttribute name="&#x22;catalog&#x22;" type="null" value="&#x22;None&#x22;">
  Cached catalog dictionary.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, manifest_path, catalog_path=None)&#x22;">
  Initialize dbt manifest parser.

  <PySourceCode>
    ```python
    def __init__(self, manifest_path: str, catalog_path: Optional[str] = None):
        """Initialize dbt manifest parser.

        Args:
            manifest_path: Path to dbt manifest.json.
            catalog_path: Path to dbt catalog.json (optional, for column docs).

        """
        self.manifest_path = Path(manifest_path)
        self.catalog_path = Path(catalog_path) if catalog_path else None
        self.manifest = None
        self.catalog = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;manifest_path&#x22;" type="&#x22;str&#x22;" value="undefined">
      Path to dbt manifest.json.
    </PyParameter>

    <PyParameter name="&#x22;catalog_path&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Path to dbt catalog.json (optional, for column docs).
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;from_settings&#x22;" type="&#x22;(cls, settings) -> 'DbtManifestParser'&#x22;">
  Create parser from OpenMetadata-owned config.

  <PySourceCode>
    ```python
    @classmethod
    def from_settings(cls, settings: OpenMetadataSettings) -> "DbtManifestParser":
        """Create parser from OpenMetadata-owned config.

        Args:
            settings: OpenMetadataSettings instance with configured paths.

        Returns:
            DbtManifestParser: Initialized parser using settings paths.

        """
        return cls(
            manifest_path=settings.openmetadata_dbt_manifest_path,
            catalog_path=settings.openmetadata_dbt_catalog_path,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;settings&#x22;" type="&#x22;OpenMetadataSettings&#x22;" value="undefined">
      OpenMetadataSettings instance with configured paths.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;'DbtManifestParser'&#x22;">
    Initialized parser using settings paths.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;load_manifest&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Load and parse dbt manifest.json.

  <PySourceCode>
    ```python
    def load_manifest(self) -> dict[str, Any]:
        """Load and parse dbt manifest.json.

        Returns:
            dict[str, Any]: Parsed manifest dictionary.

        Raises:
            FileNotFoundError: If manifest file not found.
            json.JSONDecodeError: If manifest is invalid JSON.

        """
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"dbt manifest not found: {self.manifest_path}")

        try:
            with open(self.manifest_path) as f:
                self.manifest = json.load(f)
            logger.info("dbt_manifest_loaded", manifest_path=str(self.manifest_path))
            return self.manifest
        except json.JSONDecodeError as exc:
            logger.error(
                "dbt_manifest_invalid_json",
                manifest_path=str(self.manifest_path),
                error=str(exc),
            )
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Parsed manifest dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;load_catalog&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Load and parse dbt catalog.json for column documentation.

  <PySourceCode>
    ```python
    def load_catalog(self) -> dict[str, Any]:
        """Load and parse dbt catalog.json for column documentation.

        Returns:
            dict[str, Any]: Parsed catalog dictionary, or empty dict if not found.

        Raises:
            json.JSONDecodeError: If catalog is invalid JSON.

        """
        if not self.catalog_path or not self.catalog_path.exists():
            logger.warning(
                "dbt_catalog_missing",
                catalog_path=str(self.catalog_path),
                impact="column_level_docs_unavailable",
            )
            return {}

        try:
            with open(self.catalog_path) as f:
                self.catalog = json.load(f)
            logger.info("dbt_catalog_loaded", catalog_path=str(self.catalog_path))
            return self.catalog
        except json.JSONDecodeError as exc:
            logger.error(
                "dbt_catalog_invalid_json",
                catalog_path=str(self.catalog_path),
                error=str(exc),
            )
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Parsed catalog dictionary, or empty dict if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_models&#x22;" type="&#x22;(self, manifest=None) -> dict[str, dict[str, Any]]&#x22;">
  Extract all models from manifest.

  <PySourceCode>
    ```python
    def get_models(self, manifest: Optional[dict[str, Any]] = None) -> dict[str, dict[str, Any]]:
        """Extract all models from manifest.

        Args:
            manifest: Parsed manifest dict (uses loaded manifest if not provided).

        Returns:
            dict[str, dict[str, Any]]: Dictionary mapping model unique_id to model metadata.

        """
        if manifest is None:
            manifest = self.manifest or self.load_manifest()

        models = {}
        for unique_id, model in manifest.get("nodes", {}).items():
            if unique_id.startswith("model."):
                models[unique_id] = model
                logger.debug("dbt_model_found", model_name=model.get("name"), unique_id=unique_id)

        return models
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;manifest&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Parsed manifest dict (uses loaded manifest if not provided).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, dict\[str, Any]]: Dictionary mapping model unique\_id to model metadata.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_model_columns&#x22;" type="&#x22;(self, model_name, schema_name, catalog=None) -> dict[str, dict[str, Any]]&#x22;">
  Get column information for a model from catalog.json.

  <PySourceCode>
    ```python
    def get_model_columns(
        self,
        model_name: str,
        schema_name: str,
        catalog: Optional[dict[str, Any]] = None,
    ) -> dict[str, dict[str, Any]]:
        """Get column information for a model from catalog.json.

        Args:
            model_name: Model name.
            schema_name: Schema name.
            catalog: Parsed catalog dict (uses loaded catalog if not provided).

        Returns:
            dict[str, dict[str, Any]]: Dictionary mapping column name to column metadata.

        """
        if catalog is None:
            catalog = self.catalog or self.load_catalog()

        if not catalog:
            return {}

        def normalize_columns(columns: Any) -> dict[str, dict[str, Any]]:
            """Normalize catalog column payloads into a name-keyed mapping.

            Args:
                columns: Catalog column payload.

            Returns:
                dict[str, dict[str, Any]]: Mapping of column name to column metadata.

            """
            if isinstance(columns, dict):
                return columns
            if isinstance(columns, list):
                normalized: dict[str, dict[str, Any]] = {}
                for entry in columns:
                    if not isinstance(entry, dict):
                        continue
                    name = entry.get("name")
                    if isinstance(name, str) and name:
                        normalized[name] = entry
                return normalized
            return {}

        if isinstance(catalog.get("nodes"), dict):
            nodes: dict[str, Any] = catalog.get("nodes", {})
            for node in nodes.values():
                if not isinstance(node, dict):
                    continue
                metadata = node.get("metadata") or {}
                if not isinstance(metadata, dict):
                    continue
                if metadata.get("name") != model_name or metadata.get("schema") != schema_name:
                    continue
                return normalize_columns(node.get("columns"))

            return {}

        key = f"{schema_name}.{model_name}"
        model_entry = catalog.get(key, {})
        return (
            normalize_columns(model_entry.get("columns")) if isinstance(model_entry, dict) else {}
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;model_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Model name.
    </PyParameter>

    <PyParameter name="&#x22;schema_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name.
    </PyParameter>

    <PyParameter name="&#x22;catalog&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Parsed catalog dict (uses loaded catalog if not provided).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, dict\[str, Any]]: Dictionary mapping column name to column metadata.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_model_tests&#x22;" type="&#x22;(self, model_unique_id, manifest=None) -> list[dict[str, Any]]&#x22;">
  Extract tests associated with a model.

  <PySourceCode>
    ```python
    def get_model_tests(
        self,
        model_unique_id: str,
        manifest: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Extract tests associated with a model.

        Args:
            model_unique_id: Model unique_id (e.g., model.project.table).
            manifest: Parsed manifest dict.

        Returns:
            list[dict[str, Any]]: List of test metadata dicts.

        """
        if manifest is None:
            manifest = self.manifest or self.load_manifest()

        tests = []
        for unique_id, node in manifest.get("nodes", {}).items():
            if unique_id.startswith("test.") and "test_metadata" in node:
                depends = node.get("depends_on", {}).get("nodes", [])
                if model_unique_id in depends:
                    tests.append(node)
        return tests
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;model_unique_id&#x22;" type="&#x22;str&#x22;" value="undefined">
      Model unique\_id (e.g., model.project.table).
    </PyParameter>

    <PyParameter name="&#x22;manifest&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Parsed manifest dict.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict\[str, Any]]: List of test metadata dicts.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;extract_openmetadata_table&#x22;" type="&#x22;(self, model, schema_name, columns_info=None) -> OpenMetadataTable&#x22;">
  Convert dbt model metadata to OpenMetadataTable format.

  <PySourceCode>
    ```python
    def extract_openmetadata_table(
        self,
        model: dict[str, Any],
        schema_name: str,
        columns_info: Optional[dict[str, Any]] = None,
    ) -> OpenMetadataTable:
        """Convert dbt model metadata to OpenMetadataTable format.

        Args:
            model: dbt model metadata.
            schema_name: Schema name.
            columns_info: Optional column info from catalog.json.

        Returns:
            OpenMetadataTable: OpenMetadata table object.

        """
        name = model.get("name", "unknown")
        description = model.get("description")

        columns = []
        model_columns = model.get("columns", {}) or {}

        for idx, (col_name, col_meta) in enumerate(model_columns.items()):
            col_desc = col_meta.get("description")
            data_type = "UNKNOWN"

            if columns_info and col_name in columns_info:
                data_type = columns_info[col_name].get("type", "UNKNOWN")

            columns.append(
                OpenMetadataColumn(
                    name=col_name,
                    description=col_desc,
                    dataType=data_type,
                    ordinalPosition=idx,
                )
            )

        tags = []
        for tag in model.get("tags", []) or []:
            tags.append({"name": tag})

        freshness = model.get("freshness")
        if freshness and isinstance(freshness, dict):
            warn_after = freshness.get("warn_after", {})
            if isinstance(warn_after, dict):
                count = warn_after.get("count")
                period = warn_after.get("period")
                if count and period:
                    tags.append({"name": f"freshness_warn_after_{count}_{period}"})

        return OpenMetadataTable(
            name=name,
            description=description,
            columns=columns if columns else None,
            tags=tags if tags else None,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;model&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      dbt model metadata.
    </PyParameter>

    <PyParameter name="&#x22;schema_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name.
    </PyParameter>

    <PyParameter name="&#x22;columns_info&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Optional column info from catalog.json.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_openmetadata.openmetadata.OpenMetadataTable&#x22;">
    OpenMetadata table object.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;sync_to_openmetadata&#x22;" type="&#x22;(self, om_client, schema_name, model_filter=None) -> dict[str, int]&#x22;">
  Sync dbt models to OpenMetadata.

  <PySourceCode>
    ```python
    def sync_to_openmetadata(
        self,
        om_client: Any,  # OpenMetadataClient
        schema_name: str,
        model_filter: Optional[list[str]] = None,
    ) -> dict[str, int]:
        """Sync dbt models to OpenMetadata.

        Args:
            om_client: OpenMetadataClient instance.
            schema_name: Target OpenMetadata schema name.
            model_filter: Optional list of dbt model names to sync.

        Returns:
            dict[str, int]: Stats dict with created/failed counts.

        """
        stats = {"created": 0, "failed": 0}

        manifest = self.load_manifest()
        catalog = self.load_catalog()

        models = self.get_models(manifest)
        for unique_id, model in models.items():
            model_name = model.get("name")
            if model_filter and model_name not in model_filter:
                continue

            try:
                columns_info = self.get_model_columns(model_name, schema_name, catalog)
                om_table = self.extract_openmetadata_table(model, schema_name, columns_info)
                om_client.create_or_update_table(schema_name, om_table)
                stats["created"] += 1
            except Exception as exc:
                logger.error(
                    "dbt_model_sync_failed",
                    model_name=model_name,
                    unique_id=unique_id,
                    error=str(exc),
                )
                stats["failed"] += 1

        return stats
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;om_client&#x22;" type="&#x22;Any&#x22;" value="undefined">
      OpenMetadataClient instance.
    </PyParameter>

    <PyParameter name="&#x22;schema_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Target OpenMetadata schema name.
    </PyParameter>

    <PyParameter name="&#x22;model_filter&#x22;" type="&#x22;Optional[list[str]]&#x22;" value="&#x22;None&#x22;">
      Optional list of dbt model names to sync.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Stats dict with created/failed counts.
  </PyFunctionReturn>
</PyFunction>
