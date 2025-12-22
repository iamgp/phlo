"""
User Workflow Discovery

This module discovers and loads workflow files from a user's project directory.
It dynamically imports Python modules which triggers decorator registration,
then collects all registered assets, jobs, and schedules.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

from dagster import Definitions

try:
    from dagster_dbt import DbtCliResource
except Exception:  # pragma: no cover - optional dependency for user workflows
    DbtCliResource = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


def discover_user_workflows(
    workflows_path: Path | str,
    clear_registries: bool = False,
) -> Definitions:
    """
    Discover and load user workflow files from a directory.

    This function scans the workflows directory for Python files, imports them
    (which triggers @phlo_ingestion and @phlo_quality decorator registration),
    and collects all registered Dagster assets and checks.

    Args:
        workflows_path: Path to workflows directory (e.g., "./workflows")
        clear_registries: Whether to clear asset registries before discovery
            (default: False). Set to True for testing.

    Returns:
        Dagster Definitions containing all discovered workflows

    Example:
        ```python
        # Discover workflows in ./workflows directory
        user_defs = discover_user_workflows(Path("./workflows"))

        # Merge with core definitions
        all_defs = Definitions.merge(core_defs, user_defs)
        ```

    Raises:
        FileNotFoundError: If workflows_path doesn't exist
        ImportError: If workflow modules fail to import
    """
    workflows_path = Path(workflows_path)

    if not workflows_path.exists():
        logger.warning(
            "Workflows directory not found: %s. No user workflows will be loaded.",
            workflows_path,
        )
        return Definitions()

    if not workflows_path.is_dir():
        raise ValueError(f"Workflows path must be a directory, got: {workflows_path}")

    logger.info(f"Discovering user workflows in: {workflows_path}")

    # Optionally clear registries (useful for testing)
    if clear_registries:
        _clear_asset_registries()

    # Add parent directory to Python path so imports work
    parent_dir = workflows_path.parent.resolve()
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
        logger.debug(f"Added to Python path: {parent_dir}")

    # Import all workflow modules
    imported_modules = _import_workflow_modules(workflows_path)

    logger.info(f"Imported {len(imported_modules)} workflow modules from {workflows_path}")

    # Collect registered assets from decorators
    collected_assets = _collect_registered_assets()

    logger.info(f"Discovered {len(collected_assets)} assets from user workflows")

    return Definitions(assets=collected_assets)


def _import_workflow_modules(workflows_path: Path) -> list[Any]:
    """
    Import all Python modules in workflows directory.

    Args:
        workflows_path: Path to workflows directory

    Returns:
        List of imported module objects
    """
    imported_modules = []

    # Find all Python files
    py_files = list(workflows_path.rglob("*.py"))

    for py_file in py_files:
        # Skip __init__.py and files starting with underscore
        if py_file.name.startswith("_"):
            continue

        try:
            # Convert file path to module name
            # e.g., workflows/ingestion/weather/observations.py
            #    -> workflows.ingestion.weather.observations
            relative_path = py_file.relative_to(workflows_path.parent)
            module_name = str(relative_path.with_suffix("")).replace("/", ".")

            logger.debug(f"Importing workflow module: {module_name}")

            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load spec for: {py_file}")
                continue

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            imported_modules.append(module)
            logger.debug(f"Successfully imported: {module_name}")

        except Exception as exc:
            logger.error(
                f"Failed to import workflow module {py_file}: {exc}",
                exc_info=True,
            )
            # Continue with other modules rather than failing completely
            continue

    return imported_modules


def _ensure_dbt_manifest(dbt_project_path: Path, profiles_path: Path) -> bool:
    """
    Ensure a dbt manifest exists and is up-to-date.

    Args:
        dbt_project_path: Path to dbt project directory
        profiles_path: Path to dbt profiles directory

    Returns:
        True if manifest exists or was successfully generated, False otherwise
    """
    import subprocess

    manifest_path = dbt_project_path / "target" / "manifest.json"

    def _latest_project_mtime() -> float:
        candidates: list[Path] = [
            dbt_project_path / "dbt_project.yml",
            dbt_project_path / "packages.yml",
            dbt_project_path / "package-lock.yml",
        ]
        candidate_dirs = [
            dbt_project_path / "models",
            dbt_project_path / "macros",
            dbt_project_path / "seeds",
            dbt_project_path / "snapshots",
            dbt_project_path / "tests",
            dbt_project_path / "analysis",
        ]

        latest = 0.0
        for path in candidates:
            if path.exists():
                latest = max(latest, path.stat().st_mtime)

        for directory in candidate_dirs:
            if not directory.exists():
                continue
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    latest = max(latest, file_path.stat().st_mtime)

        return latest

    needs_compile = not manifest_path.exists()
    if not needs_compile:
        try:
            needs_compile = _latest_project_mtime() > manifest_path.stat().st_mtime
        except OSError:
            needs_compile = True

    if not needs_compile:
        return True

    logger.info("Generating dbt manifest via `dbt compile`...")

    try:
        result = subprocess.run(
            ["dbt", "compile", "--profiles-dir", str(profiles_path)],
            cwd=str(dbt_project_path),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0 and manifest_path.exists():
            logger.info("Successfully generated dbt manifest")
            return True
        else:
            logger.warning(
                f"Failed to generate dbt manifest: {result.stderr}\n"
                "dbt models will not be available as assets. "
                "Run 'dbt compile' manually in transforms/dbt/"
            )
            return False
    except FileNotFoundError:
        logger.warning(
            "dbt command not found. Install dbt to use dbt models as assets.\n"
            "Alternatively, run 'dbt compile' manually in transforms/dbt/"
        )
        return False
    except subprocess.TimeoutExpired:
        logger.warning(
            "dbt compile timed out after 60 seconds. Run 'dbt compile' manually in transforms/dbt/"
        )
        return False
    except Exception as e:
        logger.warning(f"Could not auto-generate dbt manifest: {e}")
        return False


def _discover_dbt_assets() -> list[Any]:
    """
    Discover and create dbt assets if transforms/dbt exists.

    Returns:
        List containing dbt asset definition if found, empty list otherwise
    """
    from phlo.config import get_settings

    settings = get_settings()
    dbt_project_path = settings.dbt_project_path
    dbt_profiles_path = settings.dbt_profiles_path
    manifest_path = dbt_project_path / "target" / "manifest.json"

    if not _ensure_dbt_manifest(dbt_project_path, dbt_profiles_path):
        logger.debug(f"No dbt manifest available at {manifest_path}, skipping dbt assets")
        return []

    try:
        from dagster_dbt import DbtCliResource, dbt_assets

        from phlo.defs.partitions import daily_partition
        from phlo.defs.transform.dbt_translator import CustomDbtTranslator

        @dbt_assets(
            manifest=manifest_path,
            dagster_dbt_translator=CustomDbtTranslator(),
            partitions_def=daily_partition,
        )
        def all_dbt_assets(context, dbt: DbtCliResource):
            import os
            import shutil

            target = context.op_config.get("target") if context.op_config else None
            target = target or "dev"

            build_args = [
                "build",
                "--project-dir",
                str(dbt_project_path),
                "--profiles-dir",
                str(settings.dbt_profiles_path),
                "--target",
                target,
            ]

            if context.has_partition_key:
                partition_date = context.partition_key
                build_args.extend(["--vars", f'{{"partition_date_str": "{partition_date}"}}'])
                context.log.info(f"Running dbt for partition: {partition_date}")

            os.environ.setdefault("TRINO_HOST", settings.trino_host)
            os.environ.setdefault("TRINO_PORT", str(settings.trino_port))

            build_invocation = dbt.cli(build_args, context=context)
            # fetch_column_metadata() automatically queries the warehouse for column schema
            # after each model runs, making it available in Dagster UI and Observatory
            yield from build_invocation.stream().fetch_column_metadata()
            build_invocation.wait()

            docs_args = [
                "docs",
                "generate",
                "--project-dir",
                str(dbt_project_path),
                "--profiles-dir",
                str(settings.dbt_profiles_path),
                "--target",
                target,
            ]
            docs_invocation = dbt.cli(docs_args, context=context).wait()

            default_target_dir = dbt_project_path / "target"
            default_target_dir.mkdir(parents=True, exist_ok=True)

            for artifact in ("manifest.json", "catalog.json", "run_results.json"):
                artifact_path = docs_invocation.target_path / artifact
                if artifact_path.exists():
                    shutil.copy(artifact_path, default_target_dir / artifact)

        logger.info(f"Discovered dbt assets from {manifest_path}")
        return [all_dbt_assets]

    except Exception as exc:
        logger.error(f"Error creating dbt assets: {exc}", exc_info=True)
        return []


def _collect_registered_assets() -> list[Any]:
    """
    Collect all assets registered via decorators and auto-discovered assets.

    Returns:
        List of Dagster asset definitions
    """
    assets = []

    # Collect ingestion assets
    try:
        from phlo.ingestion import get_ingestion_assets

        ingestion_assets = get_ingestion_assets()
        assets.extend(ingestion_assets)
        logger.debug(f"Collected {len(ingestion_assets)} ingestion assets")
    except ImportError:
        logger.warning("Could not import phlo.ingestion.get_ingestion_assets")
    except Exception as exc:
        logger.error(f"Error collecting ingestion assets: {exc}")

    # Auto-discover dbt assets
    dbt_assets = _discover_dbt_assets()
    assets.extend(dbt_assets)

    return assets


def _clear_asset_registries() -> None:
    """
    Clear all asset registries (for testing).

    This clears the global registries that decorators append to,
    allowing fresh discovery in test scenarios.
    """
    try:
        from phlo.ingestion.decorator import _INGESTION_ASSETS

        _INGESTION_ASSETS.clear()
        logger.debug("Cleared ingestion asset registry")
    except ImportError:
        pass


def get_workflows_path_from_config() -> Path:
    """
    Get workflows path from configuration.

    Returns:
        Path to workflows directory from config, or default "workflows"

    Example:
        ```python
        workflows_path = get_workflows_path_from_config()
        defs = discover_user_workflows(workflows_path)
        ```
    """
    try:
        from phlo.config import get_settings

        settings = get_settings()

        # Check if workflows_path attribute exists
        if hasattr(settings, "workflows_path"):
            return Path(settings.workflows_path)

    except Exception as exc:
        logger.warning(f"Could not get workflows_path from config: {exc}")

    # Default fallback
    return Path("workflows")
