# maintenance_sensor (/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_sensor)



Dagster sensor and ops for policy-driven Iceberg table maintenance.

This module implements automated Iceberg table maintenance through Dagster
sensors that evaluate table statistics against configured policies and
trigger maintenance operations when thresholds are exceeded.

Maintenance Operations:

* Snapshot expiration: Remove old snapshots beyond retention policy
* File optimization: Compact small files via Trino OPTIMIZE
* Statistics collection: Gather table metadata for policy evaluation

Policy-Driven Automation:
The maintenance\_policy\_sensor continuously evaluates tables against
NamespacePolicy configurations loaded from YAML files. When thresholds
are exceeded (e.g., snapshot count > 20), the sensor triggers appropriate
maintenance jobs.

Integration Requirements:

* phlo-iceberg: For table statistics and maintenance operations
* phlo-trino: For OPTIMIZE command execution
* maintenance\_policy.yaml: Policy configuration file

Configuration File Format:
policies:

* namespace: raw
  expire:
  snapshot\_count\_gt: 20
  older\_than\_days: 7
  retain\_last: 5
  optimize:
  avg\_file\_size\_mb\_lt: 64.0
* namespace: curated
  ref: main

Example:
Including policy maintenance in definitions::

from phlo\_dagster.maintenance\_sensor import get\_policy\_maintenance\_definitions

