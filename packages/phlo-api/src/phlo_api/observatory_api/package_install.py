"""Trusted package installation endpoint for Observatory.

Only packages listed in the trusted Phlo registry may be installed; anything
else is rejected with a 400 before any subprocess runs. The pinned spec is
only honored when it names the registry's own package, and on success import
caches are invalidated so the new distribution is immediately visible.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
from collections.abc import Mapping
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from phlo.infrastructure import load_project_config
from phlo.cli.commands.plugin.install import resolve_install_target
from phlo.plugins import preflight
from phlo.plugins.preflight import PreflightDecision
from phlo.plugins.registry_client import get_registry_data
from phlo_api.api.operation_controls import audit_operation, enforce_rate_limit, require_scope
from phlo_api.observatory_api.observatory_services import (
    load_project_docker_containers,
    load_services,
)

router = APIRouter(tags=["observatory"])


class ObservatoryPackageInstallRequest(BaseModel):
    """Request to install a Phlo package from the trusted registry."""

    package_name: str
    allow_community: bool = False
    override_reason: str | None = None


class ObservatoryPackageInstallResult(BaseModel):
    """Result of a Python package install requested by Observatory."""

    package_name: str
    package_spec: str
    status: Literal["succeeded", "failed", "skipped"]
    message: str
    services: list[str] = Field(default_factory=list)


def _project_root() -> Path:
    return Path(os.environ.get("PHLO_PROJECT_PATH", Path.cwd())).resolve()


def _trusted_registry_service_packages() -> dict[str, dict[str, Any]]:
    try:
        registry = get_registry_data()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Package registry is unavailable.") from exc

    plugins = registry.get("plugins") if isinstance(registry, Mapping) else None
    if not isinstance(plugins, Mapping):
        return {}

    packages: dict[str, dict[str, Any]] = {}
    # Index each plugin under every accepted spelling (plugin name, distribution
    # name, distribution name without the "phlo-" prefix) so requests using any
    # of them resolve to the same trusted entry.
    for name, payload in plugins.items():
        if not isinstance(payload, Mapping):
            continue
        package = str(payload.get("package") or "").strip()
        if not package:
            continue
        normalized = dict(payload)
        normalized["name"] = str(name)
        for key in {str(name), package, package.removeprefix("phlo-")}:
            if key:
                packages[key] = normalized
    return packages


def _uv_project_root() -> Path | None:
    configured = os.environ.get("PHLO_UV_PROJECT") or os.environ.get("UV_PROJECT")
    if configured:
        path = Path(configured).expanduser()
        if (path / "pyproject.toml").exists():
            return path

    for candidate in [_project_root(), Path.cwd(), *Path.cwd().parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return None


def _run_python_package_install(package_spec: str) -> tuple[bool, str]:
    uv = shutil.which("uv")
    if uv is not None:
        project_root = _uv_project_root()
        if project_root is not None:
            # Inside a uv project, add to pyproject/lockfile and install into the
            # active environment so the dependency survives regeneration.
            command = [uv, "add", "--active", package_spec]
            cwd = project_root
        else:
            command = [uv, "pip", "install", package_spec]
            cwd = None
    elif importlib.util.find_spec("pip") is not None:
        command = [sys.executable, "-m", "pip", "install", package_spec]
        cwd = None
    else:
        raise RuntimeError("Neither uv nor pip is available to install packages.")

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    message = (result.stdout or result.stderr or "").strip()
    return result.returncode == 0, message or "Install command completed."


def _load_services():
    project_root = _project_root()
    return load_services(project_root, containers=load_project_docker_containers(project_root))


def _clear_read_model_cache() -> None:
    from phlo_api.observatory_api.observatory import _clear_read_model_cache as clear_cache

    clear_cache()


def _evidence_paths() -> list[Path]:
    """Conformance evidence paths from $PHLO_CONFORMANCE_EVIDENCE."""
    configured = os.environ.get("PHLO_CONFORMANCE_EVIDENCE", "")
    return [Path(part) for part in configured.split(os.pathsep) if part.strip()]


def _preflight_decision(
    registry_entry: Mapping[str, Any],
    request: ObservatoryPackageInstallRequest,
) -> PreflightDecision:
    """Run the shared pure preflight for a registry-resolved candidate.

    The identical decision the CLI enforces before its pip mutation
    (issue #857); a rejection here prevents the Observatory mutation.
    """
    descriptor_data = {
        "type": registry_entry.get("type", "service"),
        "package": registry_entry.get("package", ""),
        "version": registry_entry.get("version", ""),
        "description": registry_entry.get("description", ""),
        "author": registry_entry.get("author", ""),
        "homepage": registry_entry.get("homepage"),
        "tags": list(registry_entry.get("tags", [])),
    }
    override_reason = request.override_reason if request.allow_community else None
    return preflight.evaluate_install_preflight(
        descriptor_data=descriptor_data,
        plugin_name=str(registry_entry.get("name", "")),
        conformance_results=preflight.load_conformance_evidence(_evidence_paths()),
        project_requirements=preflight.read_project_requirements(
            load_project_config(_project_root())
        ),
        override_reason=override_reason,
        legacy_verified=bool(registry_entry.get("verified", False)),
    )


def _install_python_package(
    request: ObservatoryPackageInstallRequest,
) -> ObservatoryPackageInstallResult:
    requested = request.package_name.strip()
    if not requested:
        raise HTTPException(status_code=400, detail="Package name is required.")

    trusted_packages = _trusted_registry_service_packages()
    registry_entry = trusted_packages.get(requested)
    if registry_entry is None:
        raise HTTPException(
            status_code=400,
            detail="Only trusted Phlo packages from the registry can be installed.",
        )

    registry_name = str(registry_entry["name"])
    package_name = str(registry_entry["package"])
    package_spec, _display_name = resolve_install_target(registry_name)
    # The resolver's answer is only trusted when it names the registry's own
    # package; otherwise fall back to installing exactly what the registry
    # pinned, so an unvetted spec can never be substituted.
    if not package_spec.startswith(package_name):
        package_spec = package_name
        version = str(registry_entry.get("version") or "").strip()
        if version:
            package_spec = f"{package_name}=={version}"

    # The shared pure preflight decides before anything is installed; the
    # mutation below is unreachable for rejected candidates (issue #857).
    decision = _preflight_decision(registry_entry, request)
    if not decision.accepted:
        raise HTTPException(
            status_code=400,
            detail="Install rejected by preflight: " + "; ".join(decision.rejection_messages()),
        )

    try:
        succeeded, install_message = _run_python_package_install(package_spec)
    except Exception as exc:
        return ObservatoryPackageInstallResult(
            package_name=package_name,
            package_spec=package_spec,
            status="failed",
            message=f"Install failed: {exc}",
            services=[registry_name],
        )
    if not succeeded:
        return ObservatoryPackageInstallResult(
            package_name=package_name,
            package_spec=package_spec,
            status="failed",
            message=install_message[-500:],
            services=[registry_name],
        )

    # New distributions are on disk but unknown to the running interpreter until
    # the import path caches are refreshed.
    importlib.invalidate_caches()
    _clear_read_model_cache()
    installed_services = [
        service.id
        for service in _load_services()
        if service.metadata.get("package") == package_name
    ]
    message = f"Installed {package_name}. Regenerate the Phlo service stack before starting it."
    if decision.override_rule:
        message += (
            f" Installed under explicit override ({decision.override_rule}): the provider "
            f"remains tier {decision.tier.value}; the override never changes a tier."
        )
    return ObservatoryPackageInstallResult(
        package_name=package_name,
        package_spec=package_spec,
        status="succeeded",
        message=message,
        services=installed_services or [registry_name],
    )


@router.post("/packages/install", response_model=ObservatoryPackageInstallResult)
def post_observatory_package_install(
    request: ObservatoryPackageInstallRequest, http_request: Request
) -> ObservatoryPackageInstallResult:
    """Install a trusted Phlo Python package into the current environment."""
    auth = require_scope(http_request, "admin")
    enforce_rate_limit(auth["subject"], "install_package")
    result = _install_python_package(request)
    audit_operation(
        operation="install_package",
        target=request.package_name,
        dry_run=False,
        auth=auth,
        payload=request.model_dump(mode="json"),
        result=result.model_dump(mode="json"),
    )
    _clear_read_model_cache()
    return result
