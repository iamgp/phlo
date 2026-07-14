"""Core ingestion decorator for DLT-based data pipelines.

This module provides the primary ``@phlo_ingestion`` decorator used to define
DLT-based data ingestion pipelines in Phlo. It handles asset registration,
validation configuration, merge strategy setup, and runtime execution.

Key Functions:
    - :func:`phlo_ingestion`: Main decorator for defining ingestion assets
    - :func:`get_ingestion_assets`: Retrieve all registered ingestion assets
    - :func:`clear_ingestion_assets`: Clear the asset registry

Validation Functions:
    - :func:`_validate_unique_key_in_schema`: Validate unique_key exists in schema
    - :func:`_validate_merge_config`: Validate merge strategy and configuration
    - :func:`_default_merge_config`: Build default merge configuration

Capability Resolution:
    - :func:`_resolve_table_store_capability`: Resolve table-store provider

Registry:
    - ``_INGESTION_ASSETS``: Global list of registered AssetSpec objects

The decorator integrates with Phlo's capability system for table store resolution,
supports Write-Audit-Publish (WAP) patterns with strict validation, and provides
comprehensive Pandera schema validation.

See Also:
    - :mod:`phlo_dlt.executor`: DltIngester implementation
    - :mod:`phlo_dlt.pandera_checks`: Validation logic
    - :mod:`phlo_dlt.registry`: TableConfig definition
    - :mod:`phlo.capabilities`: Capability resolution system

Example:
    ```python
    from phlo_dlt import phlo_ingestion
    from workflows.schemas.raw import UserSchema

    @phlo_ingestion(
        table_name="users",
        unique_key="user_id",
        group="raw",
        validation_schema=UserSchema,
        merge_strategy="merge",
        cron="0 */6 * * *",
        validate=True,
        strict_validation=True,
    )
    def load_users(partition_date: str):
        # Return DLT source or data
        return rest_api_source(...)

    # Get all registered assets
    from phlo_dlt.decorator import get_ingestion_assets
    assets = get_ingestion_assets()
    ```

"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Literal

from phlo.capabilities import (
    AssetCheckSpec,
    AssetSpec,
    MaterializeResult,
    PartitionSpec,
    RunResult,
    RunSpec,
    configured_capability_name,
    list_capabilities,
    resolve_capability,
)
from phlo.contracts import Consumer, SLA, normalize_consumers, serialize_consumers, serialize_sla
from phlo.capabilities.runtime import RuntimeContext, routing_from_context
from phlo.exceptions import PhloConfigError
from phlo.logging import log_event
from phlo_dlt.pandera_checks import (
    PANDERA_CONTRACT_CHECK_NAME,
    PanderaContractEvaluation,
    PanderaContractValidationError,
    deserialize_pandera_contract_evaluation,
    evaluate_pandera_contract_parquet,
    evaluate_pandera_contract_parquet_files,
    pandera_contract_asset_check_result,
)

from phlo_dlt.dlt_helpers import get_branch_from_context, get_write_branch_from_context
from phlo_dlt.registry import TableConfig

_INGESTION_ASSETS: list[AssetSpec] = []


def get_ingestion_assets() -> list[AssetSpec]:
    """Return registered ingestion asset specifications.

    Retrieves a copy of all ingestion assets that have been registered
    via the ``@phlo_ingestion`` decorator. This function is used by
    plugin interfaces and asset discovery systems.

    Returns:
        list[AssetSpec]: A shallow copy of all ingestion assets created
            via ``phlo_ingestion``. Modifying the returned list does not
            affect the internal registry.

    Example:
        ```python
        from phlo_dlt.decorator import get_ingestion_assets

        assets = get_ingestion_assets()
        for asset in assets:
            print(f"Asset key: {asset.key}, Group: {asset.group}")
        ```

    See Also:
        :func:`clear_ingestion_assets`: Clear the asset registry
        :func:`phlo_ingestion`: Decorator that registers assets

    """
    return list(_INGESTION_ASSETS)


def clear_ingestion_assets() -> None:
    """Clear all registered ingestion asset specifications.

    Removes all ingestion assets from the internal registry. This is
    primarily used during testing, plugin reloads, or when dynamically
    reconfiguring the ingestion system.

    Warning:
        This operation is destructive and cannot be undone. Assets
        must be re-registered by re-importing modules with ``@phlo_ingestion``
        decorators.

    Example:
        ```python
        from phlo_dlt.decorator import clear_ingestion_assets, get_ingestion_assets

        # Clear all assets
        clear_ingestion_assets()
        assert len(get_ingestion_assets()) == 0
        ```

    See Also:
        :func:`get_ingestion_assets`: Retrieve registered assets

    """
    _INGESTION_ASSETS.clear()


def _validate_unique_key_in_schema(unique_key: str, schema: type[Any] | None) -> None:
    """Validate that the configured unique key exists in the schema annotations.

    Args:
        unique_key: Column name used to identify unique records.
        schema: Optional schema class used for validation.

    Raises:
        PhloConfigError: If `schema` is provided and `unique_key` is missing.

    """
    if schema is None:
        return
    annotations = getattr(schema, "__annotations__", {})
    if unique_key not in annotations:
        raise PhloConfigError(
            message=f"unique_key '{unique_key}' not found in schema {schema.__name__}",
            suggestions=[
                f"Add `{unique_key}` to {schema.__name__} schema annotations",
                "Or update unique_key to match an existing schema field",
            ],
        )


def _validate_merge_config(
    merge_strategy: str,
    unique_key: str,
    merge_config: dict[str, Any] | None,
) -> None:
    """Validate merge strategy and merge configuration semantics.

    Args:
        merge_strategy: Write strategy for ingestion (`append` or `merge`).
        unique_key: Column name used for deduplication and merge operations.
        merge_config: Optional merge behavior overrides.

    Raises:
        PhloConfigError: If strategy or config values are invalid.

    """
    if merge_strategy not in ("append", "merge"):
        raise PhloConfigError(
            message=f"Invalid merge_strategy: {merge_strategy}",
            suggestions=["Use merge_strategy='append' or merge_strategy='merge'"],
        )

    if merge_config is None:
        return

    if not isinstance(merge_config, dict):
        raise PhloConfigError(
            message="merge_config must be a dict",
            suggestions=["Pass merge_config={'deduplication': True, ...}"],
        )

    if merge_config.get("deduplication") and not unique_key:
        raise PhloConfigError(
            message="deduplication requires a unique_key",
            suggestions=["Set unique_key parameter to a valid column name"],
        )


def _default_merge_config(
    merge_strategy: str,
    merge_config: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build merge configuration defaults for the selected strategy.

    Args:
        merge_strategy: Write strategy for ingestion (`append` or `merge`).
        merge_config: Optional user-provided merge configuration.

    Returns:
        Effective merge configuration with strategy defaults applied.

    """
    config = merge_config.copy() if merge_config else {}

    if merge_strategy == "append":
        config.setdefault("deduplication", False)
    elif merge_strategy == "merge":
        config.setdefault("deduplication", True)
        config.setdefault("deduplication_method", "last")

    return config


