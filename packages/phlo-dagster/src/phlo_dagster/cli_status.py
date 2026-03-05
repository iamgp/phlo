"""Status Command

Display current state of assets, jobs, and services.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import click
import requests as http_requests
from rich.console import Console
from rich.table import Table

from phlo.logging import get_logger
from phlo_dagster.settings import get_settings

console = Console()
logger = get_logger(__name__)


@click.command()
@click.option(
    "--assets",
    is_flag=True,
    default=False,
    help="Show assets only",
)
@click.option(
    "--services",
    is_flag=True,
    default=False,
    help="Show services only",
)
@click.option(
    "--group",
    help="Filter by asset group",
)
@click.option(
    "--stale",
    is_flag=True,
    default=False,
    help="Show only stale assets",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="JSON output for scripting",
)
def status(
    assets: bool,
    services: bool,
    group: str | None,
    stale: bool,
    output_json: bool,
) -> None:
    """
    Show current state of assets, jobs, and services.

    Displays:
    - Asset materialization status and freshness
    - Service health (Dagster, Trino, MinIO, Nessie)
    - Color-coded status indicators

    \b
    Examples:
      phlo status                    # All assets and services
      phlo status --assets           # Assets only
      phlo status --services         # Services only
      phlo status --group nightscout # Filter by group
      phlo status --stale            # Only stale assets
      phlo status --json             # JSON output for scripting
    """
    if not output_json:
        console.print("\n[bold blue]📊 Status Report[/bold blue]\n")

    start_time = time.time()

    # Show both by default if neither is specified
    show_assets = assets or (not assets and not services)
    show_services = services or (not assets and not services)
    logger.info(
        "dagster_status_command_started",
        show_assets=show_assets,
        show_services=show_services,
        group=group,
        stale_only=stale,
        output_json=output_json,
    )

    result = {}

    if show_assets:
        asset_status = _get_asset_status(group=group, stale=stale)
        result["assets"] = asset_status
        logger.info(
            "dagster_status_assets_collected",
            asset_count=len(asset_status),
            group=group,
            stale_only=stale,
        )
        if not output_json:
            _display_asset_status(asset_status, group=group, stale=stale)

    if show_services:
        service_status = _get_service_status()
        result["services"] = service_status
        logger.info(
            "dagster_status_services_collected",
            service_count=len(service_status),
        )
        if not output_json:
            _display_service_status(service_status)

    elapsed = time.time() - start_time

    if output_json:
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        result["elapsed_seconds"] = round(elapsed, 2)
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        console.print(f"[dim]Query time: {elapsed:.2f}s[/dim]\n")
    logger.info(
        "dagster_status_command_finished",
        elapsed_seconds=round(elapsed, 3),
        show_assets=show_assets,
        show_services=show_services,
    )


def _get_asset_status(
    group: str | None = None,
    stale: bool = False,
) -> list[dict[str, Any]]:
    """
    Get asset status from Dagster GraphQL API.

    Returns:
        List of asset status dicts with name, last_run, status, freshness
    """
    assets: list[dict[str, Any]] = []
    logger.debug(
        "dagster_status_asset_query_started",
        group=group,
        stale_only=stale,
    )

    try:
        settings = get_settings()
        dagster_host = os.getenv("DAGSTER_WEBSERVER_HOST", "localhost")
        dagster_port = os.getenv("DAGSTER_WEBSERVER_PORT") or str(settings.dagster_port)

        dagster_url = f"http://{dagster_host}:{dagster_port}/graphql"

        # Query asset materializations
        query = """
        {
            assetsOrError {
                __typename
                ... on AssetConnection {
                    nodes {
                        key {
                            path
                        }
                        definition {
                            groupName
                            description
                        }
                    }
                }
            }
        }
        """

        try:
            response = http_requests.post(dagster_url, json={"query": query}, timeout=5)
            response.raise_for_status()
            result = response.json()

            if result and "data" in result:
                for asset in result["data"].get("assetsOrError", {}).get("nodes", []):
                    asset_path = asset.get("key", {}).get("path", [])
                    asset_name = "/".join(asset_path) if asset_path else "unknown"
                    asset_group = asset.get("definition", {}).get("groupName", "")

                    if group and asset_group != group:
                        continue

                    # Get last materialization
                    last_run = _get_asset_last_run(asset_name)

                    is_stale = _check_if_stale(last_run)
                    if stale and not is_stale:
                        continue

                    status_info = {
                        "name": asset_name,
                        "group": asset_group,
                        "last_run": last_run,
                        "status": (last_run.get("status", "unknown") if last_run else "never_run"),
                        "freshness": _get_freshness_indicator(last_run),
                        "is_stale": is_stale,
                    }
                    assets.append(status_info)
        except Exception:
            # If GraphQL fails, silently continue (service might be down)
            logger.warning(
                "dagster_status_asset_query_failed",
                group=group,
                stale_only=stale,
                exc_info=True,
            )

    except Exception:
        logger.info(
            "dagster_status_asset_query_client_unavailable",
            group=group,
            stale_only=stale,
            exc_info=True,
        )

    return assets


def _get_asset_last_run(asset_name: str) -> dict[str, Any] | None:
    """Get last run info for an asset."""
    return None


def _check_if_stale(last_run: dict[str, Any] | None) -> bool:
    """Check if asset is stale based on SLA."""
    if not last_run:
        return True

    if last_run.get("status") == "failure":
        return True

    last_run_time = last_run.get("timestamp")
    if not last_run_time:
        return True

    # Check if older than 24 hours
    age = datetime.now(timezone.utc) - last_run_time
    return age > timedelta(hours=24)


def _get_freshness_indicator(last_run: dict[str, Any] | None) -> str:
    """Get freshness indicator (fresh, stale, never)."""
    if not last_run:
        return "never_run"

    if last_run.get("status") == "failure":
        return "failed"

    last_run_time = last_run.get("timestamp")
    if not last_run_time:
        return "unknown"

    age = datetime.now(timezone.utc) - last_run_time

    if age < timedelta(hours=1):
        return "fresh"
    elif age < timedelta(hours=24):
        return "okay"
    else:
        return "stale"


def _get_service_status() -> dict[str, dict[str, Any]]:
    """Get service health status."""
    services: dict[str, dict[str, Any]] = {}

    settings = get_settings()

    # Check Dagster
    services["dagster"] = _check_service_health(
        f"http://localhost:{settings.dagster_port}/server_info",
        name="Dagster",
    )

    # Check Trino
    services["trino"] = _check_service_health(
        "http://localhost:8080/v1/info",
        name="Trino",
    )

    # Check MinIO
    services["minio"] = _check_service_health(
        "http://localhost:9000/minio/health/ready",
        name="MinIO",
    )

    # Check Nessie
    nessie_port = 19120
    try:
        from phlo_nessie.settings import get_settings as get_nessie_settings

        nessie_port = get_nessie_settings().nessie_port
    except Exception:
        pass
    services["nessie"] = _check_service_health(
        f"http://localhost:{nessie_port}/api/v1/config",
        name="Nessie",
    )
    logger.info("dagster_status_service_checks_completed", service_count=len(services))

    return services


def _check_service_health(
    url: str,
    name: str,
) -> dict[str, Any]:
    """Check if a service is healthy."""
    try:
        from requests import exceptions as requests_exceptions
    except ImportError:
        logger.info(
            "dagster_status_service_health_requests_missing",
            service_name=name,
        )
        return {
            "name": name,
            "status": "error",
            "latency_ms": None,
            "error": "requests library not installed",
        }

    try:
        start = time.time()
        response = http_requests.get(url, timeout=2)
        latency = (time.time() - start) * 1000  # Convert to ms

        is_healthy = 200 <= response.status_code < 300
        health_status = "healthy" if is_healthy else "unhealthy"
        if not is_healthy:
            logger.warning(
                "dagster_status_service_health_unhealthy",
                service_name=name,
                status_code=response.status_code,
                latency_ms=round(latency, 1),
            )

        return {
            "name": name,
            "status": health_status,
            "latency_ms": round(latency, 1),
            "status_code": response.status_code,
        }
    except requests_exceptions.Timeout:
        logger.warning(
            "dagster_status_service_health_timeout",
            service_name=name,
            timeout_seconds=2,
        )
        return {
            "name": name,
            "status": "timeout",
            "latency_ms": 2000,
            "error": "Request timeout",
        }
    except requests_exceptions.ConnectionError:
        logger.warning(
            "dagster_status_service_health_connection_error",
            service_name=name,
        )
        return {
            "name": name,
            "status": "down",
            "latency_ms": None,
            "error": "Connection refused",
        }
    except Exception as e:
        logger.error(
            "dagster_status_service_health_failed",
            service_name=name,
            error=str(e),
            exc_info=True,
        )
        return {
            "name": name,
            "status": "error",
            "latency_ms": None,
            "error": str(e),
        }


def _display_asset_status(
    assets: list[dict[str, Any]],
    group: str | None = None,
    stale: bool = False,
) -> None:
    """Display asset status table."""
    if not assets:
        console.print("[yellow]No assets found[/yellow]")
        return

    table = Table(title="Asset Status", show_header=True, header_style="bold blue")

    table.add_column("Asset Name", style="cyan")
    table.add_column("Group", style="magenta")
    table.add_column("Status", style="white")
    table.add_column("Last Run", style="green")
    table.add_column("Freshness", style="yellow")

    for asset in sorted(assets, key=lambda a: a["name"]):
        # Status color
        asset_status = asset["status"]
        if asset_status == "success":
            status_str = "[green]✓ success[/green]"
        elif asset_status == "failure":
            status_str = "[red]✗ failed[/red]"
        else:
            status_str = "[yellow]⚠ unknown[/yellow]"

        # Freshness color
        freshness = asset["freshness"]
        if freshness == "fresh":
            freshness_str = "[green]Fresh[/green]"
        elif freshness == "okay":
            freshness_str = "[yellow]Okay[/yellow]"
        elif freshness == "stale":
            freshness_str = "[red]Stale[/red]"
        elif freshness == "failed":
            freshness_str = "[red]Failed[/red]"
        else:
            freshness_str = "[dim]Never run[/dim]"

        # Last run time
        last_run = asset.get("last_run")
        if last_run and last_run.get("timestamp"):
            ts = last_run["timestamp"]
            age = datetime.now(timezone.utc) - ts
            if age < timedelta(hours=1):
                last_run_str = f"{int(age.total_seconds() / 60)}m ago"
            elif age < timedelta(days=1):
                last_run_str = f"{int(age.total_seconds() / 3600)}h ago"
            else:
                last_run_str = f"{int(age.days)}d ago"
        else:
            last_run_str = "[dim]Never[/dim]"

        table.add_row(
            asset["name"],
            asset.get("group", "-"),
            status_str,
            last_run_str,
            freshness_str,
        )

    console.print(table)


def _display_service_status(services: dict[str, dict[str, Any]]) -> None:
    """Display service health table."""
    table = Table(
        title="Service Health",
        show_header=True,
        header_style="bold blue",
    )

    table.add_column("Service", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Latency", style="yellow")

    for service_key in sorted(services.keys()):
        service = services[service_key]
        svc_status = service.get("status", "unknown")

        # Status color
        if svc_status == "healthy":
            status_str = "[green]✓ Healthy[/green]"
        elif svc_status == "down":
            status_str = "[red]✗ Down[/red]"
        elif svc_status == "timeout":
            status_str = "[yellow]⚠ Timeout[/yellow]"
        elif svc_status == "unhealthy":
            status_str = "[red]✗ Unhealthy[/red]"
        else:
            status_str = "[yellow]⚠ Error[/yellow]"

        # Latency
        latency = service.get("latency_ms")
        if latency:
            latency_str = f"{latency:.0f}ms"
        else:
            latency_str = "[dim]—[/dim]"

        table.add_row(
            service["name"],
            status_str,
            latency_str,
        )

    console.print(table)
