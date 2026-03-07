"""OpenMetadata CLI commands."""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console

from phlo.logging import get_logger
from phlo_openmetadata.capabilities import resolve_catalog_scanner
from phlo_openmetadata.dbt_sync import DbtManifestParser
from phlo_openmetadata.nessie_sync import sync_nessie_tables_to_openmetadata
from phlo_openmetadata.openmetadata import OpenMetadataClient
from phlo_openmetadata.settings import get_settings

console = Console()
logger = get_logger(__name__)


@click.group()
def openmetadata():
    """Manage OpenMetadata integration (optional)."""


@openmetadata.command()
def health() -> None:
    """Check OpenMetadata connectivity using configured credentials."""
    cfg = get_settings()
    client = OpenMetadataClient(
        base_url=cfg.openmetadata_uri(),
        username=cfg.openmetadata_username,
        password=cfg.openmetadata_password,
        verify_ssl=cfg.openmetadata_verify_ssl,
        timeout=10,
        service_name=cfg.openmetadata_service_name,
        service_type=cfg.openmetadata_service_type,
        database_name=cfg.openmetadata_database(),
    )
    logger.debug("openmetadata_health_check_started")
    ok = client.health_check()
    if ok:
        logger.info("openmetadata_health_check_succeeded")
        console.print("[green]OpenMetadata is reachable[/green]")
        return
    logger.warning("openmetadata_health_check_failed")
    console.print("[red]OpenMetadata is not reachable[/red]")
    sys.exit(1)


@openmetadata.command()
@click.option("--include-namespace", multiple=True, help="Only sync these namespaces (repeatable)")
@click.option("--exclude-namespace", multiple=True, help="Skip these namespaces (repeatable)")
@click.option("--dbt/--no-dbt", default=True, help="Also sync dbt models (if manifest exists)")
@click.option("--dbt-schema", default=None, help="Limit dbt sync to a schema (e.g., bronze)")
def sync(
    include_namespace: tuple[str, ...],
    exclude_namespace: tuple[str, ...],
    dbt: bool,
    dbt_schema: str | None,
) -> None:
    """Sync Nessie catalog (and optionally dbt docs) into OpenMetadata."""
    logger.info(
        "openmetadata_sync_started",
        include_namespaces=list(include_namespace),
        exclude_namespaces=list(exclude_namespace),
        dbt_enabled=dbt,
        dbt_schema=dbt_schema,
    )
    cfg = get_settings()
    client = OpenMetadataClient(
        base_url=cfg.openmetadata_uri(),
        username=cfg.openmetadata_username,
        password=cfg.openmetadata_password,
        verify_ssl=cfg.openmetadata_verify_ssl,
        timeout=30,
        service_name=cfg.openmetadata_service_name,
        service_type=cfg.openmetadata_service_type,
        database_name=cfg.openmetadata_database(),
    )

    if not client.health_check():
        logger.warning("openmetadata_sync_health_check_failed")
        console.print("[red]OpenMetadata is not reachable[/red]")
        sys.exit(1)

    try:
        scanner = resolve_catalog_scanner("nessie")
    except RuntimeError as exc:
        logger.error("openmetadata_nessie_scanner_unavailable", error=str(exc))
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    nessie_stats = sync_nessie_tables_to_openmetadata(
        scanner,
        client,
        include_namespaces=list(include_namespace) or None,
        exclude_namespaces=list(exclude_namespace) or None,
    )
    logger.info("openmetadata_nessie_sync_completed", stats=nessie_stats)
    console.print(f"[green]Nessie sync[/green]: {nessie_stats}")

    if dbt:
        try:
            parser = DbtManifestParser.from_config()
            if dbt_schema:
                dbt_stats = parser.sync_to_openmetadata(client, schema_name=dbt_schema)
            else:
                # Default to syncing schemas present in manifest by iterating models.
                manifest = parser.load_manifest()
                schemas = {m.get("schema") for m in parser.get_models(manifest).values()}
                schemas = {s for s in schemas if isinstance(s, str)}
                dbt_stats = {"created": 0, "failed": 0}
                for schema_name in sorted(schemas):
                    partial = parser.sync_to_openmetadata(client, schema_name=schema_name)
                    dbt_stats["created"] += partial.get("created", 0)
                    dbt_stats["failed"] += partial.get("failed", 0)
            console.print(f"[green]dbt sync[/green]: {dbt_stats}")
            logger.info("openmetadata_dbt_sync_completed", stats=dbt_stats)
        except FileNotFoundError:
            logger.warning("openmetadata_dbt_manifest_missing")
            console.print("[yellow]dbt manifest not found; skipping dbt sync[/yellow]")
        except json.JSONDecodeError as e:
            logger.error("openmetadata_dbt_manifest_invalid_json", error=str(e))
            console.print(f"[red]Failed to parse dbt manifest: {e}[/red]")
            sys.exit(1)