def _resolve_table_store_capability(context: RuntimeContext) -> tuple[Any, str]:
    """Resolve the effective table-store capability for an ingestion run.

    Queries the Phlo capability system to find an appropriate table store
    provider for the current runtime context. Supports multiple provider
    types (e.g., Iceberg, Delta) and handles configuration errors.

    Resolution Order:
        1. Check capability overrides in runtime context
        2. Check PHLO_DEFAULT_CAPABILITIES environment variable
        3. Use default from capability registry

    Args:
        context: Runtime context with capability configuration.

    Returns:
        tuple[Any, str]: Tuple of (provider_instance, provider_name).

    Raises:
        PhloConfigError: If the configured provider is not installed,
            if multiple providers are available but none selected,
            or if no providers are installed.

    Example:
        ```python
        from phlo_dlt.decorator import _resolve_table_store_capability
        from phlo.capabilities.runtime import RuntimeContext

        context = RuntimeContext(...)
        store, name = _resolve_table_store_capability(context)
        print(f"Using table store: {name}")
        ```

    See Also:
        :mod:`phlo.capabilities`: Capability resolution system
        :func:`phlo.capabilities.resolve_capability`: Core resolution logic

    """
    from phlo.capabilities.discovery import discover_capabilities

    discover_capabilities()
    resolution = resolve_capability("table_store", runtime=context)
    if resolution is not None:
        return resolution.provider, resolution.name

    available = list_capabilities("table_store")
    configured_name = configured_capability_name("table_store", runtime=context)
    if configured_name:
        raise PhloConfigError(
            message=f"Configured table_store '{configured_name}' is not installed",
            suggestions=[
                f"Install the '{configured_name}' table_store provider",
                f"Or update PHLO_DEFAULT_CAPABILITIES / phlo/capability/table_store to one of: {available}",
            ],
        )
    if available:
        raise PhloConfigError(
            message="Multiple table_store providers are installed but none was selected",
            suggestions=[
                f'Set PHLO_DEFAULT_CAPABILITIES={{"table_store": "{available[0]}"}}',
                "Or set workflow tag phlo/capability/table_store=<provider>",
                'Or set asset capability_overrides={"table_store": "<provider>"}',
            ],
        )
    raise PhloConfigError(
        message="No table_store capability is installed",
        suggestions=["Install a table-store provider such as phlo-iceberg or phlo-delta"],
    )


