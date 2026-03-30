# adapter (/docs/python-reference/packages/phlo-dagster/phlo_dagster/adapter)



Dagster orchestrator adapter for Phlo capability specs.

This module provides the core translation layer between Phlo's capability-based
architecture and Dagster's asset-centric execution model. It converts capability
specifications (AssetSpec, AssetCheckSpec, ResourceSpec) into Dagster definitions.

Translation Mapping:

* AssetSpec → @asset decorated functions
* AssetCheckSpec → @asset\_check decorated functions
* ResourceSpec → Dagster ResourceDefinition
* Partitions → Dagster PartitionsDefinition
* Cron schedules → Dagster AutomationCondition
* Freshness windows → Dagster FreshnessPolicy

Key Components:

* DagsterOrchestratorAdapter: Main adapter implementing OrchestratorAdapterPlugin
* DagsterRuntime: Runtime context wrapper providing Dagster integration
* Metadata conversion helpers for Dagster-compatible types

Dagster Integration Points:

* AssetExecutionContext: Wrapped to provide Phlo RuntimeContext interface
* MaterializeResult/CheckResult: Converted to Dagster result types
* Retry policies and op tags from spec configuration
* Dependencies mapped to AssetKey relationships

Example:
Adapter instantiation::

from phlo\_dagster.adapter import DagsterOrchestratorAdapter
from phlo.capabilities.discovery import discover\_capabilities

Discover capabilities from user code [#discover-capabilities-from-user-code]

discover\_capabilities()

Build Dagster definitions [#build-dagster-definitions]

adapter = DagsterOrchestratorAdapter()
defs = adapter.build\_definitions(
assets=registry.list\_assets(),
checks=registry.list\_checks(),
resources=registry.list\_resources(),
)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DagsterRuntime&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/adapter/DagsterRuntime&#x22;" />

      <Card title="&#x22;DagsterOrchestratorAdapter&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/adapter/DagsterOrchestratorAdapter&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_asset_key_from_string&#x22;" type="&#x22;(key) -> dg.AssetKey&#x22;">
      Convert a dotted asset key string into a Dagster asset key.

      <PySourceCode>
        ```python
        def _asset_key_from_string(key: str) -> dg.AssetKey:
            """Convert a dotted asset key string into a Dagster asset key.

            Args:
                key: Asset key in dotted or simple form.

            Returns:
                Dagster asset key object.

            """
            if "." in key:
                return dg.AssetKey(key.split("."))
            return dg.AssetKey([key])
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset key in dotted or simple form.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dagster.AssetKey&#x22;">
        Dagster asset key object.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_metadata_value&#x22;" type="&#x22;(value) -> dg.MetadataValue&#x22;">
      Convert a Python value into a Dagster metadata value.

      <PySourceCode>
        ```python
        def _metadata_value(value: Any) -> dg.MetadataValue:
            """Convert a Python value into a Dagster metadata value.

            Args:
                value: Raw metadata value.

            Returns:
                Dagster metadata wrapper for the provided value.

            """
            if isinstance(value, dg.MetadataValue):
                return value
            if isinstance(value, dg.TableSchema):
                return dg.MetadataValue.table_schema(value)
            if isinstance(value, bool):
                return dg.MetadataValue.bool(value)
            if isinstance(value, int):
                return dg.MetadataValue.int(value)
            if isinstance(value, float):
                return dg.MetadataValue.float(value)
            if isinstance(value, str):
                return dg.MetadataValue.text(value)
            try:
                return dg.MetadataValue.json(value)
            except TypeError:
                return dg.MetadataValue.text(repr(value))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Raw metadata value.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dagster.MetadataValue&#x22;">
        Dagster metadata wrapper for the provided value.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_convert_metadata&#x22;" type="&#x22;(metadata) -> dict[str, dg.MetadataValue]&#x22;">
      Normalize metadata keys and values for Dagster materializations.

      <PySourceCode>
        ```python
        def _convert_metadata(metadata: dict[str, Any]) -> dict[str, dg.MetadataValue]:
            """Normalize metadata keys and values for Dagster materializations.

            Args:
                metadata: Raw metadata mapping from capability results.

            Returns:
                Metadata mapping with Dagster-compatible values.

            """
            converted: dict[str, dg.MetadataValue] = {}
            for key, value in metadata.items():
                if key == "phlo/column_schema" and isinstance(value, list):
                    columns: list[dg.TableColumn] = []
                    for column in value:
                        if not isinstance(column, dict):
                            continue
                        columns.append(
                            dg.TableColumn(
                                name=str(column.get("name", "")),
                                type=str(column.get("type", "")),
                                description=str(column.get("description", "")),
                            )
                        )
                    if columns:
                        converted["dagster/column_schema"] = _metadata_value(
                            dg.TableSchema(columns=columns)
                        )
                    continue
                converted[key] = _metadata_value(value)
            return converted
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;metadata&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Raw metadata mapping from capability results.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Metadata mapping with Dagster-compatible values.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_severity_from_string&#x22;" type="&#x22;(value) -> dg.AssetCheckSeverity | None&#x22;">
      Map a string severity label to Dagster severity.

      <PySourceCode>
        ```python
        def _severity_from_string(value: str | None) -> dg.AssetCheckSeverity | None:
            """Map a string severity label to Dagster severity.

            Args:
                value: Severity string from capability checks.

            Returns:
                Dagster severity if recognized, otherwise ``None``.

            """
            if not value:
                return None
            normalized = value.strip().lower()
            if normalized in {"info", "informational"}:
                return dg.AssetCheckSeverity.WARN
            if normalized in {"warn", "warning"}:
                return dg.AssetCheckSeverity.WARN
            if normalized in {"error", "critical"}:
                return dg.AssetCheckSeverity.ERROR
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Severity string from capability checks.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dg.AssetCheckSeverity | None&#x22;">
        Dagster severity if recognized, otherwise `None`.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
