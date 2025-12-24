"""
Phlo API - Backend service exposing phlo internals to Observatory.

This FastAPI service provides endpoints for Observatory to:
- List installed plugins
- Get service status and configuration
- Read phlo.yaml config
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Phlo API",
    description="Backend API for Phlo Observatory",
    version="0.1.0",
)

# Allow CORS for Observatory
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Observatory API routers
try:
    from phlo.api.observatory_api.dagster import router as dagster_router
    from phlo.api.observatory_api.iceberg import router as iceberg_router
    from phlo.api.observatory_api.lineage import router as lineage_router
    from phlo.api.observatory_api.loki import router as loki_router
    from phlo.api.observatory_api.nessie import router as nessie_router
    from phlo.api.observatory_api.quality import router as quality_router
    from phlo.api.observatory_api.search import router as search_router
    from phlo.api.observatory_api.trino import router as trino_router

    app.include_router(trino_router, prefix="/api/trino")
    app.include_router(iceberg_router, prefix="/api/iceberg")
    app.include_router(dagster_router, prefix="/api/dagster")
    app.include_router(nessie_router, prefix="/api/nessie")
    app.include_router(quality_router, prefix="/api/quality")
    app.include_router(loki_router, prefix="/api/loki")
    app.include_router(lineage_router, prefix="/api/lineage")
    app.include_router(search_router, prefix="/api/search")
except ImportError:
    # Routers not available (minimal install)
    pass


def get_project_path() -> Path:
    """Get the phlo project path from environment or default."""
    project_path = os.environ.get("PHLO_PROJECT_PATH", "/app/project")
    return Path(project_path)


def load_phlo_config() -> dict[str, Any]:
    """Load phlo.yaml configuration."""
    config_path = get_project_path() / "phlo.yaml"
    if not config_path.exists():
        return {"name": "unknown", "description": ""}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    """Get phlo.yaml configuration."""
    return load_phlo_config()


@app.get("/api/plugins")
def get_plugins() -> dict[str, list[dict[str, Any]]]:
    """List all installed plugins by type."""
    try:
        from phlo.plugins.discovery import list_plugins

        return list_plugins()
    except ImportError:
        return {
            "source_connectors": [],
            "quality_checks": [],
            "transformations": [],
            "services": [],
        }


@app.get("/api/plugins/{plugin_type}")
def get_plugins_by_type(plugin_type: str) -> list[str]:
    """List plugins of a specific type."""
    try:
        from phlo.plugins.discovery import list_plugins

        all_plugins = list_plugins()
        if plugin_type not in all_plugins:
            raise HTTPException(status_code=404, detail=f"Unknown plugin type: {plugin_type}")
        return all_plugins[plugin_type]
    except ImportError:
        return []


@app.get("/api/plugins/{plugin_type}/{name}")
def get_plugin_info(plugin_type: str, name: str) -> dict[str, Any]:
    """Get detailed information about a specific plugin."""
    try:
        from phlo.plugins.discovery import get_plugin_info as _get_plugin_info

        info = _get_plugin_info(plugin_type, name)
        if not info:
            raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")
        return info
    except ImportError as e:
        raise HTTPException(status_code=500, detail="Plugin system not available") from e


@app.get("/api/services")
def get_services() -> list[dict[str, Any]]:
    """List all discovered services."""
    try:
        from phlo.services.discovery import ServiceDiscovery

        discovery = ServiceDiscovery()
        services = discovery.discover()
        return [
            {
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "default": s.default,
                "profile": s.profile,
                "core": getattr(s, "core", False),
            }
            for s in services.values()
        ]
    except ImportError:
        return []


@app.get("/api/services/{name}")
def get_service_info(name: str) -> dict[str, Any]:
    """Get detailed information about a specific service."""
    try:
        from phlo.services.discovery import ServiceDiscovery

        discovery = ServiceDiscovery()
        service = discovery.get_service(name)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service not found: {name}")
        return {
            "name": service.name,
            "description": service.description,
            "category": service.category,
            "default": service.default,
            "profile": service.profile,
            "depends_on": service.depends_on,
            "env_vars": service.env_vars,
            "core": getattr(service, "core", False),
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail="Service discovery not available") from e


@app.get("/api/registry")
def get_registry() -> dict[str, Any]:
    """Get the plugin registry (available plugins for installation)."""
    try:
        from phlo.plugins.registry_client import get_registry_data

        return get_registry_data()
    except ImportError:
        return {"plugins": {}}


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "4000"))
    uvicorn.run(app, host=host, port=port)
