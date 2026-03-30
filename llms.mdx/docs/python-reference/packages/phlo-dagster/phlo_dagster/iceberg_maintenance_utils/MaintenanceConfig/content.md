# MaintenanceConfig (/docs/python-reference/packages/phlo-dagster/phlo_dagster/iceberg_maintenance_utils/MaintenanceConfig)



Configuration for Iceberg table maintenance operations.

Attributes [#attributes]

<PyAttribute name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="&#x22;'raw'&#x22;">
  Namespace to run maintenance on, or `"all"` for all namespaces.
</PyAttribute>

<PyAttribute name="&#x22;snapshot_retention_days&#x22;" type="&#x22;Annotated[int, Field(gt=0)]&#x22;" value="&#x22;7&#x22;">
  Snapshot age threshold for expiration in days.
</PyAttribute>

<PyAttribute name="&#x22;snapshot_retain_last&#x22;" type="&#x22;Annotated[int, Field(ge=0)]&#x22;" value="&#x22;5&#x22;">
  Minimum number of snapshots to retain.
</PyAttribute>

<PyAttribute name="&#x22;orphan_retention_days&#x22;" type="&#x22;Annotated[int, Field(gt=0)]&#x22;" value="&#x22;3&#x22;">
  Orphan file age threshold for deletion in days.
</PyAttribute>

<PyAttribute name="&#x22;orphan_dry_run&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
  If `True`, list orphan files without deleting.
</PyAttribute>

<PyAttribute name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;">
  Nessie reference (branch or tag) used for catalog operations.
</PyAttribute>

<PyAttribute name="&#x22;table_allowlist&#x22;" type="&#x22;Optional[list[str]]&#x22;" value="&#x22;None&#x22;" />