policy\_defs = get\_policy\_maintenance\_definitions()
defs = dg.Definitions.merge(your\_defs, policy\_defs)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;OptimizeConfig&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_sensor/OptimizeConfig&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_validate_table_name&#x22;" type="&#x22;(table_name) -> str&#x22;">
      Validate fully-qualified table names before SQL interpolation.

      <PySourceCode>
        ```python
        def _validate_table_name(table_name: str) -> str:
            """Validate fully-qualified table names before SQL interpolation.

            Args:
                table_name: Table name to validate.

            Returns:
                Validated table name.

            Raises:
                ValueError: If table name is invalid.

            """
            if not _VALID_TABLE_NAME.fullmatch(table_name):
                raise ValueError(f"Invalid table name: {table_name}")
            return table_name
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table name to validate.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Validated table name.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_load_iceberg_stats&#x22;" type="&#x22;() -> Any&#x22;">
      Load get\_table\_stats lazily for optional integration support.

      <PySourceCode>
        ```python
        def _load_iceberg_stats() -> Any:
            """Load get_table_stats lazily for optional integration support.

            Args:
                None

            Returns:
                get_table_stats function.

            Raises:
                RuntimeError: If phlo-iceberg package is not available.

            """
            try:
                from phlo_iceberg.tables import get_table_stats
            except Exception as exc:  # noqa: BLE001 - runtime guidance for optional dependency
                raise RuntimeError(
                    "Iceberg maintenance requires phlo-iceberg. Install phlo-dagster[iceberg] "
                    "or phlo-iceberg."
                ) from exc
            return get_table_stats
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        get\_table\_stats function.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_load_optimize_query_engine&#x22;" type="&#x22;() -> QueryEngine&#x22;">
      Resolve the query engine used for maintenance OPTIMIZE operations.

      <PySourceCode>
        ```python
        def _load_optimize_query_engine() -> QueryEngine:
            """Resolve the query engine used for maintenance OPTIMIZE operations.

            Args:
                None

            Returns:
                QueryEngine provider.

            Raises:
                RuntimeError: If query_engine:trino capability is not available.

            """
            resolution = resolve_capability("query_engine", "trino")
            if resolution is None:
                raise RuntimeError(
                    "Trino OPTIMIZE requires a query_engine:trino capability. "
                    "Install phlo-trino or another provider exposing that capability."
                )
            return resolution.provider
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.capabilities.QueryEngine&#x22;">
        QueryEngine provider.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_evaluate_namespace&#x22;" type="&#x22;(policy, get_table_stats, context) -> list[TableAction]&#x22;">
      Evaluate all tables in a namespace against a policy.

      <PySourceCode>
        ```python
        def _evaluate_namespace(
            policy: NamespacePolicy,
            get_table_stats: Any,
            context: dg.SensorEvaluationContext,
        ) -> list[TableAction]:
            """Evaluate all tables in a namespace against a policy.

            Args:
                policy: Namespace policy configuration.
                get_table_stats: Function to get table statistics.
                context: Dagster sensor evaluation context.

            Returns:
                List of TableActions that have at least one action flagged.

            """
            actions: list[TableAction] = []
            tables = list_tables(policy.namespace, policy.ref)

            for table_name in tables:
                try:
                    stats = get_table_stats(table_name=table_name, ref=policy.ref)
                except Exception:
                    logger.exception("maintenance_sensor_stats_failed", table_name=table_name)
                    continue

                action = evaluate_table(table_name, stats, policy)
                if action.expire_snapshots or action.optimize:
                    actions.append(action)

            return actions
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;policy&#x22;" type="&#x22;NamespacePolicy&#x22;" value="undefined">
          Namespace policy configuration.
        </PyParameter>

        <PyParameter name="&#x22;get_table_stats&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Function to get table statistics.
        </PyParameter>

        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.SensorEvaluationContext&#x22;" value="undefined">
          Dagster sensor evaluation context.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of TableActions that have at least one action flagged.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;optimize_table_files&#x22;" type="&#x22;(context, config) -> dict[str, Any]&#x22;">
      Run Trino OPTIMIZE on tables to compact small files.

      <PySourceCode>
        ```python
        @dg.op
        def optimize_table_files(
            context: dg.OpExecutionContext,
            config: OptimizeConfig,
        ) -> dict[str, Any]:
            """Run Trino OPTIMIZE on tables to compact small files."""
            query_engine = _load_optimize_query_engine()
            results: list[dict[str, Any]] = []
            errors: list[str] = []

            for table_name in config.table_names:
                try:
                    validated_table_name = _validate_table_name(table_name)
                    query_engine.execute(f"ALTER TABLE {validated_table_name} EXECUTE optimize")
                    context.log.info(f"Optimized table {table_name}")
                    results.append({"table_name": table_name, "status": "success"})
                except Exception as e:
                    error_msg = f"Failed to optimize {table_name}: {e}"
                    context.log.warning(error_msg)
                    errors.append(error_msg)
                    results.append({"table_name": table_name, "status": "error", "error": str(e)})

            return {"results": results, "errors": errors}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.OpExecutionContext&#x22;" value="null" />

        <PyParameter name="&#x22;config&#x22;" type="&#x22;OptimizeConfig&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;optimize_tables_job&#x22;" type="&#x22;()&#x22;">
      Job that runs Trino OPTIMIZE on selected tables.

      <PySourceCode>
        ```python
        @dg.job(description="Optimize Iceberg table files via Trino EXECUTE optimize")
        def optimize_tables_job():
            """Job that runs Trino OPTIMIZE on selected tables."""
            optimize_table_files()
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;maintenance_policy_sensor&#x22;" type="&#x22;(context)&#x22;">
      Evaluate tables against maintenance policies, yield RunRequests as needed.

      <PySourceCode>
        ```python
        @dg.sensor(
            name="maintenance_policy_sensor",
            description=(
                "Evaluates table stats against maintenance policies "
                "and triggers maintenance when thresholds are exceeded"
            ),
            jobs=_SENSOR_TARGET_JOBS,
            minimum_interval_seconds=1800,
            default_status=dg.DefaultSensorStatus.STOPPED,
        )
        def maintenance_policy_sensor(context: dg.SensorEvaluationContext):
            """Evaluate tables against maintenance policies, yield RunRequests as needed.

            Args:
                context: Dagster sensor evaluation context.

            Returns:
                Generator of RunRequest objects for triggered maintenance jobs.

            Raises:
                No explicit exceptions raised. Logs warnings on failures.

            """
            cursor_key = context.cursor or datetime.now(timezone.utc).isoformat()
            policy_path = os.environ.get("PHLO_MAINTENANCE_POLICY_PATH", _DEFAULT_POLICY_PATH)

            try:
                policies = load_policies(policy_path)
            except Exception:
                logger.exception("maintenance_sensor_policy_load_failed", path=policy_path)
                return

            get_table_stats = _load_iceberg_stats()

            for policy in policies:
                actions = _evaluate_namespace(policy, get_table_stats, context)
                if not actions:
                    continue

                expire_tables = [a.table_name for a in actions if a.expire_snapshots]
                optimize_tables = [a.table_name for a in actions if a.optimize]

                if expire_tables:
                    if expire_snapshots_job is None:
                        logger.warning(
                            "maintenance_sensor_expire_job_unavailable",
                            namespace=policy.namespace,
                            table_count=len(expire_tables),
                        )
                        continue
                    logger.info(
                        "maintenance_sensor_expire_triggered",
                        namespace=policy.namespace,
                        table_count=len(expire_tables),
                    )
                    yield dg.RunRequest(
                        run_key=f"expire_{policy.namespace}_{cursor_key}",
                        job_name="expire_snapshots_job",
                        run_config=dg.RunConfig(
                            ops={
                                "expire_table_snapshots": {
                                    "config": {
                                        "namespace": policy.namespace,
                                        "ref": policy.ref,
                                        "snapshot_retention_days": (
                                            policy.expire.older_than_days if policy.expire else 7
                                        ),
                                        "snapshot_retain_last": (
                                            policy.expire.retain_last if policy.expire else 5
                                        ),
                                        "table_allowlist": expire_tables,
                                    }
                                }
                            }
                        ),
                    )

                if optimize_tables:
                    logger.info(
                        "maintenance_sensor_optimize_triggered",
                        namespace=policy.namespace,
                        table_count=len(optimize_tables),
                    )
                    yield dg.RunRequest(
                        run_key=f"optimize_{policy.namespace}_{cursor_key}",
                        job_name="optimize_tables_job",
                        run_config=dg.RunConfig(
                            ops={
                                "optimize_table_files": {
                                    "config": {
                                        "table_names": optimize_tables,
                                        "ref": policy.ref,
                                    }
                                }
                            }
                        ),
                    )

            context.update_cursor(datetime.now(timezone.utc).isoformat())
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.SensorEvaluationContext&#x22;" value="undefined">
          Dagster sensor evaluation context.
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        Generator of RunRequest objects for triggered maintenance jobs.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_policy_maintenance_definitions&#x22;" type="&#x22;() -> dg.Definitions&#x22;">
      Get Dagster definitions for policy-driven maintenance.

      Returns definitions including the policy sensor and optimize job,
      to be merged into a project's main definitions.

      <PySourceCode>
        ```python
        def get_policy_maintenance_definitions() -> dg.Definitions:
            """Get Dagster definitions for policy-driven maintenance.

            Returns definitions including the policy sensor and optimize job,
            to be merged into a project's main definitions.

            Args:
                None

            Returns:
                Dagster Definitions containing policy maintenance jobs and sensors.

            Raises:
                No explicit exceptions raised. Logs warnings if expire job unavailable.

            """
            jobs: list[dg.JobDefinition] = [optimize_tables_job]
            if expire_snapshots_job is None:
                logger.warning("dagster_policy_maintenance_expire_job_unavailable")
            else:
                jobs.insert(0, expire_snapshots_job)

            logger.info(
                "dagster_policy_maintenance_definitions_built",
                job_count=len(jobs),
                sensor_count=1,
            )
            return dg.Definitions(
                jobs=jobs,
                sensors=[maintenance_policy_sensor],
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dagster.Definitions&#x22;">
        Dagster Definitions containing policy maintenance jobs and sensors.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
