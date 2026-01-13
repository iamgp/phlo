"""
Phlo API - Backend service exposing phlo internals to Observatory.

This FastAPI service provides endpoints for Observatory to:
- List installed plugins
- Get service status and configuration
- Read phlo.yaml config
"""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

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

# Auto-discover and register Observatory API routers
_OBSERVATORY_ROUTERS = [
    ("trino", "/api/trino"),
    ("iceberg", "/api/iceberg"),
    ("dagster", "/api/dagster"),
    ("nessie", "/api/nessie"),
    ("quality", "/api/quality"),
    ("loki", "/api/loki"),
    ("lineage", "/api/lineage"),
    ("maintenance", "/api/maintenance"),
    ("search", "/api/search"),
]

_OBSERVATORY_ROUTERS_NO_PREFIX = [
    "extensions",
    "extension_settings",
    "settings",
]


def _register_observatory_routers() -> None:
    """Register Observatory API routers if available."""
    # Combine routers with prefix and without prefix into single iterable
    all_routers = [
        *_OBSERVATORY_ROUTERS,
        *((name, None) for name in _OBSERVATORY_ROUTERS_NO_PREFIX),
    ]

    for name, prefix in all_routers:
        try:
            module = importlib.import_module(f"phlo_api.observatory_api.{name}")
            router = getattr(module, "router", None)
            if router:
                if prefix is not None:
                    app.include_router(router, prefix=prefix)
                else:
                    app.include_router(router)
        except ImportError as e:
            logger.debug("Failed to import observatory router %s: %s", name, e)


_register_observatory_routers()


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
def get_plugins() -> dict[str, list[str]]:
    """List all installed plugins by type."""
    try:
        from phlo.discovery import list_plugins

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
        from phlo.discovery import list_plugins

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
        from phlo.discovery import get_plugin_info as _get_plugin_info

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
        from phlo.discovery import ServiceDiscovery

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
        from phlo.discovery import ServiceDiscovery

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
