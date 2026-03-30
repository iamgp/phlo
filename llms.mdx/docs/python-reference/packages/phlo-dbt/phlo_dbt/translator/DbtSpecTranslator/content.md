# DbtSpecTranslator (/docs/python-reference/packages/phlo-dbt/phlo_dbt/translator/DbtSpecTranslator)



Translate dbt manifest entries into orchestrator-agnostic spec fields.

This class converts dbt manifest node data into Phlo-compatible asset
specifications. It handles:

* Asset key generation (including special handling for sources)
* Description extraction with optional SQL inclusion
* Group name inference from paths and naming conventions
* Metadata extraction (columns, compiled SQL)
* Kind labeling

The translator uses dbt metadata like schema, path, and FQN to determine
appropriate groupings and follows dbt naming conventions (stg\_, dim\_, fct\_,
mrt\_) for layer detection.

Example:

> > > from phlo\_dbt.translator import DbtSpecTranslator
> > > translator = DbtSpecTranslator()
> > >
> > > node = \{
> > > ...     "name": "fct\_orders",
> > > ...     "resource\_type": "model",
> > > ...     "schema": "gold",
> > > ...     "description": "Orders fact table"
> > > ... }
> > >
> > > key = translator.get\_asset\_key(node)
> > > print(key)  # "fct\_orders"
> > >
> > > group = translator.get\_group\_name(node)
> > > print(group)  # "gold" (from schema)
> > >
> > > kinds = translator.get\_kinds(node)
> > > print(kinds)  # \{"dbt"}

Functions [#functions]

<PyFunction name="&#x22;get_asset_key&#x22;" type="&#x22;(self, dbt_resource_props) -> str&#x22;">
  Build the asset key for a dbt resource.

  <PySourceCode>
    ```python
    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> str:
        """Build the asset key for a dbt resource.

        Args:
            dbt_resource_props: dbt manifest resource dictionary.

        Returns:
            Canonical asset key string.

        """
        resource_type = dbt_resource_props.get("resource_type")
        is_source = resource_type == "source" or (
            resource_type is None and "source_name" in dbt_resource_props
        )

        if is_source:
            source_name = dbt_resource_props["source_name"]
            table_name = dbt_resource_props["name"]
            if source_name == "dagster_assets":
                return f"dlt_{table_name}"
            return f"{source_name}.{table_name}"

        return str(dbt_resource_props["name"])
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;dbt_resource_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
      dbt manifest resource dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Canonical asset key string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_description&#x22;" type="&#x22;(self, dbt_resource_props) -> str&#x22;">
  Build the asset description from dbt metadata.

  <PySourceCode>
    ````python
    def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
        """Build the asset description from dbt metadata.

        Args:
            dbt_resource_props: dbt manifest resource dictionary.

        Returns:
            Description text for the translated asset.

        """
        model_name = str(dbt_resource_props.get("name", ""))
        docstring = str(dbt_resource_props.get("description") or "")

        parts = [f"dbt model {model_name}"]
        if docstring:
            parts.append(docstring)

        if _bool_env("PHLO_DBT_INCLUDE_COMPILED_SQL_IN_DESCRIPTION", default=False):
            max_bytes = _int_env("PHLO_DBT_COMPILED_SQL_MAX_BYTES", default=64_000)
            compiled_sql, _, _, _ = get_compiled_sql_from_resource_props(
                dbt_resource_props, max_bytes=max_bytes
            )
            if compiled_sql:
                parts.append("\n#### Compiled SQL (truncated):\n\```sql\n" + compiled_sql + "\n\```")

        return "\n\n".join(parts)
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;dbt_resource_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
      dbt manifest resource dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Description text for the translated asset.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_group_name&#x22;" type="&#x22;(self, dbt_resource_props) -> str&#x22;">
  Infer the group name for a dbt resource.

  <PySourceCode>
    ```python
    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str:
        """Infer the group name for a dbt resource.

        Args:
            dbt_resource_props: dbt manifest resource dictionary.

        Returns:
            Group name used for asset organization.

        """
        meta = dbt_resource_props.get("meta", {})
        if isinstance(meta, dict) and "group" in meta:
            return str(meta["group"])

        path_layer = _first_matching_layer(_path_segments_from_props(dbt_resource_props))
        if path_layer is not None:
            return path_layer

        fqn_layer = _first_matching_layer(_fqn_segments_from_props(dbt_resource_props))
        if fqn_layer is not None:
            return fqn_layer

        model_name = str(dbt_resource_props.get("name", ""))
        if model_name.startswith("stg_"):
            return "silver"
        if model_name.startswith(("dim_", "fct_")):
            return "gold"
        if model_name.startswith("mrt_"):
            return "marts"
        return "transform"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;dbt_resource_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
      dbt manifest resource dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Group name used for asset organization.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_metadata&#x22;" type="&#x22;(self, dbt_resource_props) -> dict[str, Any]&#x22;">
  Build asset metadata from dbt manifest fields.

  <PySourceCode>
    ```python
    def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> dict[str, Any]:
        """Build asset metadata from dbt manifest fields.

        Args:
            dbt_resource_props: dbt manifest resource dictionary.

        Returns:
            Metadata dictionary for the translated asset.

        """
        metadata: dict[str, Any] = {}
        columns = dbt_resource_props.get("columns", {})
        if isinstance(columns, dict) and columns:
            table_columns = []
            for col_name, col_info in columns.items():
                if not isinstance(col_info, dict):
                    continue
                table_columns.append(
                    {
                        "name": str(col_name),
                        "type": str(col_info.get("data_type", "unknown")),
                        "description": str(col_info.get("description", "")),
                    }
                )
            if table_columns:
                metadata["phlo/column_schema"] = table_columns

        max_bytes = _int_env("PHLO_DBT_COMPILED_SQL_MAX_BYTES", default=64_000)
        compiled_sql, was_truncated, original_bytes, source = get_compiled_sql_from_resource_props(
            dbt_resource_props, max_bytes=max_bytes
        )
        if compiled_sql:
            metadata["phlo/compiled_sql"] = compiled_sql
            metadata["phlo/compiled_sql_truncated"] = was_truncated
            metadata["phlo/compiled_sql_bytes"] = original_bytes
            metadata["phlo/compiled_sql_byte_limit"] = max_bytes
            metadata["phlo/compiled_sql_source"] = source

        return metadata
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;dbt_resource_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
      dbt manifest resource dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Metadata dictionary for the translated asset.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_kinds&#x22;" type="&#x22;(self, dbt_resource_props) -> set[str]&#x22;">
  Return asset kinds for the dbt resource.

  <PySourceCode>
    ```python
    def get_kinds(self, dbt_resource_props: Mapping[str, Any]) -> set[str]:
        """Return asset kinds for the dbt resource.

        Args:
            dbt_resource_props: dbt manifest resource dictionary.

        Returns:
            Set of kind labels.

        """
        return {"dbt"}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;dbt_resource_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
      dbt manifest resource dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;set&#x22;">
    Set of kind labels.
  </PyFunctionReturn>
</PyFunction>
