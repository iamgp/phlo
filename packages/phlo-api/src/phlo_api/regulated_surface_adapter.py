"""Regulated surface adapter for phlo-api.

This adapter registers phlo-api as a regulated surface with the capability registry.
"""

from __future__ import annotations

from typing import Any

from phlo.capabilities import (
    RegulatedSurfaceSpec,
    register_regulated_surface,
)
from phlo.rbac.models import CanonicalAction
from phlo.security.adapters import SurfaceOperation

SURFACE_NAME = "phlo-api"
SURFACE_FRAMEWORK = "fastapi"


class PhloAPIRegulatedSurfaceAdapter:
    """Regulated surface adapter for phlo-api.

    Declares all regulated operations and registers with the capability registry.
    """

    surface_name: str = SURFACE_NAME
    framework_type: str = SURFACE_FRAMEWORK
    _installed_runtime: Any | None = None

    def list_operations(self) -> list[SurfaceOperation]:
        """Return all regulated operations exposed by phlo-api."""
        return [
            SurfaceOperation(
                action=CanonicalAction.DATASET_READ.value,
                resource_type="dataset",
                operation_name="dataset.read",
            ),
            SurfaceOperation(
                action=CanonicalAction.DATASET_QUERY.value,
                resource_type="dataset",
                operation_name="dataset.query",
            ),
            SurfaceOperation(
                action="dataset.write",
                resource_type="dataset",
                operation_name="dataset.write",
            ),
            SurfaceOperation(
                action="dataset.publish",
                resource_type="dataset",
                operation_name="dataset.publish",
            ),
            SurfaceOperation(
                action=CanonicalAction.ASSET_READ.value,
                resource_type="asset",
                operation_name="asset.read",
            ),
            SurfaceOperation(
                action=CanonicalAction.ASSET_EXECUTE.value,
                resource_type="asset",
                operation_name="asset.execute",
            ),
            SurfaceOperation(
                action="asset.approve",
                resource_type="asset",
                operation_name="asset.approve",
            ),
            SurfaceOperation(
                action=CanonicalAction.SERVICE_READ.value,
                resource_type="service",
                operation_name="service.read",
            ),
            SurfaceOperation(
                action=CanonicalAction.SERVICE_MANAGE.value,
                resource_type="service",
                operation_name="service.manage",
            ),
            SurfaceOperation(
                action=CanonicalAction.ADMIN_READ.value,
                resource_type="admin",
                operation_name="admin.read",
            ),
            SurfaceOperation(
                action=CanonicalAction.ADMIN_MANAGE.value,
                resource_type="admin",
                operation_name="admin.manage",
            ),
            SurfaceOperation(
                action="settings.read",
                resource_type="settings",
                operation_name="settings.read",
            ),
            SurfaceOperation(
                action="settings.manage",
                resource_type="settings",
                operation_name="settings.manage",
            ),
            SurfaceOperation(
                action=CanonicalAction.CATALOG_READ.value,
                resource_type="catalog",
                operation_name="catalog.read",
            ),
            SurfaceOperation(
                action=CanonicalAction.CATALOG_MANAGE.value,
                resource_type="catalog",
                operation_name="catalog.manage",
            ),
            SurfaceOperation(
                action="platform_metadata.read",
                resource_type="platform_metadata",
                operation_name="platform_metadata.read",
            ),
            SurfaceOperation(
                action="observability.read",
                resource_type="observability",
                operation_name="observability.read",
            ),
            SurfaceOperation(
                action="maintenance.read",
                resource_type="maintenance",
                operation_name="maintenance.read",
            ),
            SurfaceOperation(
                action="run.read",
                resource_type="run",
                operation_name="run.read",
            ),
            SurfaceOperation(
                action="run.execute",
                resource_type="run",
                operation_name="run.execute",
            ),
            SurfaceOperation(
                action="run.manage",
                resource_type="run",
                operation_name="run.manage",
            ),
            SurfaceOperation(
                action="audit.read",
                resource_type="audit",
                operation_name="audit.read",
            ),
        ]

    def is_active(self, runtime: Any) -> bool:
        """Return True if runtime matches the FastAPI app this adapter is installed on."""
        if self._installed_runtime is None:
            return False
        return runtime is self._installed_runtime

    def install(self, runtime: Any) -> None:
        """Register phlo-api as a regulated surface and track the runtime."""
        if runtime is None:
            raise ValueError("phlo-api adapter requires a non-None FastAPI app as runtime")
        self._installed_runtime = runtime
        spec = RegulatedSurfaceSpec(
            name=SURFACE_NAME,
            provider=self,
            metadata={"framework_runtime": "fastapi"},
        )
        register_regulated_surface(spec)


_adapter: PhloAPIRegulatedSurfaceAdapter | None = None


def get_adapter() -> PhloAPIRegulatedSurfaceAdapter:
    """Return the singleton adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = PhloAPIRegulatedSurfaceAdapter()
    return _adapter
