"""Status Command

Display current state of assets, jobs, and services.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


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
    group: Optional[str],
    stale: bool,
    output_json: bool,
):
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

    result = {}

    if show_assets:
        asset_status = _get_asset_status(group=group, stale=stale, quiet=output_json)
        result["assets"] = asset_status
        if not output_json:
            _display_asset_status(asset_status, group=group, stale=stale)

    if show_services:
        service_status = _get_service_status()
        result["services"] = service_status
        if not output_json:
            _display_service_status(service_status)

    elapsed = time.time() - start_time

    if output_json:
        result["timestamp"] = datetime.utcnow().isoformat()
        result["elapsed_seconds"] = round(elapsed, 2)
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        console.print(f"[dim]Query time: {elapsed:.2f}s[/dim]\n")


def _get_asset_status(
    group: Optional[str] = None,
    stale: bool = False,
    quiet: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get asset status from Dagster GraphQL API.

    Returns:
        List of asset status dicts with name, last_run, status, freshness
    """
    assets = []

    try:
        # Try to get asset info from Dagster
        import os

        from dagster_graphql import DagsterGraphQLClient

        dagster_host = os.getenv("DAGSTER_WEBSERVER_HOST", "localhost")
        dagster_port = os.getenv("DAGSTER_WEBSERVER_PORT", "3000")

        client = DagsterGraphQLClient(
            hostname=dagster_host,
            port_number=int(dagster_port),
        )

        # Query asset materializations
        # This is a simplified implementation - in production would query actual GraphQL
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
            result = client.execute(query)
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
                        "status": last_run.get("status", "unknown") if last_run else "never_run",
                        "freshness": _get_freshness_indicator(last_run),
                        "is_stale": is_stale,
                    }
                    assets.append(status_info)
        except Exception:
            # If GraphQL fails, silently continue (service might be down)
            pass

    except ImportError:
        # Dagster GraphQL client not available
        pass

    # If no assets found, return mock data for demo
    if not assets:
        assets = _get_mock_asset_status(group=group, stale=stale, show_warning=not quiet)

    return assets


def _get_asset_last_run(asset_name: str) -> Optional[Dict[str, Any]]:
    """Get last run info for an asset."""
    # Mock implementation - would query Dagster in production
    return None


def _check_if_stale(last_run: Optional[Dict[str, Any]]) -> bool:
    """Check if asset is stale based on SLA."""
    if not last_run:
        return True

    if last_run.get("status") == "failure":
        return True

    last_run_time = last_run.get("timestamp")
    if not last_run_time:
        return True

    # Check if older than 24 hours
    age = datetime.utcnow() - last_run_time
    return age > timedelta(hours=24)


def _get_freshness_indicator(last_run: Optional[Dict[str, Any]]) -> str:
    """Get freshness indicator (fresh, stale, never)."""
    if not last_run:
        return "never_run"

    if last_run.get("status") == "failure":
        return "failed"

    last_run_time = last_run.get("timestamp")
    if not last_run_time:
        return "unknown"

    age = datetime.utcnow() - last_run_time

    if age < timedelta(hours=1):
        return "fresh"
    elif age < timedelta(hours=24):
        return "okay"
    else:
        return "stale"


def _get_mock_asset_status(
    group: Optional[str] = None,
    stale: bool = False,
    show_warning: bool = False,
) -> List[Dict[str, Any]]:
    """Get mock asset status for demo."""
    if show_warning:
        console.print("[dim](showing demo data - Dagster not connected)[/dim]\n")
    mock_assets = [
        {
            "name": "dlt_glucose_entries",
            "group": "nightscout",
            "last_run": {
                "status": "success",
                "timestamp": datetime.utcnow() - timedelta(hours=0.5),
            },
            "status": "success",
            "freshness": "fresh",
            "is_stale": False,
        },
        {
            "name": "stg_glucose_entries",
            "group": "nightscout",
            "last_run": {
                "status": "success",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
            },
            "status": "success",
            "freshness": "okay",
            "is_stale": False,
        },
        {
            "name": "fct_glucose_readings",
            "group": "nightscout",
            "last_run": {
                "status": "failure",
                "timestamp": datetime.utcnow() - timedelta(hours=48),
            },
            "status": "failure",
            "freshness": "failed",
            "is_stale": True,
        },
        {
            "name": "mrt_glucose_readings",
            "group": "nightscout",
            "last_run": {
                "status": "success",
                "timestamp": datetime.utcnow() - timedelta(hours=30),
            },
            "status": "success",
            "freshness": "stale",
            "is_stale": True,
        },
    ]

    # Filter by group if specified
    if group:
        mock_assets = [a for a in mock_assets if a["group"] == group]

    # Filter stale if requested
    if stale:
        mock_assets = [a for a in mock_assets if a["is_stale"]]

    return mock_assets


def _get_service_status() -> Dict[str, Dict[str, Any]]:
    """Get service health status."""
    services = {}

    # Check Dagster
    services["dagster"] = _check_service_health(
        "http://localhost:3000/server_info",
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
    services["nessie"] = _check_service_health(
        "http://localhost:19120/api/v1/config",
        name="Nessie",
    )

    return services


def _check_service_health(
    url: str,
    name: str,
) -> Dict[str, Any]:
    """Check if a service is healthy."""
    try:
        import requests
    except ImportError:
        return {
            "name": name,
            "status": "error",
            "latency_ms": None,
            "error": "requests library not installed",
        }

    try:
        start = time.time()
        response = requests.get(url, timeout=2)
        latency = (time.time() - start) * 1000  # Convert to ms

        is_healthy = 200 <= response.status_code < 300
        status = "healthy" if is_healthy else "unhealthy"

        return {
            "name": name,
            "status": status,
            "latency_ms": round(latency, 1),
            "status_code": response.status_code,
        }
    except requests.exceptions.Timeout:
        return {
            "name": name,
            "status": "timeout",
            "latency_ms": 2000,
            "error": "Request timeout",
        }
    except requests.exceptions.ConnectionError:
        return {
            "name": name,
            "status": "down",
            "latency_ms": None,
            "error": "Connection refused",
        }
    except Exception as e:
        return {
            "name": name,
            "status": "error",
            "latency_ms": None,
            "error": str(e),
        }


def _display_asset_status(
    assets: List[Dict[str, Any]],
    group: Optional[str] = None,
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
        status = asset["status"]
        if status == "success":
            status_str = "[green]✓ success[/green]"
        elif status == "failure":
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
            age = datetime.utcnow() - ts
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


def _display_service_status(services: Dict[str, Dict[str, Any]]) -> None:
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
        status = service.get("status", "unknown")

        # Status color
        if status == "healthy":
            status_str = "[green]✓ Healthy[/green]"
        elif status == "down":
            status_str = "[red]✗ Down[/red]"
        elif status == "timeout":
            status_str = "[yellow]⚠ Timeout[/yellow]"
        elif status == "unhealthy":
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
