# DagsterOrchestratorAdapter (/docs/python-reference/packages/phlo-dagster/phlo_dagster/adapter/DagsterOrchestratorAdapter)



Translate capability specs into Dagster definitions.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata used by capability discovery.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;exec_service_name&#x22;" type="&#x22;(self) -> str | None&#x22;">
  Return the service container used for orchestrator-scoped CLI execution.

  <PySourceCode>
    ```python
    def exec_service_name(self) -> str | None:
        """Return the service container used for orchestrator-scoped CLI execution."""
        return "dagster"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;build_definitions&#x22;" type="&#x22;(self, *, assets, checks, resources) -> dg.Definitions&#x22;">
  Build Dagster definitions from capability specs.

  <PySourceCode>
    ```python
    def build_definitions(
        self,
        *,
        assets: Iterable[AssetSpec],
        checks: Iterable[AssetCheckSpec],
        resources: Iterable[ResourceSpec],
    ) -> dg.Definitions:
        """Build Dagster definitions from capability specs.

        Args:
            assets: Asset capability specs.
            checks: Asset check capability specs.
            resources: Resource capability specs.

        Returns:
            Dagster definitions bundle for assets, checks, and resources.

        """
        assets_list = list(assets)
        checks_list = list(checks)
        resources_list = list(resources)
        logger.info(
            "dagster_adapter_build_definitions_started",
            asset_spec_count=len(assets_list),
            check_spec_count=len(checks_list),
            resource_spec_count=len(resources_list),
        )

        resources_map: dict[str, Any] = {}
        for resource in resources_list:
            value = resource.resource
            if isinstance(value, dg.ResourceDefinition):
                resources_map[resource.name] = value
            else:
                resources_map[resource.name] = dg.ResourceDefinition.hardcoded_resource(value)

        asset_defs = [self._build_asset(spec) for spec in assets_list if spec.run is not None]
        check_defs = [self._build_check(check) for check in checks_list if check.fn is not None]

        logger.info(
            "dagster_adapter_build_definitions_completed",
            asset_definition_count=len(asset_defs),
            check_definition_count=len(check_defs),
            resource_definition_count=len(resources_map),
        )

        return dg.Definitions(
            assets=asset_defs,
            asset_checks=check_defs,
            resources=resources_map,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;assets&#x22;" type="&#x22;Iterable[AssetSpec]&#x22;" value="undefined">
      Asset capability specs.
    </PyParameter>

    <PyParameter name="&#x22;checks&#x22;" type="&#x22;Iterable[AssetCheckSpec]&#x22;" value="undefined">
      Asset check capability specs.
    </PyParameter>

    <PyParameter name="&#x22;resources&#x22;" type="&#x22;Iterable[ResourceSpec]&#x22;" value="undefined">
      Resource capability specs.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dagster.Definitions&#x22;">
    Dagster definitions bundle for assets, checks, and resources.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_asset&#x22;" type="&#x22;(self, spec) -> dg.AssetsDefinition&#x22;">
  Create a Dagster asset definition from a capability asset spec.

  <PySourceCode>
    ```python
    def _build_asset(self, spec: AssetSpec) -> dg.AssetsDefinition:
        """Create a Dagster asset definition from a capability asset spec.

        Args:
            spec: Asset capability spec.

        Returns:
            Dagster assets definition function.

        """
        check_specs = [
            dg.AssetCheckSpec(
                name=check.name,
                asset=_asset_key_from_string(check.asset_key),
                blocking=check.blocking,
                description=check.description,
            )
            for check in spec.checks
            if check.fn is None
        ]

        partitions_def = None
        if spec.partitions and spec.partitions.kind == "daily":
            from phlo_dagster.partitions import daily_partition

            partitions_def = daily_partition

        op_tags: dict[str, str] = {}
        if spec.run and spec.run.max_runtime_seconds:
            op_tags["dagster/max_runtime"] = str(spec.run.max_runtime_seconds)

        retry_policy = None
        if spec.run and spec.run.max_retries:
            retry_policy = dg.RetryPolicy(
                max_retries=spec.run.max_retries,
                delay=spec.run.retry_delay_seconds or 30,
            )

        automation_condition = None
        if spec.run and spec.run.cron:
            automation_condition = dg.AutomationCondition.on_cron(spec.run.cron)

        freshness_policy = None
        if spec.run and spec.run.freshness_hours:
            freshness_policy = dg.FreshnessPolicy.time_window(
                warn_window=timedelta(hours=spec.run.freshness_hours[0]),
                fail_window=timedelta(hours=spec.run.freshness_hours[1]),
            )

        asset_key = _asset_key_from_string(spec.key)
        deps = [_asset_key_from_string(dep) for dep in spec.deps]
        required_resources = set(spec.resources)
        asset_metadata = _convert_metadata(spec.metadata) if spec.metadata else None

        name = asset_key.path[-1]
        key_prefix = asset_key.path[:-1] or None

        @dg.asset(
            name=name,
            key_prefix=key_prefix,
            group_name=spec.group,
            description=spec.description,
            kinds=spec.kinds,
            tags=spec.tags,
            metadata=asset_metadata,
            partitions_def=partitions_def,
            deps=deps,
            check_specs=check_specs or None,
            required_resource_keys=required_resources or None,
            op_tags=op_tags or None,
            retry_policy=retry_policy,
            automation_condition=automation_condition,
            freshness_policy=freshness_policy,
        )
        def _asset_fn(context) -> Iterable[Any]:
            """Execute capability asset logic and yield Dagster results.

            Args:
                context: Dagster execution context.

            Yields:
                Dagster materialization or asset check results.

            """
            runtime = DagsterRuntime(
                context, asset_capability_overrides=dict(spec.capability_overrides)
            )
            results = spec.run.fn(runtime) if spec.run else []
            if results is None:
                return
            for result in results:
                if isinstance(result, MaterializeResult):
                    metadata = _convert_metadata(result.metadata)
                    if result.status:
                        metadata.setdefault("status", dg.MetadataValue.text(result.status))
                    status = str(result.status or "").lower()
                    if status in {"failure", "failed", "error"}:
                        logger.warning(
                            "dagster_adapter_asset_materialization_failed_status",
                            asset_key=spec.key,
                            status=result.status,
                            run_id=runtime.run_id,
                            partition_key=runtime.partition_key,
                        )
                        raise dg.Failure(
                            description=f"Asset run reported status '{result.status}'",
                            metadata=metadata,
                        )
                    yield dg.MaterializeResult(metadata=metadata)
                elif isinstance(result, CheckResult):
                    severity = _severity_from_string(result.severity) or dg.AssetCheckSeverity.ERROR
                    asset_check_key = _asset_key_from_string(result.asset_key)
                    metadata = _convert_metadata(result.metadata)
                    yield dg.AssetCheckResult(
                        passed=result.passed,
                        check_name=result.check_name,
                        asset_key=asset_check_key,
                        metadata=metadata,
                        severity=severity,
                    )

        return _asset_fn
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;AssetSpec&#x22;" value="undefined">
      Asset capability spec.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dagster.AssetsDefinition&#x22;">
    Dagster assets definition function.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_check&#x22;" type="&#x22;(self, spec) -> dg.AssetChecksDefinition&#x22;">
  Create a Dagster asset check definition from a capability check spec.

  <PySourceCode>
    ```python
    def _build_check(self, spec: AssetCheckSpec) -> dg.AssetChecksDefinition:
        """Create a Dagster asset check definition from a capability check spec.

        Args:
            spec: Asset check capability spec.

        Returns:
            Dagster asset check definition function.

        """
        asset_key = _asset_key_from_string(spec.asset_key)
        default_severity = _severity_from_string(spec.severity) or dg.AssetCheckSeverity.ERROR

        @dg.asset_check(
            name=spec.name,
            asset=asset_key,
            blocking=spec.blocking,
            description=spec.description,
        )
        def _check_fn(context) -> dg.AssetCheckResult:
            """Execute capability check logic and return Dagster check result.

            Args:
                context: Dagster execution context.

            Returns:
                Dagster asset check result.

            """
            runtime = DagsterRuntime(context)
            result = spec.fn(runtime) if spec.fn else None
            if result is None:
                return dg.AssetCheckResult(passed=True, check_name=spec.name, asset_key=asset_key)
            metadata = _convert_metadata(result.metadata)
            result_severity = _severity_from_string(result.severity)
            severity = result_severity or default_severity
            return dg.AssetCheckResult(
                passed=result.passed,
                check_name=result.check_name,
                asset_key=asset_key,
                metadata=metadata,
                severity=severity,
            )

        return _check_fn
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;AssetCheckSpec&#x22;" value="undefined">
      Asset check capability spec.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dagster.AssetChecksDefinition&#x22;">
    Dagster asset check definition function.
  </PyFunctionReturn>
</PyFunction>
