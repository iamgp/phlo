# dbt_column_lineage (/docs/python-reference/packages/phlo-lineage/phlo_lineage/dbt_column_lineage)



Extract column-level lineage from dbt manifest.json.

This module implements heuristic-based extraction of column-level lineage from
dbt's manifest.json file. It uses same-name intersection heuristics rather than
full SQL parsing, making it lightweight but potentially less accurate than
parsing-based approaches.

Heuristic Method:
For each dbt model node:

1. Collect target columns from node\["columns"]
2. For each upstream dependency in depends\_on\["nodes"]:
   a. Collect upstream columns
   b. Create ColumnLineage for every column name appearing in both sets

Columns sharing a name across an edge are assumed to carry lineage.
This assumption holds for well-modeled dbt projects using consistent
naming conventions.

Source Type Tagging:
All mappings are tagged with source\_type="dbt\_heuristic" to signal that
they were derived via name matching rather than SQL analysis.

Limitations:

* Column renames are not detected (e.g., user\_id -> customer\_id)
* Derived columns (calculations, CASE statements) are not linked
* Column selection via \* is not expanded
* SQL-level transformations are opaque

Example:

> > > import json
> > > from phlo\_lineage.dbt\_column\_lineage import extract\_column\_lineage
> > >
> > > with open("target/manifest.json") as f:
> > > ...     manifest = json.load(f)
> > >
> > > mappings = extract\_column\_lineage(manifest)
> > > print(f"Found \{len(mappings)} column lineage mappings")
> > >
> > > for m in mappings\[:3]:
> > > ...     print(f"\{m.source\_column} in \{m.source\_asset} -> \{m.target\_column} in \{m.target\_asset}")

