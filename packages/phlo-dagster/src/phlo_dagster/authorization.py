"""Regulated surface adapter for Dagster webserver.

This adapter registers Dagster as a regulated surface with the capability registry
and provides GraphQL operation mapping to canonical actions.

GraphQL Operation Mapping:
    - assetMutation (MaterializeResult) -> asset.execute
    - launchPipelineRun / launchBackfill -> run.execute
    - GraphQL queries (assets, pipelines, runs) -> asset.read / run.read
    - Sensor/schedule mutations -> run.manage
    - Repository queries -> catalog.read

Principal Extraction:
    - Bearer token from Authorization header
    - Canonicalized via EnforcementContext.identity_bridge
    - Service tokens and verified RS256 OIDC tokens only; unsigned user headers are rejected

Route vs Operation Granularity:
    - Route-level (GraphQL endpoint) is a single entry point
    - Operation-level enforcement within the GraphQL request body
    - Operation name + selection set determine the canonical action
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from phlo.capabilities import (
    RegulatedSurfaceSpec,
    register_capability,
)
from phlo.rbac.models import CanonicalAction
from phlo.security.adapters import SurfaceOperation

SURFACE_NAME = "dagster-webserver"
SURFACE_FRAMEWORK = "dagster-graphql"

ACTION_ASSET_READ = CanonicalAction.ASSET_READ.value
ACTION_ASSET_EXECUTE = CanonicalAction.ASSET_EXECUTE.value
ACTION_RUN_READ = "run.read"
ACTION_RUN_EXECUTE = "run.execute"
ACTION_RUN_MANAGE = "run.manage"
ACTION_CATALOG_READ = CanonicalAction.CATALOG_READ.value
ACTION_CATALOG_MANAGE = CanonicalAction.CATALOG_MANAGE.value
ACTION_SERVICE_READ = CanonicalAction.SERVICE_READ.value
ACTION_ADMIN_READ = CanonicalAction.ADMIN_READ.value


@dataclass(frozen=True)
class GraphQLOperationSpec:
    """Exact classification for one or more GraphQL root fields."""

    operation: str
    fields: tuple[str, ...]
    action: str
    resource_type: str
    resource_keys: tuple[str, ...] = ()


_GRAPHQL_OPERATION_SPECS: tuple[GraphQLOperationSpec, ...] = (
    GraphQLOperationSpec(
        "query",
        (
            "assetBackfillPreview",
            "assetCheckExecutions",
            "assetConditionEvaluationForPartition",
            "assetConditionEvaluationRecordsOrError",
            "assetConditionEvaluationsForEvaluationId",
            "assetNodeAdditionalRequiredKeys",
            "assetNodeDefinitionCollisions",
            "assetNodeOrError",
            "assetNodes",
            "assetOrError",
            "assetRecordsOrError",
            "assetsLatestInfo",
            "assetsOrError",
            "autoMaterializeAssetEvaluationsOrError",
            "autoMaterializeEvaluationsForEvaluationId",
            "truePartitionsForAutomationConditionEvaluationNode",
        ),
        ACTION_ASSET_READ,
        "asset",
        ("assetKey", "assetKeyPath"),
    ),
    GraphQLOperationSpec(
        "query",
        (
            "capturedLogs",
            "capturedLogsMetadata",
            "executionPlanOrError",
            "graphOrError",
            "latestDefsStateInfo",
            "logsForRun",
            "partitionBackfillOrError",
            "partitionBackfillsOrError",
            "partitionSetOrError",
            "partitionSetsOrError",
            "pipelineOrError",
            "pipelineRunOrError",
            "pipelineRunsOrError",
            "pipelineSnapshotOrError",
            "runGroupOrError",
            "runIdsOrError",
            "runOrError",
            "runTagKeysOrError",
            "runTagsOrError",
            "runsFeedCountOrError",
            "runsFeedOrError",
            "runsOrError",
        ),
        ACTION_RUN_READ,
        "run",
        (
            "runId",
            "runIds",
            "pipelineName",
            "jobName",
            "repositoryName",
            "repositoryLocationName",
        ),
    ),
    GraphQLOperationSpec(
        "query",
        (
            "instigationStateOrError",
            "instigationStatesOrError",
            "locationStatusesOrError",
            "scheduleOrError",
            "scheduler",
            "schedulesOrError",
            "sensorOrError",
            "sensorsOrError",
            "workspaceLocationEntryOrError",
        ),
        ACTION_SERVICE_READ,
        "service",
        ("repositoryName", "jobName", "pipelineName"),
    ),
    GraphQLOperationSpec(
        "query",
        (
            "allTopLevelResourceDetailsOrError",
            "repositoriesOrError",
            "repositoryOrError",
            "resourcesOrError",
            "workspaceOrError",
        ),
        ACTION_CATALOG_READ,
        "catalog",
        ("repositoryName", "locationName"),
    ),
    GraphQLOperationSpec(
        "query",
        (
            "autoMaterializeTicks",
            "canBulkTerminate",
            "instance",
            "isPipelineConfigValid",
            "permissions",
            "runConfigSchemaOrError",
            "shouldShowNux",
            "test",
            "topLevelResourceDetailsOrError",
            "utilizedEnvVarsOrError",
            "version",
        ),
        ACTION_ADMIN_READ,
        "admin",
    ),
    GraphQLOperationSpec(
        "mutation",
        (
            "cancelPartitionBackfill",
            "deletePipelineRun",
            "deleteRun",
            "freeConcurrencySlots",
            "freeConcurrencySlotsForRun",
            "launchMultipleRuns",
            "launchPartitionBackfill",
            "launchPipelineExecution",
            "launchPipelineReexecution",
            "launchRun",
            "launchRunReexecution",
            "reexecutePartitionBackfill",
            "terminatePipelineExecution",
            "terminateRun",
            "terminateRuns",
        ),
        ACTION_RUN_EXECUTE,
        "run",
        (
            "runId",
            "runIds",
            "pipelineName",
            "jobName",
            "repositoryName",
            "repositoryLocationName",
        ),
    ),
    GraphQLOperationSpec(
        "mutation",
        (
            "addDynamicPartition",
            "deleteConcurrencyLimit",
            "deleteDynamicPartitions",
            "reportAssetCheckEvaluations",
            "reportRunlessAssetEvents",
            "setAutoMaterializePaused",
            "setConcurrencyLimit",
            "wipeAssets",
        ),
        ACTION_ASSET_EXECUTE,
        "asset",
        ("assetKey", "assetKeyPath"),
    ),
    GraphQLOperationSpec(
        "mutation",
        (
            "reloadRepositoryLocation",
            "reloadWorkspace",
        ),
        ACTION_CATALOG_MANAGE,
        "catalog",
        ("repositoryName", "locationName"),
    ),
    GraphQLOperationSpec(
        "mutation",
        (
            "resetSchedule",
            "resetSensor",
            "resumePartitionBackfill",
            "scheduleDryRun",
            "sensorDryRun",
            "shutdownRepositoryLocation",
            "startSchedule",
            "startSensor",
            "stopRunningSchedule",
        ),
        ACTION_RUN_MANAGE,
        "service",
        ("repositoryName", "jobName", "pipelineName"),
    ),
    GraphQLOperationSpec(
        "mutation",
        (
            "logTelemetry",
            "setNuxSeen",
        ),
        ACTION_ADMIN_READ,
        "admin",
    ),
    GraphQLOperationSpec(
        "mutation",
        (
            "setSensorCursor",
            "stopSensor",
        ),
        ACTION_RUN_MANAGE,
        "service",
        ("repositoryName", "jobName", "pipelineName"),
    ),
    GraphQLOperationSpec(
        "subscription",
        ("capturedLogs", "locationStateChangeEvents", "pipelineRunLogs"),
        ACTION_RUN_READ,
        "run",
        ("runId",),
    ),
    GraphQLOperationSpec("query", ("__schema", "__type"), ACTION_ADMIN_READ, "admin"),
)


def _operation_index() -> dict[tuple[str, str], GraphQLOperationSpec]:
    index: dict[tuple[str, str], GraphQLOperationSpec] = {}
    for spec in _GRAPHQL_OPERATION_SPECS:
        for field in spec.fields:
            key = (spec.operation, field)
            if key in index:
                raise RuntimeError(f"Duplicate Dagster GraphQL operation classification: {key}")
            index[key] = spec
    return index


_GRAPHQL_OPERATION_INDEX = _operation_index()


def resolve_graphql_operation(operation: str, field: str) -> GraphQLOperationSpec:
    """Return the exact registry entry for a GraphQL root field."""
    try:
        return _GRAPHQL_OPERATION_INDEX[(operation, field)]
    except KeyError as exc:
        raise RuntimeError(f"Unclassified Dagster GraphQL operation: {operation}.{field}") from exc


def validate_graphql_schema(schema: Any | None = None) -> None:
    """Prove every reachable Dagster root field has one exact classification."""
    if schema is None:
        from dagster_graphql.schema import create_schema

        schema = create_schema().graphql_schema

    for operation in ("query", "mutation", "subscription"):
        root = schema.get_type(operation.capitalize())
        if root is None:
            continue
        actual_fields = set(root.fields)
        classified = {field for kind, field in _GRAPHQL_OPERATION_INDEX if kind == operation}
        missing = sorted(actual_fields - classified)
        extra = sorted(
            classified - actual_fields - ({"__schema", "__type"} if operation == "query" else set())
        )
        if missing or extra:
            raise RuntimeError(
                f"Dagster GraphQL registry mismatch for {operation}: "
                f"missing={missing}, extra={extra}"
            )


class DagsterRegulatedSurfaceAdapter:
    """Regulated surface adapter for Dagster webserver GraphQL API.

    Declares all regulated operations and registers with the capability registry.
    Operations are mapped from GraphQL operation names to canonical actions.
    """

    surface_name: str = SURFACE_NAME
    framework_type: str = SURFACE_FRAMEWORK
    _installed_runtime: Any | None = None

    _OPERATION_MAPPINGS: list[tuple[tuple[str, ...], str, str]] = [
        (spec.fields, spec.action, spec.resource_type) for spec in _GRAPHQL_OPERATION_SPECS
    ]

    def list_operations(self) -> list[SurfaceOperation]:
        """Return all regulated operations exposed by Dagster GraphQL API."""
        seen: set[tuple[str, str]] = set()
        operations: list[SurfaceOperation] = []

        for op_names, action, resource_type in self._OPERATION_MAPPINGS:
            key = (action, resource_type)
            if key in seen:
                continue
            seen.add(key)
            operations.append(
                SurfaceOperation(
                    action=action,
                    resource_type=resource_type,
                    operation_name=f"dagster.{op_names[0]}",
                    resource_id_strategy="graphql_variables",
                    framework_metadata={
                        "graphql_operations": op_names,
                        "surface": SURFACE_NAME,
                    },
                )
            )

        operations.extend(
            [
                SurfaceOperation(
                    action=ACTION_ASSET_READ,
                    resource_type="asset",
                    operation_name="dagster.asset.query",
                ),
                SurfaceOperation(
                    action=ACTION_ASSET_EXECUTE,
                    resource_type="asset",
                    operation_name="dagster.asset.mutate",
                ),
                SurfaceOperation(
                    action=ACTION_RUN_READ,
                    resource_type="run",
                    operation_name="dagster.run.query",
                ),
                SurfaceOperation(
                    action=ACTION_RUN_EXECUTE,
                    resource_type="run",
                    operation_name="dagster.run.launch",
                ),
                SurfaceOperation(
                    action=ACTION_RUN_MANAGE,
                    resource_type="run",
                    operation_name="dagster.run.manage",
                ),
                SurfaceOperation(
                    action=ACTION_CATALOG_READ,
                    resource_type="catalog",
                    operation_name="dagster.catalog.query",
                ),
                SurfaceOperation(
                    action=ACTION_CATALOG_MANAGE,
                    resource_type="catalog",
                    operation_name="dagster.catalog.manage",
                ),
                SurfaceOperation(
                    action=ACTION_SERVICE_READ,
                    resource_type="service",
                    operation_name="dagster.service.query",
                ),
            ]
        )

        return operations

    def is_active(self, runtime: Any) -> bool:
        """Return True if the adapter is installed on the given runtime."""
        if self._installed_runtime is None:
            return False
        return runtime is self._installed_runtime

    def install(self, runtime: Any) -> None:
        """Register Dagster as a regulated surface and track the runtime."""
        if runtime is None:
            raise ValueError(
                "Dagster adapter requires a non-None Dagster webserver instance as runtime"
            )
        self._installed_runtime = runtime
        schema = getattr(runtime, "_graphene_schema", None)
        if schema is not None:
            validate_graphql_schema(schema.graphql_schema)
        spec = RegulatedSurfaceSpec(
            name=SURFACE_NAME,
            provider=self,
            metadata={
                "framework_runtime": SURFACE_FRAMEWORK,
                "entrypoint": "graphql",
            },
        )
        register_capability("regulated_surface", spec)


_adapter: DagsterRegulatedSurfaceAdapter | None = None


def get_adapter() -> DagsterRegulatedSurfaceAdapter:
    """Return the singleton adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = DagsterRegulatedSurfaceAdapter()
    return _adapter
