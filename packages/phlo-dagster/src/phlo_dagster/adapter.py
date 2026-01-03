"""Dagster orchestrator adapter for capability specs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Iterable

import dagster as dg

from phlo.capabilities.runtime import RuntimeContext
from phlo.capabilities.specs import (
    AssetCheckSpec,
    AssetSpec,
    CheckResult,
    MaterializeResult,
    ResourceSpec,
)
from phlo.plugins.base import OrchestratorAdapterPlugin, PluginMetadata


def _asset_key_from_string(key: str) -> dg.AssetKey:
    if "." in key:
        return dg.AssetKey(key.split("."))
    return dg.AssetKey([key])


def _metadata_value(value: Any) -> dg.MetadataValue:
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
    context: dg.AssetExecutionContext

    @property
    def run_id(self) -> str | None:
        return self.context.run_id if hasattr(self.context, "run_id") else None

    @property
    def partition_key(self) -> str | None:
        return self.context.partition_key if self.context.has_partition_key else None

    @property
    def tags(self) -> dict[str, str]:
        return dict(self.context.tags or {})

    @property
    def logger(self) -> Any:
        return self.context.log

    @property
    def resources(self) -> dict[str, Any]:
        resources = getattr(self.context, "resources", None)
        if isinstance(resources, dict):
            return dict(resources)
        return {}

    def get_resource(self, name: str) -> Any:
        return getattr(self.context.resources, name)


class DagsterOrchestratorAdapter(OrchestratorAdapterPlugin):
    """Translate capability specs into Dagster definitions."""

    @property
    def metadata(self) -> PluginMetadata:
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
        resources_map: dict[str, Any] = {}
        for resource in resources:
            value = resource.resource
            if isinstance(value, dg.ResourceDefinition):
                resources_map[resource.name] = value
            else:
                resources_map[resource.name] = dg.ResourceDefinition.hardcoded_resource(value)

        asset_defs = [self._build_asset(spec) for spec in assets if spec.run is not None]
        check_defs = [self._build_check(check) for check in checks if check.fn is not None]

        return dg.Definitions(
            assets=asset_defs,
            asset_checks=check_defs,
            resources=resources_map,
        )

    def _build_asset(self, spec: AssetSpec) -> dg.AssetsDefinition:
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
        def _asset_fn(context: dg.AssetExecutionContext) -> Iterable[Any]:
            runtime = DagsterRuntime(context)
            results = spec.run.fn(runtime) if spec.run else []
            if results is None:
                return
            for result in results:
                if isinstance(result, MaterializeResult):
                    metadata = _convert_metadata(result.metadata)
                    if result.status:
                        metadata.setdefault("status", dg.MetadataValue.text(result.status))
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
        asset_key = _asset_key_from_string(spec.asset_key)
        default_severity = _severity_from_string(spec.severity) or dg.AssetCheckSeverity.ERROR

        @dg.asset_check(
            name=spec.name,
            asset=asset_key,
            blocking=spec.blocking,
            description=spec.description,
        )
        def _check_fn(context: dg.AssetExecutionContext) -> dg.AssetCheckResult:
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
