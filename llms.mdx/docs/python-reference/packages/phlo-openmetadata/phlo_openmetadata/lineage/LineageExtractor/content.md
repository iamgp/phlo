# LineageExtractor (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/lineage/LineageExtractor)



Extracts lineage from various sources (Dagster, dbt, Iceberg).

Builds a unified lineage graph and publishes to OpenMetadata.

Attributes [#attributes]

<PyAttribute name="&#x22;graph&#x22;" type="null" value="&#x22;OpenMetadataLineageGraph()&#x22;">
  OpenMetadataLineageGraph storing extracted lineage.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self)&#x22;">
  Initialize lineage extractor.

  Creates a new OpenMetadataLineageGraph instance for tracking
  lineage between assets.

  <PySourceCode>
    ```python
    def __init__(self):
        """Initialize lineage extractor.

        Creates a new OpenMetadataLineageGraph instance for tracking
        lineage between assets.
        """
        from phlo_openmetadata.graph import OpenMetadataLineageGraph

        self.graph = OpenMetadataLineageGraph()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;extract_from_dagster&#x22;" type="&#x22;(self, context) -> None&#x22;">
  Extract lineage from Dagster context.

  <PySourceCode>
    ```python
    @log_extraction_errors("Dagster")
    def extract_from_dagster(self, context: Any) -> None:
        """Extract lineage from Dagster context.

        Args:
            context: Dagster context with run and asset information.

        Returns:
            None

        """
        if not hasattr(context, "get_asset_materialization_events"):
            logger.warning(
                "Unsupported Dagster execution context for lineage extraction. "
                "Expected an ExecuteInProcessResult-like object with "
                "get_asset_materialization_events()."
            )
            return

        events = context.get_asset_materialization_events()
        if not isinstance(events, list):
            logger.warning(
                "dagster_materialization_events_invalid_type",
                events_type=type(events).__name__,
            )
            return

        for event in events:
            asset_key = getattr(event, "asset_key", None)
            if asset_key is None:
                continue
            if hasattr(asset_key, "path") and asset_key.path:
                asset_name = asset_key.path[-1]
            else:
                asset_name = str(asset_key)
            self.graph.add_asset(asset_name, asset_type="unknown")

        logger.info(
            "dagster_lineage_assets_extracted",
            asset_count=len(self.graph.assets),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Dagster context with run and asset information.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;extract_from_dbt_manifest&#x22;" type="&#x22;(self, manifest) -> None&#x22;">
  Extract lineage from dbt manifest.json.

  <PySourceCode>
    ```python
    @log_extraction_errors("dbt")
    def extract_from_dbt_manifest(self, manifest: dict[str, Any]) -> None:
        """Extract lineage from dbt manifest.json.

        Args:
            manifest: Parsed dbt manifest dictionary.

        Returns:
            None

        """
        for unique_id, node in manifest.get("nodes", {}).items():
            if unique_id.startswith("model."):
                model_name = node.get("name")
                if not model_name:
                    logger.warning("dbt_model_name_missing", unique_id=unique_id)
                    continue
                self.graph.add_asset(
                    model_name,
                    asset_type="transform",
                    status="unknown",
                )

        for unique_id, source in manifest.get("sources", {}).items():
            src_name_part = source.get("source_name") or ""
            tbl_name_part = source.get("name") or ""
            source_name = f"{src_name_part}.{tbl_name_part}".strip(".")
            if not source_name:
                logger.warning("dbt_source_name_missing", unique_id=unique_id)
                continue
            self.graph.add_asset(
                source_name,
                asset_type="ingestion",
                status="unknown",
            )

        nodes = manifest.get("nodes", {})
        sources = manifest.get("sources", {})

        for unique_id, node in nodes.items():
            if unique_id.startswith("model."):
                model_name = node.get("name")
                if not model_name:
                    logger.warning("dbt_model_name_missing", unique_id=unique_id)
                    continue

                for dep_id in node.get("depends_on", {}).get("nodes", []):
                    if dep_id.startswith("model."):
                        dep_node = nodes.get(dep_id)
                        if dep_node is None:
                            logger.warning("dbt_dependency_node_missing", dependency_id=dep_id)
                            continue
                        dep_name = dep_node.get("name")
                        if dep_name:
                            self.graph.add_edge(dep_name, model_name)
                    elif dep_id.startswith("source."):
                        source = sources.get(dep_id)
                        if source is None:
                            logger.warning("dbt_source_node_missing", source_id=dep_id)
                            continue
                        src_name_part = source.get("source_name") or ""
                        tbl_name_part = source.get("name") or ""
                        source_name = f"{src_name_part}.{tbl_name_part}".strip(".")
                        if source_name:
                            self.graph.add_edge(source_name, model_name)

        logger.info(
            "dbt_lineage_extracted",
            asset_count=len(self.graph.assets),
            edge_count=sum(len(v) for v in self.graph.edges.values()),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;manifest&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Parsed dbt manifest dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;extract_from_iceberg&#x22;" type="&#x22;(self, nessie_tables) -> None&#x22;">
  Add Iceberg tables to lineage graph.

  <PySourceCode>
    ```python
    @log_extraction_errors("Iceberg")
    def extract_from_iceberg(
        self,
        nessie_tables: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Add Iceberg tables to lineage graph.

        Args:
            nessie_tables: Dictionary of namespace -> tables from Nessie.

        Returns:
            None

        """
        for namespace, tables in nessie_tables.items():
            for table in tables:
                table_name = table.get("name")
                if not table_name:
                    logger.debug(
                        "iceberg_table_name_missing",
                        namespace=namespace,
                    )
                    continue
                full_name = f"{namespace}.{table_name}"

                self.graph.add_asset(
                    full_name,
                    asset_type="ingestion",
                    status="unknown",
                )

        logger.info("iceberg_tables_extracted", table_count=len(self.graph.assets))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;nessie_tables&#x22;" type="&#x22;dict[str, list[dict[str, Any]]]&#x22;" value="undefined">
      Dictionary of namespace -> tables from Nessie.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;build_publishing_lineage&#x22;" type="&#x22;(self, manifest, postgres_schema) -> dict[str, list[str]]&#x22;">
  Build source -> published tables mapping.

  Identifies dbt models in `postgres_schema` as "published" tables, then returns
  which of those tables are downstream of each ingestion source.

  <PySourceCode>
    ```python
    def build_publishing_lineage(
        self,
        manifest: dict[str, Any],
        postgres_schema: str,
    ) -> dict[str, list[str]]:
        """Build source -> published tables mapping.

        Identifies dbt models in `postgres_schema` as "published" tables, then returns
        which of those tables are downstream of each ingestion source.

        Args:
            manifest: Parsed dbt manifest dictionary.
            postgres_schema: Schema name identifying published models.

        Returns:
            dict[str, list[str]]: Dictionary mapping source FQN to list of
                published downstream tables.

        """
        published_models: set[str] = set()
        for unique_id, node in manifest.get("nodes", {}).items():
            if not unique_id.startswith("model."):
                continue
            if node.get("schema") == postgres_schema and node.get("name"):
                published_models.add(node["name"])

        if not published_models:
            return {}

        lineage: dict[str, list[str]] = {}
        for _unique_id, source in manifest.get("sources", {}).items():
            source_fqn = f"{source.get('source_name')}.{source.get('name')}"
            downstream = self.graph.get_downstream(source_fqn)
            published_downstream = sorted(a for a in downstream if a in published_models)
            if published_downstream:
                lineage[source_fqn] = published_downstream

        return lineage
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;manifest&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Parsed dbt manifest dictionary.
    </PyParameter>

    <PyParameter name="&#x22;postgres_schema&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name identifying published models.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, list\[str]]: Dictionary mapping source FQN to list of
    published downstream tables.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;publish_to_openmetadata&#x22;" type="&#x22;(self, om_client, include_edges=True) -> dict[str, int]&#x22;">
  Publish lineage graph to OpenMetadata.

  <PySourceCode>
    ```python
    def publish_to_openmetadata(
        self,
        om_client: Any,  # OpenMetadataClient
        include_edges: bool = True,
    ) -> dict[str, int]:
        """Publish lineage graph to OpenMetadata.

        Args:
            om_client: OpenMetadataClient instance.
            include_edges: Whether to publish edges (default True).

        Returns:
            dict[str, int]: Publication statistics with 'edges_published'
                and 'failed' counts.

        """
        stats = {"edges_published": 0, "failed": 0}

        if not include_edges:
            return stats

        try:
            for from_asset, to_assets in self.graph.edges.items():
                for to_asset in to_assets:
                    try:
                        om_client.create_lineage(from_asset, to_asset)
                        stats["edges_published"] += 1
                    except Exception as exc:
                        logger.error(
                            "lineage_edge_publish_failed",
                            from_asset=from_asset,
                            to_asset=to_asset,
                            error=str(exc),
                        )
                        stats["failed"] += 1

            logger.info(
                "lineage_publish_completed",
                edges_published=stats["edges_published"],
            )

        except Exception as exc:
            logger.error("lineage_publish_failed", error=str(exc))
            stats["failed"] += 1

        return stats
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;om_client&#x22;" type="&#x22;Any&#x22;" value="undefined">
      OpenMetadataClient instance.
    </PyParameter>

    <PyParameter name="&#x22;include_edges&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether to publish edges (default True).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, int]: Publication statistics with 'edges\_published'
    and 'failed' counts.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_impact_analysis&#x22;" type="&#x22;(self, asset_name) -> dict[str, Any]&#x22;">
  Return downstream impact analysis for an asset.

  <PySourceCode>
    ```python
    def get_impact_analysis(self, asset_name: str) -> dict[str, Any]:
        """Return downstream impact analysis for an asset.

        Args:
            asset_name: Name of the asset to analyze.

        Returns:
            dict[str, Any]: Dictionary with 'affected_assets' list
                and 'total_affected' count.

        """
        affected = sorted(self.graph.get_downstream(asset_name))
        return {"affected_assets": affected, "total_affected": len(affected)}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the asset to analyze.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Dictionary with 'affected\_assets' list
    and 'total\_affected' count.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;export_lineage&#x22;" type="&#x22;(self, format_type='json') -> str&#x22;">
  Export lineage graph in a supported format.

  <PySourceCode>
    ```python
    def export_lineage(self, format_type: str = "json") -> str:
        """Export lineage graph in a supported format.

        Args:
            format_type: Export format - 'json', 'dot', or 'mermaid'.

        Returns:
            str: Formatted lineage graph string.

        Raises:
            ValueError: If format_type is not supported.

        """
        if format_type == "json":
            return self.graph.to_json()
        if format_type == "dot":
            return self.graph.to_dot()
        if format_type == "mermaid":
            return self.graph.to_mermaid()
        raise ValueError(f"Unsupported format: {format_type}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;format_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'json'&#x22;">
      Export format - 'json', 'dot', or 'mermaid'.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Formatted lineage graph string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_normalize_fqn&#x22;" type="&#x22;(fqn) -> str&#x22;">
  Normalize unqualified table names to `default.\<name>`.

  <PySourceCode>
    ```python
    @staticmethod
    def _normalize_fqn(fqn: str) -> str:
        """Normalize unqualified table names to `default.<name>`.

        Args:
            fqn: Table name that may or may not include schema prefix.

        Returns:
            str: Fully qualified name with 'default.' prefix if needed.

        """
        return fqn if "." in fqn else f"default.{fqn}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table name that may or may not include schema prefix.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Fully qualified name with 'default.' prefix if needed.
  </PyFunctionReturn>
</PyFunction>
