"""Observatory extension manifest and asset endpoints."""

from __future__ import annotations

import importlib.metadata
import re
import shutil
import tempfile
from importlib.resources import as_file
from pathlib import Path, PurePosixPath
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from phlo.discovery import discover_plugins, get_global_registry
from phlo.logging import get_logger
from phlo.plugins.base import ObservatoryExtensionPlugin

logger = get_logger(__name__)

router = APIRouter(prefix="/api/observatory", tags=["observatory"])


def _load_extensions() -> list[ObservatoryExtensionPlugin]:
    discover_plugins(plugin_type="observatory_extensions", auto_register=True)
    registry = get_global_registry()
    observatory_version = _get_observatory_version()
    extensions = []
    for name in registry.list_observatory_extensions():
        plugin = registry.get_observatory_extension(name)
        if not plugin:
            continue
        if not _is_compatible(plugin, observatory_version):
            logger.warning(
                "Skipping incompatible Observatory extension: %s",
                plugin.metadata.name,
            )
            continue
        extensions.append(plugin)
    return extensions


def _extension_payload(plugin: ObservatoryExtensionPlugin) -> dict[str, Any]:
    manifest = plugin.get_manifest()
    return {
        "manifest": manifest.model_dump(),
        "assets_base_path": f"/api/observatory/extensions/{plugin.metadata.name}/assets",
    }


def _get_observatory_version() -> str | None:
    try:
        return importlib.metadata.version("phlo-observatory")
    except importlib.metadata.PackageNotFoundError:
        return None


def _parse_version(value: str) -> tuple[int, ...]:
    parts = re.split(r"[.+-]", value)
    numbers: list[int] = []
    for part in parts:
        if not part.isdigit():
            break
        numbers.append(int(part))
    return tuple(numbers) if numbers else (0,)


def _is_compatible(plugin: ObservatoryExtensionPlugin, observatory_version: str | None) -> bool:
    if not observatory_version:
        return True
    manifest = plugin.get_manifest()
    required = manifest.compat.observatory_min
    return _parse_version(observatory_version) >= _parse_version(required)


@router.get("/extensions")
def list_extensions() -> dict[str, list[dict[str, Any]]]:
    """List all installed Observatory extensions."""
    extensions = _load_extensions()
    return {"extensions": [_extension_payload(plugin) for plugin in extensions]}


@router.get("/extensions/{name}")
def get_extension(name: str) -> dict[str, Any]:
    """Get a single Observatory extension manifest."""
    extensions = _load_extensions()
    for plugin in extensions:
        if plugin.metadata.name == name:
            return _extension_payload(plugin)
    raise HTTPException(status_code=404, detail=f"Observatory extension not found: {name}")


def _cleanup_temp_dir(dir_path: Path) -> None:
    """Remove temporary directory and contents after response is sent."""
    try:
        shutil.rmtree(dir_path, ignore_errors=True)
    except Exception:
        pass


@router.get("/extensions/{name}/assets/{asset_path:path}")
def get_extension_asset(name: str, asset_path: str, background_tasks: BackgroundTasks):
    """Serve extension asset files."""
    extensions = _load_extensions()
    plugin = next((p for p in extensions if p.metadata.name == name), None)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Observatory extension not found: {name}")

    if not asset_path:
        raise HTTPException(status_code=404, detail="Asset path required")

    path = PurePosixPath(asset_path)
    if path.is_absolute() or ".." in path.parts:
        raise HTTPException(status_code=400, detail="Invalid asset path")

    asset = plugin.asset_root.joinpath(*path.parts)
    try:
        if not asset.is_file():
            raise HTTPException(status_code=404, detail="Asset not found")
    except (AttributeError, OSError):
        raise HTTPException(status_code=404, detail="Asset not found")

    try:
        with as_file(asset) as resolved:
            temp_dir = Path(tempfile.mkdtemp())
            temp_file = temp_dir / resolved.name
            shutil.copy2(resolved, temp_file)

        background_tasks.add_task(_cleanup_temp_dir, temp_dir)
        return FileResponse(temp_file)
    except Exception as exc:
        logger.exception("Failed to serve extension asset")
        raise HTTPException(status_code=500, detail="Failed to serve asset") from exc
