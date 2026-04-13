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
    - Falls back to dagster user from X-Dagster-User header if no auth provider

Route vs Operation Granularity:
    - Route-level (GraphQL endpoint) is a single entry point
    - Operation-level enforcement within the GraphQL request body
    - Operation name + selection set determine the canonical action
"""

from __future__ import annotations

from typing import Any

from phlo.capabilities import (
    RegulatedSurfaceSpec,
    register_regulated_surface,
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


class DagsterRegulatedSurfaceAdapter:
    """Regulated surface adapter for Dagster webserver GraphQL API.

    Declares all regulated operations and registers with the capability registry.
    Operations are mapped from GraphQL operation names to canonical actions.
    """

    surface_name: str = SURFACE_NAME
    framework_type: str = SURFACE_FRAMEWORK
    _installed_runtime: Any | None = None

    _OPERATION_MAPPINGS: list[tuple[tuple[str, ...], str, str]] = [
        (("assetMutation",), ACTION_ASSET_EXECUTE, "asset"),
        (("launchPipelineRun",), ACTION_RUN_EXECUTE, "run"),
        (("launchBackfill",), ACTION_RUN_EXECUTE, "run"),
        (("terminatePipelineRun",), ACTION_RUN_EXECUTE, "run"),
        (("terminateRun",), ACTION_RUN_EXECUTE, "run"),
        (("deletePipelineRun",), ACTION_RUN_EXECUTE, "run"),
        (("deleteRun",), ACTION_RUN_EXECUTE, "run"),
        (("reloadRepository",), ACTION_CATALOG_MANAGE, "catalog"),
        (("reloadWorkspace",), ACTION_CATALOG_MANAGE, "catalog"),
        (("createSensor",), ACTION_RUN_MANAGE, "run"),
        (("updateSensor",), ACTION_RUN_MANAGE, "run"),
        (("deleteSensor",), ACTION_RUN_MANAGE, "run"),
        (("createSchedule",), ACTION_RUN_MANAGE, "run"),
        (("updateSchedule",), ACTION_RUN_MANAGE, "run"),
        (("deleteSchedule",), ACTION_RUN_MANAGE, "run"),
        (("assets",), ACTION_ASSET_READ, "asset"),
        (("asset",), ACTION_ASSET_READ, "asset"),
        (("assetNodes",), ACTION_ASSET_READ, "asset"),
        (("pipeline",), ACTION_ASSET_READ, "asset"),
        (("pipelines",), ACTION_ASSET_READ, "asset"),
        (("pipelineSnapshot",), ACTION_ASSET_READ, "asset"),
        (("runGroup",), ACTION_RUN_READ, "run"),
        (("runGroups",), ACTION_RUN_READ, "run"),
        (("run",), ACTION_RUN_READ, "run"),
        (("runs",), ACTION_RUN_READ, "run"),
        (("runsOrError",), ACTION_RUN_READ, "run"),
        (("scheduler",), ACTION_SERVICE_READ, "service"),
        (("sensors",), ACTION_SERVICE_READ, "service"),
        (("sensor",), ACTION_SERVICE_READ, "service"),
        (("schedules",), ACTION_SERVICE_READ, "service"),
        (("schedule",), ACTION_SERVICE_READ, "service"),
        (("repository",), ACTION_CATALOG_READ, "catalog"),
        (("workspace",), ACTION_CATALOG_READ, "catalog"),
        (("topResource",), ACTION_ADMIN_READ, "admin"),
        (("version",), ACTION_ADMIN_READ, "admin"),
        (("services",), ACTION_SERVICE_READ, "service"),
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
        spec = RegulatedSurfaceSpec(
            name=SURFACE_NAME,
            provider=self,
            metadata={
                "framework_runtime": SURFACE_FRAMEWORK,
                "entrypoint": "graphql",
            },
        )
        register_regulated_surface(spec)


_adapter: DagsterRegulatedSurfaceAdapter | None = None


def get_adapter() -> DagsterRegulatedSurfaceAdapter:
    """Return the singleton adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = DagsterRegulatedSurfaceAdapter()
    return _adapter
