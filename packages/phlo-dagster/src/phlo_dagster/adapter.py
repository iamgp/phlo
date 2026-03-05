"""Dagster orchestrator adapter for capability specs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Iterable, Mapping

import dagster as dg

from phlo.capabilities.runtime import RuntimeContext, RuntimeRouting, routing_from_context
from phlo.capabilities.specs import (
    AssetCheckSpec,
    AssetSpec,
    CheckResult,
    MaterializeResult,
    ResourceSpec,
)
from phlo.logging import get_logger
from phlo.plugins.base import OrchestratorAdapterPlugin, PluginMetadata

logger = get_logger(__name__)


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


@dataclass(frozen=True)
class DagsterRuntime(RuntimeContext):
    """Runtime context wrapper around ``dagster.AssetExecutionContext``."""

    context: dg.AssetExecutionContext

    @property
    def run_id(self) -> str | None:
        """Return the current Dagster run identifier when available."""
        return self.context.run_id if hasattr(self.context, "run_id") else None

    @property
    def partition_key(self) -> str | None:
        """Return the active partition key for partitioned runs."""
        return self.context.partition_key if self.context.has_partition_key else None

    @property
    def tags(self) -> dict[str, str]:
        """Return run tags from the best available context attribute."""
        direct_tags = getattr(self.context, "tags", None)
        if isinstance(direct_tags, Mapping):
            return {str(key): str(value) for key, value in direct_tags.items()}

        run_tags = getattr(self.context, "run_tags", None)
        if isinstance(run_tags, Mapping):
            return {str(key): str(value) for key, value in run_tags.items()}

        run = getattr(self.context, "run", None)
        run_level_tags = getattr(run, "tags", None) if run is not None else None
        if isinstance(run_level_tags, Mapping):
            return {str(key): str(value) for key, value in run_level_tags.items()}

        return {}

    @property
    def logger(self) -> Any:
        """Expose Dagster logger for capability runtime hooks."""
        return self.context.log

    @property
    def resources(self) -> dict[str, Any]:
        """Return resources as a plain mapping for runtime consumers."""
        resources = getattr(self.context, "resources", None)
        if resources is None:
            return {}
        if isinstance(resources, dict):
            return dict(resources)
        if hasattr(resources, "_asdict"):
            return dict(resources._asdict())
        if hasattr(resources, "__dict__"):
            return {
                name: value for name, value in vars(resources).items() if not name.startswith("_")
            }
        resource_map: dict[str, Any] = {}
        for name in dir(resources):
            if name.startswith("_"):
                continue
            try:
                value = getattr(resources, name)
            except Exception:
                continue
            if callable(value):
                continue
            resource_map[name] = value
        return resource_map

    @property
    def routing(self) -> RuntimeRouting:
        """Return canonical runtime routing information."""
        return routing_from_context(self)

    def get_resource(self, name: str) -> Any:
        """Return a named Dagster resource from execution context.

        Args:
            name: Resource name.

        Returns:
            Resolved resource object.
        """
        return getattr(self.context.resources, name)


class DagsterOrchestratorAdapter(OrchestratorAdapterPlugin):
    """Translate capability specs into Dagster definitions."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata used by capability discovery."""
        return PluginMetadata(
            name="dagster",
            version="0.1.0",
            description="Dagster orchestrator adapter for Phlo capability specs",
        )

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
            runtime = DagsterRuntime(context)
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
