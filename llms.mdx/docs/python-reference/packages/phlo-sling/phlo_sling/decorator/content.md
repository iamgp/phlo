# decorator (/docs/python-reference/packages/phlo-sling/phlo_sling/decorator)



Decorator helpers for registering Sling-backed Phlo assets.

This module provides decorators and helper functions for registering Sling-based
data replication assets within the Phlo orchestration platform. It supports both
single asset registration via @phlo\_sling\_replication and batch registration
via @phlo\_sling\_assets.

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_sling_assets&#x22;" type="&#x22;() -> list[AssetSpec]&#x22;">
      Return registered Sling replication asset specifications.

      Retrieves all Sling replication assets that have been registered via
      the
      @phlo\_sling\_replication or @phlo\_sling\_assets decorators.

      <PySourceCode>
        ```python
        def get_sling_assets() -> list[AssetSpec]:
            """Return registered Sling replication asset specifications.

                Retrieves all Sling replication assets that have been registered via
            the
                @phlo_sling_replication or @phlo_sling_assets decorators.

            Returns:
                    List of AssetSpec objects representing all registered Sling
                    replication pipelines.

            """
            return list(_SLING_ASSETS)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of AssetSpec objects representing all registered Sling
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;clear_sling_assets&#x22;" type="&#x22;() -> None&#x22;">
      Clear all registered Sling replication asset specifications.

      Removes all registered Sling assets from the internal registry. This
      is primarily used for testing and plugin reload scenarios.

      <PySourceCode>
        ```python
        def clear_sling_assets() -> None:
            """Clear all registered Sling replication asset specifications.

            Removes all registered Sling assets from the internal registry. This
            is primarily used for testing and plugin reload scenarios.

            Returns:
                None

            """
            _SLING_ASSETS.clear()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_validate_replication_mode&#x22;" type="&#x22;(mode) -> None&#x22;">
      Validate the replication mode is supported.

      Checks that the provided replication mode is one of the supported
      Sling replication modes.

      <PySourceCode>
        ```python
        def _validate_replication_mode(mode: str) -> None:
            """Validate the replication mode is supported.

            Checks that the provided replication mode is one of the supported
            Sling replication modes.

            Args:
                mode: The replication mode string to validate.

            Raises:
                PhloConfigError: If the mode is not in the set of valid modes.

            """
            valid_modes = {"full-refresh", "incremental", "snapshot", "backfill"}
            if mode not in valid_modes:
                raise PhloConfigError(
                    message=f"Invalid replication mode: {mode}",
                    suggestions=[f"Use one of: {', '.join(sorted(valid_modes))}"],
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;mode&#x22;" type="&#x22;str&#x22;" value="undefined">
          The replication mode string to validate.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_validate_incremental_config&#x22;" type="&#x22;(mode, update_key) -> None&#x22;">
      Validate incremental mode has a required update key.

      Ensures that incremental replication mode has an update\_key configured
      for change detection.

      <PySourceCode>
        ```python
        def _validate_incremental_config(mode: str, update_key: str | None) -> None:
            """Validate incremental mode has a required update key.

            Ensures that incremental replication mode has an update_key configured
            for change detection.

            Args:
                mode: The replication mode string.
                update_key: The update key column name (optional).

            Raises:
                PhloConfigError: If mode is "incremental" but update_key is None.

            """
            if mode == "incremental" and not update_key:
                raise PhloConfigError(
                    message="Incremental mode requires an update_key",
                    suggestions=["Set update_key to a timestamp or incrementing column"],
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;mode&#x22;" type="&#x22;str&#x22;" value="undefined">
          The replication mode string.
        </PyParameter>

        <PyParameter name="&#x22;update_key&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          The update key column name (optional).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_normalize_primary_key&#x22;" type="&#x22;(primary_key) -> list[str]&#x22;">
      Normalize primary key input into a list of column names.

      Converts various primary key input formats into a consistent list
      of column name strings.

      <PySourceCode>
        ```python
        def _normalize_primary_key(primary_key: list[str] | str | None) -> list[str]:
            """Normalize primary key input into a list of column names.

            Converts various primary key input formats into a consistent list
            of column name strings.

            Args:
                primary_key: Input primary key specification (string, list, or None).

            Returns:
                List of column name strings.

            """
            return [primary_key] if isinstance(primary_key, str) else list(primary_key or [])
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;primary_key&#x22;" type="&#x22;list[str] | str | None&#x22;" value="undefined">
          Input primary key specification (string, list, or None).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of column name strings.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_build_replication_config&#x22;" type="&#x22;(*, stream_name, table_name, source_conn, group, target_conn, mode, primary_key, update_key, object, select, where, source_options, target_options) -> ReplicationConfig&#x22;">
      Validate and normalize decorator-style replication inputs.

      Processes decorator arguments to create a validated ReplicationConfig
      with defaults applied and constraints checked.

      <PySourceCode>
        ```python
        def _build_replication_config(
            *,
            stream_name: str,
            table_name: str,
            source_conn: str,
            group: str,
            target_conn: str | None,
            mode: Literal["full-refresh", "incremental", "snapshot", "backfill"] | None,
            primary_key: list[str] | str | None,
            update_key: str | None,
            object: str | None,
            select: list[str] | None,
            where: str | None,
            source_options: dict[str, Any] | None,
            target_options: dict[str, Any] | None,
        ) -> ReplicationConfig:
            """Validate and normalize decorator-style replication inputs.

            Processes decorator arguments to create a validated ReplicationConfig
            with defaults applied and constraints checked.

            Args:
                stream_name: Source stream identifier.
                table_name: Target table name.
                source_conn: Source connection name.
                group: Asset group name.
                target_conn: Target connection name (optional).
                mode: Replication mode (optional, defaults to settings).
                primary_key: Primary key column(s) (optional).
                update_key: Update key column for incremental mode (optional).
                object: Target object path for file-based targets (optional).
                select: Column selection list (optional).
                where: SQL WHERE clause (optional).
                source_options: Additional source options dict (optional).
                target_options: Additional target options dict (optional).

            Returns:
                Validated ReplicationConfig instance.

            Raises:
                PhloConfigError: If validation fails (invalid mode, missing
                    update_key, etc.).

            """
            resolved_mode = mode or get_settings().sling_default_mode
            _validate_replication_mode(resolved_mode)
            _validate_incremental_config(resolved_mode, update_key)

            return ReplicationConfig(
                stream_name=stream_name,
                table_name=table_name,
                source_conn=source_conn,
                target_conn=target_conn,
                mode=resolved_mode,
                primary_key=_normalize_primary_key(primary_key),
                update_key=update_key,
                group_name=group,
                object=object,
                select=select or [],
                where=where,
                source_options=source_options or {},
                target_options=target_options or {},
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;stream_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source stream identifier.
        </PyParameter>

        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target table name.
        </PyParameter>

        <PyParameter name="&#x22;source_conn&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source connection name.
        </PyParameter>

        <PyParameter name="&#x22;group&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset group name.
        </PyParameter>

        <PyParameter name="&#x22;target_conn&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Target connection name (optional).
        </PyParameter>

        <PyParameter name="&#x22;mode&#x22;" type="&#x22;Literal['full-refresh', 'incremental', 'snapshot', 'backfill'] | None&#x22;" value="undefined">
          Replication mode (optional, defaults to settings).
        </PyParameter>

        <PyParameter name="&#x22;primary_key&#x22;" type="&#x22;list[str] | str | None&#x22;" value="undefined">
          Primary key column(s) (optional).
        </PyParameter>

        <PyParameter name="&#x22;update_key&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Update key column for incremental mode (optional).
        </PyParameter>

        <PyParameter name="&#x22;object&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Target object path for file-based targets (optional).
        </PyParameter>

        <PyParameter name="&#x22;select&#x22;" type="&#x22;list[str] | None&#x22;" value="undefined">
          Column selection list (optional).
        </PyParameter>

        <PyParameter name="&#x22;where&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          SQL WHERE clause (optional).
        </PyParameter>

        <PyParameter name="&#x22;source_options&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="undefined">
          Additional source options dict (optional).
        </PyParameter>

        <PyParameter name="&#x22;target_options&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="undefined">
          Additional target options dict (optional).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_sling.registry.ReplicationConfig&#x22;">
        Validated ReplicationConfig instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_build_asset_run&#x22;" type="&#x22;(repl_config, source_func, override_resolver) -> Callable[[RuntimeContext], Iterator[MaterializeResult]]&#x22;">
      Build the runtime function used by Sling-backed asset specs.

      Creates the execution function that orchestrates Sling replication
      runs and yields MaterializeResult objects.

      <PySourceCode>
        ```python
        def _build_asset_run(
            repl_config: ReplicationConfig,
            source_func: Callable[..., Any],
            override_resolver: Callable[[RuntimeContext], dict[str, Any] | None],
        ) -> Callable[[RuntimeContext], Iterator[MaterializeResult]]:
            """Build the runtime function used by Sling-backed asset specs.

            Creates the execution function that orchestrates Sling replication
            runs and yields MaterializeResult objects.

            Args:
                repl_config: The replication configuration.
                source_func: The decorated user function.
                override_resolver: Callable that resolves runtime overrides from
                    the user function.

            Returns:
                Callable that executes the Sling replication and yields results.

            """

            def run(runtime: RuntimeContext) -> Iterator[MaterializeResult]:
                partition_date = runtime.partition_key or "latest"
                run_id = runtime.run_id or "unknown"
                logger = runtime.logger

                log_event(logger, "info", "starting_sling_replication", partition_date=partition_date)
                log_event(
                    logger,
                    "info",
                    "sling_stream_selected",
                    stream_name=repl_config.stream_name,
                    table_name=repl_config.full_table_name,
                    mode=repl_config.mode,
                )

                from phlo_sling.executor import SlingIngester

                ingester = SlingIngester(
                    context=runtime,
                    logger=logger,
                    replication_config=repl_config,
                    source_func=source_func,
                    overrides=override_resolver(runtime),
                )
                result = ingester.run_ingestion(
                    partition_key=partition_date,
                    parameters={"run_id": run_id},
                )

                if result.status == "no_data":
                    yield MaterializeResult(
                        metadata={
                            "partition_date": partition_date,
                            "rows_loaded": 0,
                            "status": "no_data",
                            "stream_name": repl_config.stream_name,
                        },
                        status="no_data",
                    )
                    return

                yield MaterializeResult(
                    metadata={
                        "partition_date": partition_date,
                        "rows_inserted": result.rows_inserted,
                        "rows_deleted": result.rows_deleted,
                        "table_name": repl_config.full_table_name,
                        "stream_name": repl_config.stream_name,
                        "mode": repl_config.mode,
                        "sling_elapsed_seconds": result.metadata.get("sling_elapsed_seconds", 0.0),
                        "total_elapsed_seconds": result.metadata.get("total_elapsed_seconds", 0.0),
                    },
                    status=result.status,
                )

            return run
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;repl_config&#x22;" type="&#x22;ReplicationConfig&#x22;" value="undefined">
          The replication configuration.
        </PyParameter>

        <PyParameter name="&#x22;source_func&#x22;" type="&#x22;Callable[..., Any]&#x22;" value="undefined">
          The decorated user function.
        </PyParameter>

        <PyParameter name="&#x22;override_resolver&#x22;" type="&#x22;Callable[[RuntimeContext], dict[str, Any] | None]&#x22;" value="undefined">
          Callable that resolves runtime overrides from
          the user function.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
        Callable that executes the Sling replication and yields results.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_register_sling_asset&#x22;" type="&#x22;(*, repl_config, source_func, override_resolver, description, owner, consumers, sla, max_runtime_seconds, max_retries, retry_delay_seconds, cron, freshness_hours, extra_metadata=None, extra_tags=None) -> AssetSpec&#x22;">
      Register a Sling asset spec and return it.

      Creates an AssetSpec from the replication configuration and registers
      it in the internal asset registry.

      <PySourceCode>
        ```python
        def _register_sling_asset(
            *,
            repl_config: ReplicationConfig,
            source_func: Callable[..., Any],
            override_resolver: Callable[[RuntimeContext], dict[str, Any] | None],
            description: str | None,
            owner: str | None,
            consumers: list[Consumer | str] | None,
            sla: SLA | None,
            max_runtime_seconds: int,
            max_retries: int,
            retry_delay_seconds: int,
            cron: str | None,
            freshness_hours: tuple[int, int] | None,
            extra_metadata: dict[str, Any] | None = None,
            extra_tags: dict[str, str] | None = None,
        ) -> AssetSpec:
            """Register a Sling asset spec and return it.

            Creates an AssetSpec from the replication configuration and registers
            it in the internal asset registry.

            Args:
                repl_config: The replication configuration.
                source_func: The decorated user function.
                override_resolver: Callable for resolving runtime overrides.
                description: Asset description (optional).
                owner: Asset owner identifier (optional).
                consumers: List of data consumers (optional).
                sla: Service level agreement definition (optional).
                max_runtime_seconds: Maximum execution time allowed.
                max_retries: Maximum retry attempts on failure.
                retry_delay_seconds: Delay between retry attempts.
                cron: Cron schedule string (optional).
                freshness_hours: Data freshness requirements as (warning, error)
                    tuple (optional).
                extra_metadata: Additional metadata dict (optional).
                extra_tags: Additional tags dict (optional).

            Returns:
                The registered AssetSpec instance.

            """
            normalized_consumers = normalize_consumers(consumers)
            asset_spec = AssetSpec(
                key=repl_config.asset_key,
                group=repl_config.group_name,
                description=description
                or f"Replicates {repl_config.stream_name} to {repl_config.full_table_name}",
                kinds={"sling", "replication"},
                tags={"source": "sling", "mode": repl_config.mode, **(extra_tags or {})},
                metadata={
                    "stream_name": repl_config.stream_name,
                    "table_name": repl_config.table_name,
                    "source_conn": repl_config.source_conn,
                    "mode": repl_config.mode,
                    "primary_key": repl_config.primary_key,
                    "update_key": repl_config.update_key,
                    "group": repl_config.group_name,
                    "owner": owner,
                    "consumers": serialize_consumers(normalized_consumers),
                    "sla": serialize_sla(sla),
                    **(extra_metadata or {}),
                },
                partitions=PartitionSpec(kind="daily"),
                resources=set(),
                run=RunSpec(
                    fn=_build_asset_run(repl_config, source_func, override_resolver),
                    max_runtime_seconds=max_runtime_seconds,
                    max_retries=max_retries,
                    retry_delay_seconds=retry_delay_seconds,
                    cron=cron,
                    freshness_hours=freshness_hours,
                ),
                checks=[],
            )
            _SLING_ASSETS.append(asset_spec)
            return asset_spec
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;repl_config&#x22;" type="&#x22;ReplicationConfig&#x22;" value="undefined">
          The replication configuration.
        </PyParameter>

        <PyParameter name="&#x22;source_func&#x22;" type="&#x22;Callable[..., Any]&#x22;" value="undefined">
          The decorated user function.
        </PyParameter>

        <PyParameter name="&#x22;override_resolver&#x22;" type="&#x22;Callable[[RuntimeContext], dict[str, Any] | None]&#x22;" value="undefined">
          Callable for resolving runtime overrides.
        </PyParameter>

        <PyParameter name="&#x22;description&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Asset description (optional).
        </PyParameter>

        <PyParameter name="&#x22;owner&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Asset owner identifier (optional).
        </PyParameter>

        <PyParameter name="&#x22;consumers&#x22;" type="&#x22;list[Consumer | str] | None&#x22;" value="undefined">
          List of data consumers (optional).
        </PyParameter>

        <PyParameter name="&#x22;sla&#x22;" type="&#x22;SLA | None&#x22;" value="undefined">
          Service level agreement definition (optional).
        </PyParameter>

        <PyParameter name="&#x22;max_runtime_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum execution time allowed.
        </PyParameter>

        <PyParameter name="&#x22;max_retries&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum retry attempts on failure.
        </PyParameter>

        <PyParameter name="&#x22;retry_delay_seconds&#x22;" type="&#x22;int&#x22;" value="undefined">
          Delay between retry attempts.
        </PyParameter>

        <PyParameter name="&#x22;cron&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Cron schedule string (optional).
        </PyParameter>

        <PyParameter name="&#x22;freshness_hours&#x22;" type="&#x22;tuple[int, int] | None&#x22;" value="undefined">
          Data freshness requirements as (warning, error)
          tuple (optional).
        </PyParameter>

        <PyParameter name="&#x22;extra_metadata&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
          Additional metadata dict (optional).
        </PyParameter>

        <PyParameter name="&#x22;extra_tags&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;">
          Additional tags dict (optional).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.AssetSpec&#x22;">
        The registered AssetSpec instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;phlo_sling_replication&#x22;" type="&#x22;(stream_name, table_name, source_conn, group, *, target_conn=None, mode=None, primary_key=None, update_key=None, object=None, select=None, where=None, source_options=None, target_options=None, cron=None, freshness_hours=None, max_runtime_seconds=600, max_retries=3, retry_delay_seconds=30, owner=None, consumers=None, sla=None) -> Callable[[Callable[..., Any]], Callable[..., Any]]&#x22;">
      Register a function as a Sling-backed replication asset.

      Decorator that registers a function as a Sling-based data replication
      asset within the Phlo orchestration platform. The decorated function
      receives a `RuntimeContext` and may return a dict of Sling overrides
      such as a dynamically resolved `src_stream` or partition-specific
      `where` clause.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Basic incremental replication::

        @phlo\_sling\_replication(
        stream\_name="public.users",
        table\_name="users",
        source\_conn="PHLO\_POSTGRES",
        group="ingestion",
        mode="incremental",
        update\_key="updated\_at",
        )
        def replicate\_users(context):

        Optional: return runtime overrides [#optional-return-runtime-overrides]

        return \{"where": f"updated\_at >= '\{context.partition\_key}'"}
      </Callout>

      <PySourceCode>
        ```python
        def phlo_sling_replication(
            stream_name: str,
            table_name: str,
            source_conn: str,
            group: str,
            *,
            target_conn: str | None = None,
            mode: Literal["full-refresh", "incremental", "snapshot", "backfill"] | None = None,
            primary_key: list[str] | str | None = None,
            update_key: str | None = None,
            object: str | None = None,
            select: list[str] | None = None,
            where: str | None = None,
            source_options: dict[str, Any] | None = None,
            target_options: dict[str, Any] | None = None,
            cron: str | None = None,
            freshness_hours: tuple[int, int] | None = None,
            max_runtime_seconds: int = 600,
            max_retries: int = 3,
            retry_delay_seconds: int = 30,
            owner: str | None = None,
            consumers: list[Consumer | str] | None = None,
            sla: SLA | None = None,
        ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            """Register a function as a Sling-backed replication asset.

            Decorator that registers a function as a Sling-based data replication
            asset within the Phlo orchestration platform. The decorated function
            receives a ``RuntimeContext`` and may return a dict of Sling overrides
            such as a dynamically resolved ``src_stream`` or partition-specific
            ``where`` clause.

            Args:
                stream_name: Source stream identifier (e.g., "public.users").
                table_name: Target table name in the destination.
                source_conn: Sling source connection name.
                group: Asset group name for organization.
                target_conn: Sling target connection name (optional, auto-resolved).
                mode: Replication mode - "full-refresh", "incremental", "snapshot",
                    or "backfill" (optional, defaults to settings).
                primary_key: Primary key column(s) for merge operations (optional).
                update_key: Update key column for incremental replication (required
                    for incremental mode).
                object: Target object path for file-based destinations (optional).
                select: List of columns to select (optional, empty = all columns).
                where: SQL WHERE clause for source filtering (optional).
                source_options: Additional source-specific Sling options (optional).
                target_options: Additional target-specific Sling options (optional).
                cron: Cron schedule for automatic execution (optional).
                freshness_hours: Data freshness SLA as (warning_hours, error_hours)
                    tuple (optional).
                max_runtime_seconds: Maximum execution time before timeout
                    (default: 600).
                max_retries: Maximum retry attempts on failure (default: 3).
                retry_delay_seconds: Seconds between retry attempts (default: 30).
                owner: Asset owner identifier (optional).
                consumers: List of data consumers (optional).
                sla: Service level agreement definition (optional).

            Returns:
                Decorator function that wraps the user function.

            Example:
                Basic incremental replication::

                    @phlo_sling_replication(
                        stream_name="public.users",
                        table_name="users",
                        source_conn="PHLO_POSTGRES",
                        group="ingestion",
                        mode="incremental",
                        update_key="updated_at",
                    )
                    def replicate_users(context):
                        # Optional: return runtime overrides
                        return {"where": f"updated_at >= '{context.partition_key}'"}

            """
            repl_config = _build_replication_config(
                stream_name=stream_name,
                table_name=table_name,
                source_conn=source_conn,
                group=group,
                target_conn=target_conn,
                mode=mode,
                primary_key=primary_key,
                update_key=update_key,
                object=object,
                select=select,
                where=where,
                source_options=source_options,
                target_options=target_options,
            )

            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                """Wrap a replication source function as a Phlo asset definition."""

                def resolve_overrides(runtime: RuntimeContext) -> dict[str, Any] | None:
                    overrides = func(runtime)
                    return overrides if isinstance(overrides, dict) else None

                _register_sling_asset(
                    repl_config=repl_config,
                    source_func=func,
                    override_resolver=resolve_overrides,
                    description=func.__doc__,
                    owner=owner,
                    consumers=consumers,
                    sla=sla,
                    max_runtime_seconds=max_runtime_seconds,
                    max_retries=max_retries,
                    retry_delay_seconds=retry_delay_seconds,
                    cron=cron,
                    freshness_hours=freshness_hours,
                )
                setattr(func, "_phlo_replication_config", repl_config)
                return func

            return decorator
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;stream_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source stream identifier (e.g., "public.users").
        </PyParameter>

        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target table name in the destination.
        </PyParameter>

        <PyParameter name="&#x22;source_conn&#x22;" type="&#x22;str&#x22;" value="undefined">
          Sling source connection name.
        </PyParameter>

        <PyParameter name="&#x22;group&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset group name for organization.
        </PyParameter>

        <PyParameter name="&#x22;target_conn&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Sling target connection name (optional, auto-resolved).
        </PyParameter>

        <PyParameter name="&#x22;mode&#x22;" type="&#x22;Literal['full-refresh', 'incremental', 'snapshot', 'backfill'] | None&#x22;" value="&#x22;None&#x22;">
          Replication mode - "full-refresh", "incremental", "snapshot",
          or "backfill" (optional, defaults to settings).
        </PyParameter>

        <PyParameter name="&#x22;primary_key&#x22;" type="&#x22;list[str] | str | None&#x22;" value="&#x22;None&#x22;">
          Primary key column(s) for merge operations (optional).
        </PyParameter>

        <PyParameter name="&#x22;update_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Update key column for incremental replication (required
          for incremental mode).
        </PyParameter>

        <PyParameter name="&#x22;object&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Target object path for file-based destinations (optional).
        </PyParameter>

        <PyParameter name="&#x22;select&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
          List of columns to select (optional, empty = all columns).
        </PyParameter>

        <PyParameter name="&#x22;where&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          SQL WHERE clause for source filtering (optional).
        </PyParameter>

        <PyParameter name="&#x22;source_options&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
          Additional source-specific Sling options (optional).
        </PyParameter>

        <PyParameter name="&#x22;target_options&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
          Additional target-specific Sling options (optional).
        </PyParameter>

        <PyParameter name="&#x22;cron&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Cron schedule for automatic execution (optional).
        </PyParameter>

        <PyParameter name="&#x22;freshness_hours&#x22;" type="&#x22;tuple[int, int] | None&#x22;" value="&#x22;None&#x22;">
          Data freshness SLA as (warning\_hours, error\_hours)
          tuple (optional).
        </PyParameter>

        <PyParameter name="&#x22;max_runtime_seconds&#x22;" type="&#x22;int&#x22;" value="&#x22;600&#x22;">
          Maximum execution time before timeout
          (default: 600).
        </PyParameter>

        <PyParameter name="&#x22;max_retries&#x22;" type="&#x22;int&#x22;" value="&#x22;3&#x22;">
          Maximum retry attempts on failure (default: 3).
        </PyParameter>

        <PyParameter name="&#x22;retry_delay_seconds&#x22;" type="&#x22;int&#x22;" value="&#x22;30&#x22;">
          Seconds between retry attempts (default: 30).
        </PyParameter>

        <PyParameter name="&#x22;owner&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Asset owner identifier (optional).
        </PyParameter>

        <PyParameter name="&#x22;consumers&#x22;" type="&#x22;list[Consumer | str] | None&#x22;" value="&#x22;None&#x22;">
          List of data consumers (optional).
        </PyParameter>

        <PyParameter name="&#x22;sla&#x22;" type="&#x22;SLA | None&#x22;" value="&#x22;None&#x22;">
          Service level agreement definition (optional).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
        Decorator function that wraps the user function.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;phlo_sling_assets&#x22;" type="&#x22;(*, group, cron=None, freshness_hours=None, max_runtime_seconds=600, max_retries=3, retry_delay_seconds=30, owner=None, consumers=None, sla=None) -> Callable[[Callable[[], Iterable[SlingReplication]]], Callable[[], Iterable[SlingReplication]]]&#x22;">
      Register multiple Sling-backed assets from a Python discovery function.

      Decorator that runs at definition time to discover and register multiple
      Sling replication assets. The decorated function yields
      `SlingReplication` objects, one per asset to register. This is the
      Python-first API for filesystem scans, schema discovery, and similar
      dynamic asset generation.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Discover and register multiple tables::

        from phlo\_sling import phlo\_sling\_assets, SlingReplication

        @phlo\_sling\_assets(group="ingestion")
        def discover\_all\_tables():
        tables = \["users", "orders", "products"]
        for table in tables:
        yield SlingReplication(
        stream\_name=f"public.\{table}",
        table\_name=table,
        source\_conn="PHLO\_POSTGRES",
        mode="full-refresh",
        )
      </Callout>

      <PySourceCode>
        ```python
        def phlo_sling_assets(
            *,
            group: str,
            cron: str | None = None,
            freshness_hours: tuple[int, int] | None = None,
            max_runtime_seconds: int = 600,
            max_retries: int = 3,
            retry_delay_seconds: int = 30,
            owner: str | None = None,
            consumers: list[Consumer | str] | None = None,
            sla: SLA | None = None,
        ) -> Callable[[Callable[[], Iterable[SlingReplication]]], Callable[[], Iterable[SlingReplication]]]:
            """Register multiple Sling-backed assets from a Python discovery function.

            Decorator that runs at definition time to discover and register multiple
            Sling replication assets. The decorated function yields
            ``SlingReplication`` objects, one per asset to register. This is the
            Python-first API for filesystem scans, schema discovery, and similar
            dynamic asset generation.

            Args:
                group: Default asset group name (can be overridden per-asset).
                cron: Cron schedule for automatic execution (optional).
                freshness_hours: Data freshness SLA as (warning_hours, error_hours)
                    tuple (optional).
                max_runtime_seconds: Maximum execution time before timeout
                    (default: 600).
                max_retries: Maximum retry attempts on failure (default: 3).
                retry_delay_seconds: Seconds between retry attempts (default: 30).
                owner: Default asset owner identifier (can be overridden per-asset).
                consumers: List of data consumers (optional).
                sla: Service level agreement definition (optional).

            Returns:
                Decorator function that processes the discovery function.

            Example:
                Discover and register multiple tables::

                    from phlo_sling import phlo_sling_assets, SlingReplication

                    @phlo_sling_assets(group="ingestion")
                    def discover_all_tables():
                        tables = ["users", "orders", "products"]
                        for table in tables:
                            yield SlingReplication(
                                stream_name=f"public.{table}",
                                table_name=table,
                                source_conn="PHLO_POSTGRES",
                                mode="full-refresh",
                            )

            """

            def decorator(
                func: Callable[[], Iterable[SlingReplication]],
            ) -> Callable[[], Iterable[SlingReplication]]:
                replications = list(func())

                for replication in replications:
                    repl_config = _build_replication_config(
                        stream_name=replication.stream_name,
                        table_name=replication.table_name,
                        source_conn=replication.source_conn,
                        group=replication.group_name or group,
                        target_conn=replication.target_conn,
                        mode=replication.mode,
                        primary_key=replication.primary_key,
                        update_key=replication.update_key,
                        object=replication.object,
                        select=replication.select,
                        where=replication.where,
                        source_options=replication.source_options,
                        target_options=replication.target_options,
                    )

                    _register_sling_asset(
                        repl_config=repl_config,
                        source_func=func,
                        override_resolver=lambda _runtime: None,
                        description=replication.description,
                        owner=replication.owner or owner,
                        consumers=consumers,
                        sla=sla,
                        max_runtime_seconds=max_runtime_seconds,
                        max_retries=max_retries,
                        retry_delay_seconds=retry_delay_seconds,
                        cron=cron,
                        freshness_hours=freshness_hours,
                        extra_metadata=replication.metadata,
                        extra_tags=replication.tags,
                    )

                return func

            return decorator
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;group&#x22;" type="&#x22;str&#x22;" value="undefined">
          Default asset group name (can be overridden per-asset).
        </PyParameter>

        <PyParameter name="&#x22;cron&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Cron schedule for automatic execution (optional).
        </PyParameter>

        <PyParameter name="&#x22;freshness_hours&#x22;" type="&#x22;tuple[int, int] | None&#x22;" value="&#x22;None&#x22;">
          Data freshness SLA as (warning\_hours, error\_hours)
          tuple (optional).
        </PyParameter>

        <PyParameter name="&#x22;max_runtime_seconds&#x22;" type="&#x22;int&#x22;" value="&#x22;600&#x22;">
          Maximum execution time before timeout
          (default: 600).
        </PyParameter>

        <PyParameter name="&#x22;max_retries&#x22;" type="&#x22;int&#x22;" value="&#x22;3&#x22;">
          Maximum retry attempts on failure (default: 3).
        </PyParameter>

        <PyParameter name="&#x22;retry_delay_seconds&#x22;" type="&#x22;int&#x22;" value="&#x22;30&#x22;">
          Seconds between retry attempts (default: 30).
        </PyParameter>

        <PyParameter name="&#x22;owner&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Default asset owner identifier (can be overridden per-asset).
        </PyParameter>

        <PyParameter name="&#x22;consumers&#x22;" type="&#x22;list[Consumer | str] | None&#x22;" value="&#x22;None&#x22;">
          List of data consumers (optional).
        </PyParameter>

        <PyParameter name="&#x22;sla&#x22;" type="&#x22;SLA | None&#x22;" value="&#x22;None&#x22;">
          Service level agreement definition (optional).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.Callable&#x22;">
        Decorator function that processes the discovery function.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
