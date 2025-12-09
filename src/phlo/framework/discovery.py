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
except ImportError:
    DbtCliResource = None  # type: ignore

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
    Attempt to generate dbt manifest if it doesn't exist.

    Args:
        dbt_project_path: Path to dbt project directory
        profiles_path: Path to dbt profiles directory

    Returns:
        True if manifest exists or was successfully generated, False otherwise
    """
    import subprocess

    manifest_path = dbt_project_path / "target" / "manifest.json"

    if manifest_path.exists():
        return True

    logger.info(f"dbt manifest not found at {manifest_path}, attempting to generate...")

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
        from typing import Mapping

        from dagster import AssetKey
        from dagster_dbt import DagsterDbtTranslator, dbt_assets

        from phlo.defs.partitions import daily_partition

        # Use generic translator - maps sources to dlt_<name> assets
        class CustomDbtTranslator(DagsterDbtTranslator):
            def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
                resource_type = dbt_resource_props.get("resource_type")
                if resource_type == "source":
                    source_name = dbt_resource_props["source_name"]
                    table_name = dbt_resource_props["name"]
                    if source_name == "dagster_assets":
                        # Convention: dbt sources map to dlt_<table_name> assets
                        return AssetKey([f"dlt_{table_name}"])
                    return super().get_asset_key(dbt_resource_props)
                return AssetKey(dbt_resource_props["name"])

            def get_kinds(self, dbt_resource_props: Mapping[str, Any]) -> set[str]:
                return {"dbt", "trino"}

            def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> dict[str, Any]:
                """Extract column schema from dbt manifest as static definition metadata."""
                from dagster import TableColumn, TableSchema

                columns = dbt_resource_props.get("columns", {})
                if not columns:
                    return {}

                # Build TableSchema from dbt manifest column definitions
                table_columns = [
                    TableColumn(
                        name=col_name,
                        type=col_info.get("data_type", "unknown"),
                        description=col_info.get("description", ""),
                    )
                    for col_name, col_info in columns.items()
                ]

                if not table_columns:
                    return {}

                return {"dagster/column_schema": TableSchema(columns=table_columns)}

            def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str:
                """Derive group from dbt model path or naming convention."""
                model_name = dbt_resource_props["name"]

                # Try to get group from dbt model config/meta
                meta = dbt_resource_props.get("meta", {})
                if "group" in meta:
                    return meta["group"]

                # Try to derive from fqn (folder path)
                fqn = dbt_resource_props.get("fqn", [])
                if len(fqn) > 2:
                    folder = fqn[1]
                    if folder in ("bronze", "silver", "gold", "marts", "staging"):
                        return folder

                # Fallback: group by naming convention
                if model_name.startswith("stg_"):
                    return "bronze"
                if model_name.startswith(("dim_", "fct_")):
                    return "silver"
                if model_name.startswith("mrt_"):
                    return "gold"
                return "transform"

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

    # Auto-discover publishing assets for marts
    publishing_assets = _discover_publishing_assets()
    assets.extend(publishing_assets)

    return assets


def _discover_publishing_assets() -> list[Any]:
    """
    Auto-discover dbt marts and create publishing assets to copy them to Postgres.

    Scans the dbt manifest for models in the 'marts' schema and creates
    a publishing asset that copies them from Iceberg to Postgres.

    Returns:
        List containing publishing asset if marts found, empty list otherwise
    """
    from phlo.config import get_settings

    settings = get_settings()
    dbt_project_path = settings.dbt_project_path
    manifest_path = dbt_project_path / "target" / "manifest.json"

    if not manifest_path.exists():
        logger.debug("No dbt manifest found, skipping publishing assets")
        return []

    try:
        import json

        from dagster import AssetKey, asset

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Find all models in marts schema
        marts_models = []
        for node_id, node in manifest.get("nodes", {}).items():
            if node.get("resource_type") == "model":
                schema = node.get("schema", "")
                if schema == "marts":
                    table_name = node.get("name")
                    marts_models.append(table_name)

        if not marts_models:
            logger.debug("No marts models found in dbt manifest")
            return []

        logger.info(f"Found {len(marts_models)} marts models to publish: {marts_models}")

        # Create asset keys for dependencies
        deps = [AssetKey(name) for name in marts_models]

        @asset(
            name="publish_marts_to_postgres",
            group_name="publishing",
            deps=deps,
            kinds={"trino", "postgres"},
            description=f"Publish {len(marts_models)} mart tables from Iceberg to PostgreSQL for BI",
        )
        def publish_marts_to_postgres(context):
            """Auto-generated publishing asset for dbt marts."""
            from phlo.defs.resources.trino import TrinoResource

            trino = TrinoResource()
            conn = trino.get_connection()
            cursor = conn.cursor()

            total_rows = 0
            published_tables = []

            # Create marts schema in postgres if not exists
            cursor.execute("CREATE SCHEMA IF NOT EXISTS postgres.marts")

            for table_name in marts_models:
                source = f"iceberg.marts.{table_name}"
                target = f"postgres.marts.{table_name}"

                context.log.info(f"Publishing {source} -> {target}")

                try:
                    # Drop and recreate (simple refresh)
                    cursor.execute(f"DROP TABLE IF EXISTS {target}")
                    cursor.execute(f"CREATE TABLE {target} AS SELECT * FROM {source}")

                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {target}")
                    row_count = cursor.fetchone()[0]
                    total_rows += row_count
                    published_tables.append(table_name)

                    context.log.info(f"Published {row_count} rows to {target}")
                except Exception as e:
                    context.log.error(f"Failed to publish {table_name}: {e}")

            cursor.close()
            conn.close()

            return {
                "tables_published": len(published_tables),
                "total_rows": total_rows,
                "tables": published_tables,
            }

        return [publish_marts_to_postgres]

    except Exception as exc:
        logger.error(f"Error creating publishing assets: {exc}", exc_info=True)
        return []


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
