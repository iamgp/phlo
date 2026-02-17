"""
Phlo API - Backend service exposing phlo internals to Observatory.

This FastAPI service provides endpoints for Observatory to:
- List installed plugins
- Get service status and configuration
- Read phlo.yaml config
"""

from __future__ import annotations

import importlib
import os
from contextlib import suppress
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from phlo.logging import bind_context, clear_context, get_logger

logger = get_logger(__name__, service="phlo-api")

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


@app.middleware("http")
async def bind_request_logging_context(request: Request, call_next: Any) -> Any:
    """Bind per-request correlation fields for structured logging."""
    request_id = request.headers.get("x-request-id") or str(uuid4())
    trace_id = request.headers.get("traceparent") or request.headers.get("x-trace-id")
    bind_context(request_id=request_id, trace_id=trace_id, path=request.url.path, method=request.method)
    try:
        response = await call_next(request)
        response.headers.setdefault("x-request-id", request_id)
        return response
    finally:
        with suppress(Exception):
            clear_context()


def get_project_path() -> Path:
    """Get the phlo project path from environment or default."""
    project_path = os.environ.get("PHLO_PROJECT_PATH", "/app/project")
    return Path(project_path)


def load_phlo_config() -> dict[str, Any]:
    """Load phlo.yaml configuration."""
    config_path = get_project_path() / "phlo.yaml"
    logger.info("phlo_config_load_started", config_path=str(config_path))
    if not config_path.exists():
        fallback_config = {"name": "unknown", "description": ""}
        logger.warning(
            "phlo_config_load_fallback",
            config_path=str(config_path),
            reason="missing_file",
            fallback_name=fallback_config["name"],
        )
        return fallback_config

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception as exc:
        logger.error("phlo_config_load_failed", config_path=str(config_path), error=str(exc))
        raise

    logger.info(
        "phlo_config_load_succeeded",
        config_path=str(config_path),
        key_count=len(config),
        has_name=bool(config.get("name")),
    )
    return config


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    """Get phlo.yaml configuration."""
    logger.info("api_config_get_started")
    return load_phlo_config()


@app.get("/api/plugins")
def get_plugins() -> dict[str, list[str]]:
    """List all installed plugins by type."""
    logger.info("api_plugins_list_started")
    try:
        from phlo.plugins.discovery import list_plugins

        plugins = list_plugins()
        logger.info(
            "api_plugins_list_succeeded",
            plugin_type_count=len(plugins),
            plugin_count=sum(len(items) for items in plugins.values()),
        )
        return plugins
    except ImportError as exc:
        logger.warning("api_plugins_list_failed", error=str(exc))
        fallback_plugins = {
            "source_connectors": [],
            "quality_checks": [],
            "transformations": [],
            "services": [],
        }
        logger.warning(
            "api_plugins_list_fallback",
            plugin_type_count=len(fallback_plugins),
            plugin_count=0,
        )
        return fallback_plugins


@app.get("/api/plugins/{plugin_type}")
def get_plugins_by_type(plugin_type: str) -> list[str]:
    """List plugins of a specific type."""
    logger.info("api_plugins_type_list_started", plugin_type=plugin_type)
    try:
        from phlo.plugins.discovery import list_plugins

        all_plugins = list_plugins()
        if plugin_type not in all_plugins:
            logger.warning("api_plugins_type_list_failed", plugin_type=plugin_type, reason="unknown_plugin_type")
            raise HTTPException(status_code=404, detail=f"Unknown plugin type: {plugin_type}")
        plugins = all_plugins[plugin_type]
        logger.info(
            "api_plugins_type_list_succeeded",
            plugin_type=plugin_type,
            plugin_count=len(plugins),
        )
        return plugins
    except ImportError as exc:
        logger.warning("api_plugins_type_list_failed", plugin_type=plugin_type, error=str(exc))
        logger.warning(
            "api_plugins_type_list_fallback",
            plugin_type=plugin_type,
            plugin_count=0,
        )
        return []


@app.get("/api/plugins/{plugin_type}/{name}")
def get_plugin_info(plugin_type: str, name: str) -> dict[str, Any]:
    """Get detailed information about a specific plugin."""
    logger.info("api_plugin_get_started", plugin_type=plugin_type, plugin_name=name)
    try:
        from phlo.plugins.discovery import get_plugin_info as _get_plugin_info

        info = _get_plugin_info(plugin_type, name)
        if not info:
            logger.warning(
                "api_plugin_get_failed",
                plugin_type=plugin_type,
                plugin_name=name,
                reason="not_found",
            )
            raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")
        logger.info(
            "api_plugin_get_succeeded",
            plugin_type=plugin_type,
            plugin_name=name,
            key_count=len(info),
        )
        return info
    except ImportError as e:
        logger.error("api_plugin_get_failed", plugin_type=plugin_type, plugin_name=name, error=str(e))
        raise HTTPException(status_code=500, detail="Plugin system not available") from e


@app.get("/api/services")
def get_services() -> list[dict[str, Any]]:
    """List all discovered services."""
    logger.info("api_services_list_started")
    try:
        from phlo.plugins.discovery import ServiceDiscovery

        discovery = ServiceDiscovery()
        services = discovery.discover()
        service_list = [
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
        logger.info("api_services_list_succeeded", service_count=len(service_list))
        return service_list
    except ImportError as exc:
        logger.warning("api_services_list_failed", error=str(exc))
        logger.warning("api_services_list_fallback", service_count=0)
        return []


@app.get("/api/services/{name}")
def get_service_info(name: str) -> dict[str, Any]:
    """Get detailed information about a specific service."""
    logger.info("api_service_get_started", service_name=name)
    try:
        from phlo.plugins.discovery import ServiceDiscovery

        discovery = ServiceDiscovery()
        service = discovery.get_service(name)
        if not service:
            logger.warning("api_service_get_failed", service_name=name, reason="not_found")
            raise HTTPException(status_code=404, detail=f"Service not found: {name}")
        service_payload = {
            "name": service.name,
            "description": service.description,
            "category": service.category,
            "default": service.default,
            "profile": service.profile,
            "depends_on": service.depends_on,
            "env_vars": service.env_vars,
            "core": getattr(service, "core", False),
        }
        logger.info(
            "api_service_get_succeeded",
            service_name=name,
            depends_on_count=len(service_payload["depends_on"]),
            env_var_count=len(service_payload["env_vars"]),
        )
        return service_payload
    except ImportError as e:
        logger.error("api_service_get_failed", service_name=name, error=str(e))
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