def phlo_ingestion(
    table_name: str,
    unique_key: str,
    group: str,
    validation_schema: type[Any] | None = None,
    table_schema: Any | None = None,
    partition_spec: Any | None = None,
    cron: str | None = None,
    freshness_hours: tuple[int, int] | None = None,
    max_runtime_seconds: int = 300,
    max_retries: int = 3,
    retry_delay_seconds: int = 30,
    validate: bool = True,
    strict_validation: bool = True,
    merge_strategy: Literal["append", "merge"] = "merge",
    merge_config: dict[str, Any] | None = None,
    add_metadata_columns: bool = True,
    owner: str | None = None,
    consumers: list[Consumer | str] | None = None,
    sla: SLA | None = None,
    capabilities: dict[str, str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a function as a DLT-backed ingestion asset.

    This is the primary decorator for defining data ingestion pipelines in Phlo.
    It wraps a source function that returns DLT-compatible data and creates a
    fully configured ingestion asset with validation, scheduling, and table store
    integration.

    Asset Naming:
        The generated asset key is ``dlt_{table_name}``. For example, a table
        named "users" becomes asset key "dlt_users".

    Execution Flow:
        1. Call the decorated function to get DLT source/data
        2. Stage data to Parquet via DLT
        3. Inject metadata columns (_phlo_row_id, _phlo_ingested_at, etc.)
        4. Validate against Pandera schema (if enabled)
        5. Load to table store via merge or append strategy
        6. Emit results and check results

    Validation Modes:
        - ``validate=True, strict_validation=False``: Run checks, log failures,
          but allow the run to succeed (non-blocking)
        - ``validate=True, strict_validation=True``: Run checks, fail the run
          on validation errors (blocking, enables WAP pattern)
        - ``validate=False``: Skip validation entirely

    Args:
        table_name: Destination table-store table name (without ``dlt_`` prefix).
            This is used for both the asset key and the physical table name.
        unique_key: Column used for deduplication and merge operations.
            Must exist in the validation_schema if one is provided.
        group: Dagster/asset group name for organizing related assets.
        validation_schema: Optional Pandera DataFrameModel for data contract checks.
            If provided, data will be validated against this schema.
        table_schema: Optional explicit table-store schema. If not provided,
            the table_store provider will derive schema from validation_schema.
        partition_spec: Optional partition specification for the table store.
            Format depends on the table store provider (e.g., Iceberg transforms).
        cron: Optional cron schedule for automated runs (e.g., "0 */6 * * *" for every 6 hours).
        freshness_hours: Optional freshness policy as (warning_hours, error_hours) tuple.
            Used for SLA monitoring and alerting.
        max_runtime_seconds: Maximum runtime before timeout (default: 300 seconds).
        max_retries: Maximum retry attempts for failed runs (default: 3).
        retry_delay_seconds: Delay between retries in seconds (default: 30).
        validate: Whether to execute Pandera contract checks (default: True).
        strict_validation: Whether failed validation should fail the run (default: True).
            When True, enables Write-Audit-Publish pattern with isolated branches.
        merge_strategy: Ingestion write strategy:
            - ``"append"``: Insert-only, never update existing rows
            - ``"merge"``: Upsert based on unique_key (default)
        merge_config: Optional merge behavior overrides as a dict.
            Common options: ``{"deduplication": True, "deduplication_method": "last"}``
        add_metadata_columns: Whether to inject Phlo metadata columns (default: True).
            Columns added: _phlo_row_id, _phlo_ingested_at, _phlo_partition_date, _phlo_run_id
        owner: Optional asset owner/team identifier for governance.
        consumers: Optional list of downstream consumers (strings or Consumer objects)
            for lineage and impact analysis.
        sla: Optional SLA metadata for freshness/quality alerting.
        capabilities: Optional capability provider overrides for this asset.
            Format: ``{"table_store": "iceberg", "catalog": "nessie"}``

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: A decorator that
        registers the ingestion asset and returns the original function unchanged.

    Raises:
        PhloConfigError: If schema is missing, unique_key not found in schema,
            merge_strategy is invalid, or merge_config is malformed.

    Example:
        Basic usage with REST API source:

        ```python
        from phlo_dlt import phlo_ingestion
        from dlt.sources.rest_api import rest_api
        from workflows.schemas.raw import UserSchema

        @phlo_ingestion(
            table_name="users",
            unique_key="id",
            group="raw",
            validation_schema=UserSchema,
            cron="0 */6 * * *",
            freshness_hours=(6, 24),
        )
        def load_users(partition_date: str):
            return rest_api(
                client={"base_url": "https://api.example.com"},
                resources=[{
                    "name": "users",
                    "endpoint": {
                        "path": "/users",
                        "params": {"date": partition_date},
                    },
                }],
            )
        ```

        With custom table schema and merge configuration:

        ```python
        from pyiceberg.schema import Schema
        from pyiceberg.types import LongType, StringType

        custom_schema = Schema(
            NestedField(1, "id", LongType(), required=True),
            NestedField(2, "name", StringType(), required=False),
        )

        @phlo_ingestion(
            table_name="products",
            unique_key="sku",
            group="inventory",
            table_schema=custom_schema,
            merge_strategy="merge",
            merge_config={"deduplication": True, "deduplication_method": "last"},
            validate=False,  # Skip validation, trust the source
        )
        def load_products(partition_date: str):
            return fetch_products_from_warehouse(partition_date)
        ```

        With consumers and SLA for governance:

        ```python
        from phlo import Consumer, SLA

        @phlo_ingestion(
            table_name="orders",
            unique_key="order_id",
            group="commerce",
            validation_schema=OrderSchema,
            owner="data-platform",
            consumers=[
                Consumer(name="analytics", contact="analytics@company.com"),
                "finance-team",
            ],
            sla=SLA(
                freshness_hours=(1, 4),
                quality_checks=["null_check", "freshness_check"],
            ),
        )
        def load_orders(partition_date: str):
            return fetch_orders(partition_date)
        ```

    See Also:
        :func:`get_ingestion_assets`: Retrieve all registered ingestion assets
        :mod:`phlo_dlt.executor`: DltIngester implementation
        :mod:`phlo_dlt.registry`: TableConfig definition
        :mod:`phlo.contracts`: Consumer and SLA classes

    """
    _validate_unique_key_in_schema(unique_key, validation_schema)
    _validate_merge_config(merge_strategy, unique_key, merge_config)

    merge_cfg = _default_merge_config(merge_strategy, merge_config)

    if table_schema is None and validation_schema is None:
        raise PhloConfigError(
            message="Missing required schema parameter",
            suggestions=[
                "Add validation_schema for provider-driven schema derivation",
                "Or add explicit table_schema parameter: table_schema=<Schema>(...)",
            ],
        )

    table_config = TableConfig(
        table_name=table_name,
        table_schema=table_schema,
        validation_schema=validation_schema,
        unique_key=unique_key,
        group_name=group,
        partition_spec=partition_spec,
    )
    normalized_consumers = normalize_consumers(consumers)

    def decorator(func: Callable[..., Any]) -> Any:
        """Wrap an ingestion source function as a Phlo asset definition.

        This inner function is the actual decorator that processes the user's
        source function and registers it as a Phlo asset. It creates the
        AssetSpec with all configuration and adds it to the global registry.

        Args:
            func: The user's source function that returns DLT-compatible data.
                Must accept ``partition_date: str`` as a parameter.

        Returns:
            Any: The original function with an added ``_phlo_table_config`` attribute.

        Side Effects:
            - Creates AssetCheckSpec if validation is enabled
            - Appends AssetSpec to ``_INGESTION_ASSETS`` registry
            - Sets ``func._phlo_table_config`` attribute

        Note:
            The returned function is unmodified in behavior but carries metadata
            used by the plugin system and executor.

        """
        check_specs: list[AssetCheckSpec] = []
        if validate and table_config.validation_schema is not None:
            check_specs = [
                AssetCheckSpec(
                    name=PANDERA_CONTRACT_CHECK_NAME,
                    asset_key=f"dlt_{table_config.table_name}",
                    blocking=bool(strict_validation),
                    description=f"Pandera schema contract for {table_config.table_name}",
                )
            ]

        def run(runtime: RuntimeContext) -> Iterator[RunResult]:
            """Execute one partitioned ingestion run for the wrapped source function.

            This inner function is the actual asset execution logic called by the
            Phlo orchestrator (e.g., Dagster) when the asset is materialized. It
            orchestrates the full ingestion flow:

            Execution Steps:
                1. Validate partition key exists
                2. Resolve target and write branches (handles WAP pattern)
                3. Log run start with context
                4. Call user function to get DLT source
                5. Handle no-data case (yield no_data result)
                6. Stage data to Parquet via DltIngester
                7. Run Pandera validation if enabled
                8. Merge to table store
                9. Yield MaterializeResult or CheckResult objects

            Args:
                runtime: RuntimeContext with partition_key, run_id, logger,
                    and other execution context.

            Yields:
                RunResult: Either CheckResult (for validation) or MaterializeResult
                (for data loads). Multiple results may be yielded in a single run.

            Raises:
                PhloConfigError: If partition key is missing.
                RuntimeError: If strict validation fails.
                PanderaContractValidationError: If validation fails in strict mode.
                Exception: Any other error is logged and re-raised for orchestrator handling.

            WAP Pattern:
                When ``strict_validation=True``, writes go to an isolated branch
                (``write_branch_name``) which may differ from the target branch.
                Validation passes before data is visible on the target branch.

            Example:
                This function is called internally by the orchestrator:

                ```python
                # In Dagster/opencda, this happens:
                for result in asset_spec.run.fn(runtime_context):
                    yield result
                ```

            See Also:
                :class:`phlo_dlt.executor.DltIngester`: Core execution engine
                :mod:`phlo_dlt.pandera_checks`: Validation logic
                :func:`phlo_dlt.dlt_helpers.get_write_branch_from_context`: WAP handling

            """
            partition_date = runtime.partition_key
            if not partition_date:
                raise PhloConfigError(
                    message="Missing partition key for ingestion asset",
                    suggestions=["Run the asset with a partition key (YYYY-MM-DD)."],
                )

            branch_name = get_branch_from_context(runtime)
            write_branch_name = get_write_branch_from_context(
                runtime,
                strict_validation=strict_validation,
            )
            routing = routing_from_context(runtime)
            run_id = routing.run_id or "unknown"
            project_id = routing.project_id
            attempt = routing.attempt
            logger = runtime.logger

            log_event(logger, "info", "starting_ingestion", partition_date=partition_date)
            log_event(logger, "info", "ingesting_to_branch", branch_name=branch_name)
            if write_branch_name != branch_name:
                log_event(
                    logger,
                    "info",
                    "ingesting_to_isolated_branch",
                    target_branch_name=branch_name,
                    write_branch_name=write_branch_name,
                )
            log_event(
                logger, "info", "target_table_selected", table_name=table_config.full_table_name
            )

            logger.info("Calling user function to get DLT source...")
            try:
                from phlo_dlt.executor import DltIngester

                table_store, table_store_name = _resolve_table_store_capability(runtime)

                ingester = DltIngester(
                    context=runtime,
                    logger=logger,
                    table_config=table_config,
                    table_store_resource=table_store,
                    dlt_source_func=func,
                    validation_schema=table_config.validation_schema,
                    validate=validate,
                    strict_validation=strict_validation,
                    add_metadata_columns=add_metadata_columns,
                    merge_strategy=merge_strategy,
                    merge_config=merge_cfg,
                )
                log_event(
                    logger, "info", "target_table_store_selected", table_store=table_store_name
                )

                result = ingester.run_ingestion(
                    partition_key=partition_date,
                    parameters={
                        "branch_name": write_branch_name,
                        "target_branch_name": branch_name,
                        "run_id": run_id,
                        "project_id": project_id,
                        "attempt": attempt,
                    },
                )

                if result.status == "no_data":
                    if validate and table_config.validation_schema is not None:
                        evaluation = PanderaContractEvaluation(
                            passed=True,
                            failed_count=0,
                            total_count=0,
                            sample=[],
                            error=None,
                        )
                        check_result = pandera_contract_asset_check_result(
                            evaluation,
                            partition_key=partition_date,
                            asset_key=f"dlt_{table_config.table_name}",
                            schema_class=table_config.validation_schema,
                            query_or_sql="status:no_data",
                        )
                        yield check_result
                    yield MaterializeResult(
                        metadata={
                            "branch": branch_name,
                            "write_branch": write_branch_name,
                            "partition_date": partition_date,
                            "rows_loaded": 0,
                            "status": "no_data",
                        },
                        status="no_data",
                    )
                    return

                if validate and table_config.validation_schema is not None:
                    validation_schema = table_config.validation_schema
                    parquet_paths_raw = result.metadata.get("parquet_paths")
                    if isinstance(parquet_paths_raw, list):
                        parquet_paths = [Path(str(path)) for path in parquet_paths_raw]
                    else:
                        parquet_path = result.metadata.get("parquet_path")
                        parquet_paths = [Path(str(parquet_path))] if parquet_path else []
                    primary_parquet_path = parquet_paths[0] if parquet_paths else None
                    query_or_sql = (
                        ",".join(f"parquet://{parquet_path}" for parquet_path in parquet_paths)
                        if parquet_paths
                        else "parquet://<missing>"
                    )
                    log_event(
                        logger,
                        "info",
                        "pandera_contract_evaluation_started",
                        table_name=table_config.full_table_name,
                        partition_date=partition_date,
                        parquet_path=str(primary_parquet_path)
                        if primary_parquet_path is not None
                        else None,
                        parquet_path_count=len(parquet_paths),
                    )
                    try:
                        evaluation = deserialize_pandera_contract_evaluation(
                            result.metadata.get("pandera_evaluation")
                        )
                        if evaluation is None:
                            if len(parquet_paths) == 1:
                                assert primary_parquet_path is not None
                                evaluation = evaluate_pandera_contract_parquet(
                                    primary_parquet_path,
                                    schema_class=validation_schema,
                                )
                            else:
                                evaluation = evaluate_pandera_contract_parquet_files(
                                    parquet_paths,
                                    schema_class=validation_schema,
                                )
                        if evaluation.passed:
                            log_event(
                                logger,
                                "info",
                                "pandera_contract_evaluation_passed",
                                table_name=table_config.full_table_name,
                                partition_date=partition_date,
                                parquet_path=str(primary_parquet_path)
                                if primary_parquet_path is not None
                                else None,
                                parquet_path_count=len(parquet_paths),
                                total_count=evaluation.total_count,
                                failed_count=evaluation.failed_count,
                            )
                        else:
                            log_event(
                                logger,
                                "warning",
                                "pandera_contract_evaluation_failed",
                                table_name=table_config.full_table_name,
                                partition_date=partition_date,
                                parquet_path=str(primary_parquet_path)
                                if primary_parquet_path is not None
                                else None,
                                parquet_path_count=len(parquet_paths),
                                total_count=evaluation.total_count,
                                failed_count=evaluation.failed_count,
                                error=evaluation.error,
                            )
                    except Exception as exc:
                        log_event(
                            logger,
                            "error",
                            "pandera_contract_evaluation_failed",
                            table_name=table_config.full_table_name,
                            partition_date=partition_date,
                            parquet_path=str(primary_parquet_path)
                            if primary_parquet_path is not None
                            else None,
                            parquet_path_count=len(parquet_paths),
                            error=str(exc),
                        )
                        logger.exception("pandera_contract_evaluation_exception")
                        evaluation = PanderaContractEvaluation(
                            passed=False,
                            failed_count=1,
                            total_count=0,
                            sample=[{"error": str(exc)}],
                            error=str(exc),
                        )
                    check_result = pandera_contract_asset_check_result(
                        evaluation,
                        partition_key=partition_date,
                        asset_key=f"dlt_{table_config.table_name}",
                        schema_class=validation_schema,
                        query_or_sql=query_or_sql,
                    )
                    yield check_result
                    if strict_validation and not evaluation.passed:
                        raise RuntimeError("Pandera contract validation failed")

                yield MaterializeResult(
                    metadata={
                        "branch": branch_name,
                        "write_branch": write_branch_name,
                        "partition_date": partition_date,
                        "rows_inserted": result.rows_inserted,
                        "rows_deleted": result.rows_deleted,
                        "unique_key": table_config.unique_key,
                        "table_name": table_config.full_table_name,
                        "table_store": table_store_name,
                        "dlt_elapsed_seconds": result.metadata.get("dlt_elapsed_seconds", 0.0),
                        "total_elapsed_seconds": result.metadata.get("total_elapsed_seconds", 0.0),
                    },
                    status=result.status,
                )

            except PanderaContractValidationError as exc:
                validation_schema = table_config.validation_schema
                assert validation_schema is not None
                query_or_sql = ",".join(
                    f"parquet://{parquet_path}" for parquet_path in exc.parquet_paths
                )
                yield pandera_contract_asset_check_result(
                    exc.evaluation,
                    partition_key=partition_date,
                    asset_key=f"dlt_{table_config.table_name}",
                    schema_class=validation_schema,
                    query_or_sql=query_or_sql,
                )
                raise RuntimeError("Pandera contract validation failed") from exc
            except Exception:
                raise

        asset_spec = AssetSpec(
            key=f"dlt_{table_config.table_name}",
            group=group,
            description=func.__doc__ or f"Ingests {table_config.table_name} data to table_store",
            kinds={"dlt", "table_store"},
            tags={"provider": "dlt", "asset_type": "ingestion", "source": "dlt"},
            metadata={
                "provider": "dlt",
                "asset_type": "ingestion",
                "source_name": getattr(func, "__name__", table_config.table_name),
                "table_name": table_config.table_name,
                "write_mode": merge_strategy,
                "primary_key": [unique_key] if isinstance(unique_key, str) else list(unique_key),
                "schema_ref": getattr(table_config.validation_schema, "__name__", None),
                "quality_provider": "pandera"
                if validate and table_config.validation_schema is not None
                else None,
                "unique_key": table_config.unique_key,
                "group": table_config.group_name,
                "owner": owner,
                "consumers": serialize_consumers(normalized_consumers),
                "sla": serialize_sla(sla),
            },
            partitions=PartitionSpec(kind="daily"),
            capability_overrides=dict(capabilities or {}),
            run=RunSpec(
                fn=run,
                max_runtime_seconds=max_runtime_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                cron=cron,
                freshness_hours=freshness_hours,
            ),
            checks=check_specs,
        )

        _INGESTION_ASSETS.append(asset_spec)
        setattr(func, "_phlo_table_config", table_config)
        return func

    return decorator
