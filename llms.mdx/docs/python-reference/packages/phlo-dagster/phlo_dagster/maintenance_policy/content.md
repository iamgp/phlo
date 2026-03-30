# maintenance_policy (/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_policy)



Policy models and evaluation for automated Iceberg table maintenance.

This module defines the data models and evaluation logic for policy-driven
Iceberg table maintenance. Policies specify thresholds that trigger maintenance
operations like snapshot expiration and file optimization.

Policy Types:

* ExpireSnapshotsPolicy: Thresholds for snapshot cleanup
* OptimizePolicy: Thresholds for file compaction
* NamespacePolicy: Complete policy scoped to a catalog namespace

Thresholds:

* Snapshot expiration: snapshot\_count\_gt, older\_than\_days, retain\_last
* File optimization: avg\_file\_size\_mb\_lt

Evaluation Logic:
Table statistics are compared against policy thresholds to determine
required maintenance actions (TableAction). Multiple actions can be
triggered for a single table.

Configuration:
Policies are loaded from YAML files with structure::

policies:

* namespace: raw
  ref: main
  expire:
  snapshot\_count\_gt: 20
  older\_than\_days: 7
  retain\_last: 5
  optimize:
  avg\_file\_size\_mb\_lt: 64.0

Example:
Loading and evaluating policies::

from phlo\_dagster.maintenance\_policy import load\_policies, evaluate\_table

policies = load\_policies("maintenance\_policy.yaml")
for policy in policies:
for table in list\_tables(policy.namespace, policy.ref):
stats = get\_table\_stats(table, policy.ref)
action = evaluate\_table(table, stats, policy)
if action.expire\_snapshots:

Trigger snapshot expiration [#trigger-snapshot-expiration]

pass

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ExpireSnapshotsPolicy&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_policy/ExpireSnapshotsPolicy&#x22;" />

      <Card title="&#x22;OptimizePolicy&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_policy/OptimizePolicy&#x22;" />

      <Card title="&#x22;NamespacePolicy&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_policy/NamespacePolicy&#x22;" />

      <Card title="&#x22;TableAction&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_policy/TableAction&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;evaluate_table&#x22;" type="&#x22;(table_name, stats, policy) -> TableAction&#x22;">
      Evaluate table stats against policy thresholds.

      <PySourceCode>
        ```python
        def evaluate_table(
            table_name: str,
            stats: dict[str, Any],
            policy: NamespacePolicy,
        ) -> TableAction:
            """Evaluate table stats against policy thresholds.

            Args:
                table_name: Fully qualified table name.
                stats: Table statistics dict (keys: snapshot_count, total_size_mb, file_count).
                policy: Namespace policy with optional expire/optimize thresholds.

            Returns:
                TableAction indicating which maintenance operations to run.

            """
            expire = False
            optimize = False

            if policy.expire is not None:
                snapshot_count = stats.get("snapshot_count", 0)
                if snapshot_count > policy.expire.snapshot_count_gt:
                    expire = True

            if policy.optimize is not None:
                file_count = stats.get("file_count", 0)
                total_size_mb = stats.get("total_size_mb", 0.0)
                if file_count > 0:
                    avg_file_size_mb = total_size_mb / file_count
                    if avg_file_size_mb < policy.optimize.avg_file_size_mb_lt:
                        optimize = True

            return TableAction(
                table_name=table_name,
                expire_snapshots=expire,
                optimize=optimize,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Fully qualified table name.
        </PyParameter>

        <PyParameter name="&#x22;stats&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Table statistics dict (keys: snapshot\_count, total\_size\_mb, file\_count).
        </PyParameter>

        <PyParameter name="&#x22;policy&#x22;" type="&#x22;NamespacePolicy&#x22;" value="undefined">
          Namespace policy with optional expire/optimize thresholds.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_dagster.maintenance_policy.TableAction&#x22;">
        TableAction indicating which maintenance operations to run.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;load_policies&#x22;" type="&#x22;(path) -> list[NamespacePolicy]&#x22;">
      Load maintenance policies from a YAML file.

      Expected format::

      policies:

      * namespace: raw
        expire:
        snapshot\_count\_gt: 20
        older\_than\_days: 7
        retain\_last: 5
        optimize:
        avg\_file\_size\_mb\_lt: 64.0
      * namespace: curated
        expire:
        snapshot\_count\_gt: 10

      <PySourceCode>
        ```python
        def load_policies(path: str | Path) -> list[NamespacePolicy]:
            """Load maintenance policies from a YAML file.

            Expected format::

                policies:
                  - namespace: raw
                    expire:
                      snapshot_count_gt: 20
                      older_than_days: 7
                      retain_last: 5
                    optimize:
                      avg_file_size_mb_lt: 64.0
                  - namespace: curated
                    expire:
                      snapshot_count_gt: 10

            Args:
                path: Path to the YAML policy file.

            Returns:
                List of parsed namespace policies.

            """
            try:
                import yaml
            except Exception as exc:  # noqa: BLE001 - runtime guidance for optional dependency
                raise RuntimeError(
                    "Policy loading requires PyYAML. Install phlo-dagster[policies] or pyyaml."
                ) from exc

            policy_path = Path(path)
            data = yaml.safe_load(policy_path.read_text())
            policies: list[NamespacePolicy] = []

            for entry in (data or {}).get("policies", []):
                expire = None
                optimize = None

                if "expire" in entry:
                    expire = ExpireSnapshotsPolicy(**entry["expire"])
                if "optimize" in entry:
                    optimize = OptimizePolicy(**entry["optimize"])

                policies.append(
                    NamespacePolicy(
                        namespace=entry["namespace"],
                        expire=expire,
                        optimize=optimize,
                        ref=entry.get("ref", "main"),
                    )
                )

            logger.info("maintenance_policies_loaded", policy_count=len(policies), path=str(policy_path))
            return policies
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;str | Path&#x22;" value="undefined">
          Path to the YAML policy file.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of parsed namespace policies.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