See Also:
phlo\_lineage.store.ColumnLineage for the data structure.
phlo\_lineage.store.LineageStore.record\_column\_lineage() for persistence.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_asset_name&#x22;" type="&#x22;(node) -> str&#x22;">
      Derive a qualified asset name from a dbt node dictionary.

      Constructs the fully qualified table/model name using the schema (database
      schema) and alias if available, falling back to the node name.

      <Callout title="&#x22;Resolution Order&#x22;" type="&#x22;resolution-order&#x22;">
        1. node\["schema"] + "." + node\["alias"]
        2. node\["schema"] + "." + node\["name"]
        3. node\["name"]
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > node = \{"schema": "silver", "alias": "stg\_orders", "name": "staging\_orders"}
        > > > \_resolve\_asset\_name(node)
        > > > 'silver.stg\_orders'
        > > >
        > > > node = \{"schema": "", "name": "raw\_orders"}
        > > > \_resolve\_asset\_name(node)
        > > > 'raw\_orders'
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        This is an internal helper function. It does not handle the case where
        schema is None (only empty string).
      </Callout>

      <PySourceCode>
        ```python
        def _resolve_asset_name(node: dict[str, Any]) -> str:
            """Derive a qualified asset name from a dbt node dictionary.

            Constructs the fully qualified table/model name using the schema (database
            schema) and alias if available, falling back to the node name.

            Args:
                node: dbt manifest node dictionary containing keys like schema, alias, name.

            Returns:
                Fully qualified asset name in "schema.name" format if schema is present,
                otherwise just the node name.

            Resolution Order:
                1. node["schema"] + "." + node["alias"]
                2. node["schema"] + "." + node["name"]
                3. node["name"]

            Example:
                >>> node = {"schema": "silver", "alias": "stg_orders", "name": "staging_orders"}
                >>> _resolve_asset_name(node)
                'silver.stg_orders'
                >>>
                >>> node = {"schema": "", "name": "raw_orders"}
                >>> _resolve_asset_name(node)
                'raw_orders'

            Note:
                This is an internal helper function. It does not handle the case where
                schema is None (only empty string).

            """
            schema = node.get("schema", "")
            name = node.get("alias") or node.get("name", "")
            return f"{schema}.{name}" if schema else name
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;node&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          dbt manifest node dictionary containing keys like schema, alias, name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Fully qualified asset name in "schema.name" format if schema is present,
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_get_node_columns&#x22;" type="&#x22;(node) -> set[str]&#x22;">
      Extract column names from a dbt node dictionary.

      Retrieves the set of column names defined in the node's "columns" property.
      This typically includes columns explicitly documented in the model's
      YAML schema or inferred from the model SQL.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > node = \{
        > > > ...     "columns": \{
        > > > ...         "order\_id": \{"type": "int"},
        > > > ...         "customer\_id": \{"type": "int"},
        > > > ...     }
        > > > ... }
        > > > \_get\_node\_columns(node)
        > > > \{'order\_id', 'customer\_id'}
        > > >
        > > > node = \{"name": "orphan\_model"}
        > > > \_get\_node\_columns(node)
        > > > set()
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        This is an internal helper function. Column types and descriptions
        are ignored; only names are extracted.
      </Callout>

      <PySourceCode>
        ```python
        def _get_node_columns(node: dict[str, Any]) -> set[str]:
            """Extract column names from a dbt node dictionary.

            Retrieves the set of column names defined in the node's "columns" property.
            This typically includes columns explicitly documented in the model's
            YAML schema or inferred from the model SQL.

            Args:
                node: dbt manifest node dictionary containing a "columns" key.

            Returns:
                Set of column name strings. Empty set if node has no columns defined.

            Example:
                >>> node = {
                ...     "columns": {
                ...         "order_id": {"type": "int"},
                ...         "customer_id": {"type": "int"},
                ...     }
                ... }
                >>> _get_node_columns(node)
                {'order_id', 'customer_id'}
                >>>
                >>> node = {"name": "orphan_model"}
                >>> _get_node_columns(node)
                set()

            Note:
                This is an internal helper function. Column types and descriptions
                are ignored; only names are extracted.

            """
            columns: dict[str, Any] = node.get("columns", {})
            return set(columns.keys())
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;node&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          dbt manifest node dictionary containing a "columns" key.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;set&#x22;">
        Set of column name strings. Empty set if node has no columns defined.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;extract_column_lineage&#x22;" type="&#x22;(manifest) -> list[ColumnLineage]&#x22;">
      Extract column lineage from a dbt manifest using same-name heuristics.

      Processes all model nodes in the manifest and creates ColumnLineage
      mappings for columns that share names across dependency edges.

      <Callout title="&#x22;Algorithm&#x22;" type="&#x22;algorithm&#x22;">
        1. Filter manifest\["nodes"] to include only resource\_type="model"
        2. For each model node:
           a. Determine target\_asset from schema + alias/name
           b. Collect target\_columns from node\["columns"]
           c. Skip if no columns defined
           d. For each upstream in depends\_on\["nodes"]:
           * Resolve source\_asset from upstream node
           * Collect source\_columns
           * Compute intersection (shared column names)
           * Create ColumnLineage for each shared column
        3. Return all mappings with source\_type="dbt\_heuristic"
      </Callout>

      <Callout title="&#x22;Logging&#x22;" type="&#x22;logging&#x22;">
        Logs INFO at start with model\_count and at completion with mapping\_count.
        Logs DEBUG for models with no columns.
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > import json
        > > > from phlo\_lineage.dbt\_column\_lineage import extract\_column\_lineage
        > > >
        > > > with open("target/manifest.json") as f:
        > > > ...     manifest = json.load(f)
        > > >
        > > > mappings = extract\_column\_lineage(manifest)
        > > > print(f"Extracted \{len(mappings)} column mappings")
        > > >
        > > > Persist to store [#persist-to-store]
        > > >
        > > > from phlo\_lineage import LineageStore
        > > > store = LineageStore("postgresql://...")
        > > > store.record\_column\_lineage(mappings)
      </Callout>

      <Callout title="&#x22;Limitations&#x22;" type="&#x22;limitations&#x22;">
        This heuristic approach has known limitations:

        * Column renames across models are not detected
        * Calculated/derived columns have no upstream lineage
        * SELECT \* is not expanded to individual columns
        * Common columns (id, name, created\_at) may produce false positives
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        [https://docs.getdbt.com/reference/artifacts/manifest-json](https://docs.getdbt.com/reference/artifacts/manifest-json)
      </Callout>

      <PySourceCode>
        ```python
        def extract_column_lineage(manifest: dict[str, Any]) -> list[ColumnLineage]:
            """Extract column lineage from a dbt manifest using same-name heuristics.

            Processes all model nodes in the manifest and creates ColumnLineage
            mappings for columns that share names across dependency edges.

            Algorithm:
                1. Filter manifest["nodes"] to include only resource_type="model"
                2. For each model node:
                   a. Determine target_asset from schema + alias/name
                   b. Collect target_columns from node["columns"]
                   c. Skip if no columns defined
                   d. For each upstream in depends_on["nodes"]:
                      - Resolve source_asset from upstream node
                      - Collect source_columns
                      - Compute intersection (shared column names)
                      - Create ColumnLineage for each shared column
                3. Return all mappings with source_type="dbt_heuristic"

            Args:
                manifest: Parsed dbt manifest.json as a dictionary. Must contain
                    a "nodes" key with model node dictionaries.

            Returns:
                List of ColumnLineage dataclass instances representing inferred
                column-level relationships. May be empty if no models have columns
                defined or no dependencies exist.

            Logging:
                Logs INFO at start with model_count and at completion with mapping_count.
                Logs DEBUG for models with no columns.

            Example:
                >>> import json
                >>> from phlo_lineage.dbt_column_lineage import extract_column_lineage
                >>>
                >>> with open("target/manifest.json") as f:
                ...     manifest = json.load(f)
                >>>
                >>> mappings = extract_column_lineage(manifest)
                >>> print(f"Extracted {len(mappings)} column mappings")
                >>>
                >>> # Persist to store
                >>> from phlo_lineage import LineageStore
                >>> store = LineageStore("postgresql://...")
                >>> store.record_column_lineage(mappings)

            Limitations:
                This heuristic approach has known limitations:
                - Column renames across models are not detected
                - Calculated/derived columns have no upstream lineage
                - SELECT * is not expanded to individual columns
                - Common columns (id, name, created_at) may produce false positives

            See Also:
                https://docs.getdbt.com/reference/artifacts/manifest-json

            """
            nodes: dict[str, Any] = manifest.get("nodes", {})
            mappings: list[ColumnLineage] = []

            model_nodes = {key: node for key, node in nodes.items() if node.get("resource_type") == "model"}

            logger.info(
                "column_lineage_extraction_started",
                model_count=len(model_nodes),
            )

            for node_key, node in model_nodes.items():
                target_asset = _resolve_asset_name(node)
                target_columns = _get_node_columns(node)

                if not target_columns:
                    logger.debug(
                        "column_lineage_no_columns",
                        node_key=node_key,
                        target_asset=target_asset,
                    )
                    continue

                upstream_keys: list[str] = node.get("depends_on", {}).get("nodes", [])

                for upstream_key in upstream_keys:
                    upstream_node = nodes.get(upstream_key)
                    if upstream_node is None:
                        continue

                    source_asset = _resolve_asset_name(upstream_node)
                    source_columns = _get_node_columns(upstream_node)

                    shared = target_columns & source_columns
                    for col in sorted(shared):
                        mappings.append(
                            ColumnLineage(
                                source_asset=source_asset,
                                source_column=col,
                                target_asset=target_asset,
                                target_column=col,
                                source_type="dbt_heuristic",
                            )
                        )

            logger.info(
                "column_lineage_extraction_completed",
                mapping_count=len(mappings),
            )
            return mappings
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;manifest&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Parsed dbt manifest.json as a dictionary. Must contain
          a "nodes" key with model node dictionaries.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of ColumnLineage dataclass instances representing inferred
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
