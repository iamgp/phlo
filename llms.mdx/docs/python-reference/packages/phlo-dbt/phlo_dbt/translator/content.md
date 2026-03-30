# translator (/docs/python-reference/packages/phlo-dbt/phlo_dbt/translator)



Translate dbt manifest entries into Phlo asset specifications.

This module provides the DbtSpecTranslator class which bridges dbt's manifest
format with Phlo's asset specification system. It handles conversion of dbt
metadata including asset keys, descriptions, group names, and SQL compilation.

Example:

> > > from phlo\_dbt.translator import DbtSpecTranslator
> > > import json
> > >
> > > translator = DbtSpecTranslator()
> > >
> > > Load manifest node [#load-manifest-node]
> > >
> > > manifest = json.loads(Path("target/manifest.json").read\_text())
> > > node = manifest\["nodes"]\["model.my\_project.fct\_orders"]
> > >
> > > Translate to Phlo specs [#translate-to-phlo-specs]
> > >
> > > asset\_key = translator.get\_asset\_key(node)
> > > description = translator.get\_description(node)
> > > group = translator.get\_group\_name(node)
> > > metadata = translator.get\_metadata(node)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DbtSpecTranslator&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/translator/DbtSpecTranslator&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_bool_env&#x22;" type="&#x22;(name, default=False) -> bool&#x22;">
      <PySourceCode>
        ```python
        def _bool_env(name: str, default: bool = False) -> bool:
            value = os.getenv(name)
            if value is None:
                return default
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;default&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_int_env&#x22;" type="&#x22;(name, default) -> int&#x22;">
      <PySourceCode>
        ```python
        def _int_env(name: str, default: int) -> int:
            value = os.getenv(name)
            if value is None:
                return default
            try:
                return int(value)
            except ValueError:
                logger.warning(
                    "dbt_translator_env_int_invalid",
                    env_var=name,
                    env_value=value,
                    fallback_default=default,
                )
                return default
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;default&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_first_matching_layer&#x22;" type="&#x22;(segments) -> str | None&#x22;">
      <PySourceCode>
        ```python
        def _first_matching_layer(segments: Sequence[str]) -> str | None:
            layer_map = {
                "bronze": "bronze",
                "silver": "silver",
                "gold": "gold",
                "marts": "marts",
                "mart": "marts",
                "staging": "silver",
                "stage": "silver",
                "stg": "silver",
            }

            for segment in segments:
                layer = layer_map.get(segment)
                if layer is not None:
                    return layer
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;segments&#x22;" type="&#x22;Sequence[str]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_path_segments_from_props&#x22;" type="&#x22;(dbt_resource_props) -> list[str]&#x22;">
      <PySourceCode>
        ```python
        def _path_segments_from_props(dbt_resource_props: Mapping[str, Any]) -> list[str]:
            path = str(dbt_resource_props.get("path") or dbt_resource_props.get("original_file_path") or "")
            if not path:
                return []

            normalized = path.replace("\\", "/")
            return [segment for segment in PurePosixPath(normalized).parts if segment not in {".", ""}]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dbt_resource_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_fqn_segments_from_props&#x22;" type="&#x22;(dbt_resource_props) -> list[str]&#x22;">
      <PySourceCode>
        ```python
        def _fqn_segments_from_props(dbt_resource_props: Mapping[str, Any]) -> list[str]:
            fqn = dbt_resource_props.get("fqn")
            if not isinstance(fqn, list):
                return []
            return [str(segment) for segment in fqn]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dbt_resource_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_truncate_utf8_bytes&#x22;" type="&#x22;(text, max_bytes) -> tuple[str, bool, int]&#x22;">
      <PySourceCode>
        ```python
        def _truncate_utf8_bytes(text: str, max_bytes: int) -> tuple[str, bool, int]:
            raw = text.encode("utf-8")
            if len(raw) <= max_bytes:
                return text, False, len(raw)

            truncated = raw[:max_bytes].decode("utf-8", errors="ignore")
            return truncated, True, len(raw)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;text&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;max_bytes&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[str, bool, int]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_compiled_sql_from_resource_props&#x22;" type="&#x22;(dbt_resource_props, *, max_bytes) -> tuple[str, bool, int, str]&#x22;">
      Resolve compiled SQL from dbt resource properties.

      <PySourceCode>
        ```python
        def get_compiled_sql_from_resource_props(
            dbt_resource_props: Mapping[str, Any], *, max_bytes: int
        ) -> tuple[str, bool, int, str]:
            """Resolve compiled SQL from dbt resource properties.

            Args:
                dbt_resource_props: dbt manifest resource dictionary.
                max_bytes: Maximum number of UTF-8 bytes to keep in SQL text.

            Returns:
                A tuple of compiled SQL text, truncation flag, original byte length,
                and SQL source indicator.

            """
            compiled_sql = ""
            source = "none"

            compiled_path = dbt_resource_props.get("compiled_path")
            if compiled_path:
                compiled_file = get_settings().dbt_project_path / str(compiled_path)
                try:
                    if compiled_file.exists():
                        compiled_sql = compiled_file.read_text()
                        source = "compiled_file"
                except OSError:
                    logger.warning(
                        "dbt_translator_compiled_sql_read_failed",
                        compiled_file=str(compiled_file),
                    )

            if not compiled_sql:
                compiled_sql = str(
                    dbt_resource_props.get("compiled_code")
                    or dbt_resource_props.get("raw_code")
                    or dbt_resource_props.get("raw_sql")
                    or ""
                )
                if compiled_sql:
                    source = "manifest"

            if not compiled_sql:
                return "", False, 0, source

            truncated_sql, was_truncated, original_bytes = _truncate_utf8_bytes(compiled_sql, max_bytes)
            if was_truncated:
                logger.info(
                    "dbt_translator_compiled_sql_truncated",
                    model_name=str(dbt_resource_props.get("name") or ""),
                    source=source,
                    original_bytes=original_bytes,
                    max_bytes=max_bytes,
                )
                marker = f"\n\n-- [phlo] TRUNCATED compiled SQL: {original_bytes} bytes (limit {max_bytes} bytes)"
                truncated_sql = f"{truncated_sql}{marker}"

            return truncated_sql, was_truncated, original_bytes, source
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dbt_resource_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          dbt manifest resource dictionary.
        </PyParameter>

        <PyParameter name="&#x22;max_bytes&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum number of UTF-8 bytes to keep in SQL text.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        A tuple of compiled SQL text, truncation flag, original byte length,
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
