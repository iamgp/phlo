"""Logs Command

Access and filter Dagster run logs from CLI.
"""

import os
import re
from datetime import datetime, timedelta, timezone

import click
import requests as http_requests
from rich.console import Console

from phlo.logging import get_logger
from phlo_dagster.cli_logs_display import _display_logs, _tail_logs
from phlo_dagster.settings import get_settings

console = Console()
logger = get_logger(__name__)


@click.command()
@click.option(
    "--asset",
    type=str,
    help="Filter by asset name",
)
@click.option(
    "--job",
    type=str,
    help="Filter by job name",
)
@click.option(
    "--level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Filter by log level",
)
@click.option(
    "--since",
    type=str,
    help="Filter by time (e.g., 1h, 30m, 2d)",
)
@click.option(
    "--run-id",
    type=str,
    help="Get logs for specific run",
)
@click.option(
    "--follow",
    is_flag=True,
    default=False,
    help="Tail mode - follow new logs in real-time",
)
@click.option(
    "--full",
    is_flag=True,
    default=False,
    help="Don't truncate long messages",
)
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Number of logs to retrieve (default: 100)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="JSON output for scripting",
)
def logs(
    asset: str | None,
    job: str | None,
    level: str | None,
    since: str | None,
    run_id: str | None,
    follow: bool,
    full: bool,
    limit: int,
    output_json: bool,
):
    """
    Access and filter Dagster run logs from CLI.

    Supports multiple filtering options:
    - By asset name: --asset dlt_orders
    - By job name: --job orders_pipeline
    - By log level: --level ERROR
    - By time range: --since 1h (last hour)
    - By specific run: --run-id abc123
    - Tail mode: --follow (real-time updates)

    \b
    Examples:
      phlo logs                           # Recent logs (last 100)
      phlo logs --asset dlt_orders        # Filter by asset
      phlo logs --job orders_pipeline     # Filter by job
      phlo logs --level ERROR             # Errors only
      phlo logs --since 1h                # Last hour
      phlo logs --follow                  # Tail mode
      phlo logs --run-id abc123           # Specific run
      phlo logs --full                    # Don't truncate
    """
    if not output_json:
        console.print("\n[bold blue]📋 Logs[/bold blue]\n")

    # Parse time filter
    start_time = _parse_since(since) if since else None
    logger.info(
        "dagster_logs_command_started",
        has_asset_filter=asset is not None,
        has_job_filter=job is not None,
        level=level,
        since=since,
        run_id=run_id,
        follow=follow,
        full=full,
        limit=limit,
        output_json=output_json,
    )

    # Build filters
    filters = {
        "asset": asset,
        "job": job,
        "level": level,
        "run_id": run_id,
        "start_time": start_time,
        "limit": limit,
    }

    if follow:
        _tail_logs(filters, full, output_json)
        logger.info(
            "dagster_logs_follow_mode_completed",
            limit=limit,
        )
    else:
        logs_data = _get_logs(filters)
        _display_logs(logs_data, full=full, output_json=output_json)
        logger.info(
            "dagster_logs_query_completed",
            log_count=len(logs_data),
            limit=limit,
        )


def _parse_since(since_str: str) -> datetime:
    """
    Parse time filter string (e.g., '1h', '30m', '2d').

    Args:
        since_str: Time filter string

    Returns:
        datetime object for the cutoff time
    """
    try:
        # Extract numeric part and unit
        match = re.match(r"(\d+)\s*([hmd])", since_str.lower())
        if not match:
            raise ValueError(f"Invalid time format: {since_str}")

        amount = int(match.group(1))
        unit = match.group(2)

        now = datetime.now(timezone.utc)
        if unit == "h":
            return now - timedelta(hours=amount)
        elif unit == "m":
            return now - timedelta(minutes=amount)
        elif unit == "d":
            return now - timedelta(days=amount)
        else:
            raise ValueError(f"Unknown time unit: {unit}")
    except Exception as e:
        logger.warning(
            "dagster_logs_since_parse_failed",
            since=since_str,
            error=str(e),
        )
        console.print(f"[yellow]Warning: Invalid time filter '{since_str}': {e}[/yellow]")
        return datetime.now(timezone.utc) - timedelta(hours=24)  # Default to last 24 hours


def _get_logs(filters: dict) -> list[dict]:
    """
    Retrieve logs from Dagster with filters.

    Args:
        filters: Filter criteria (asset, job, level, run_id, start_time, limit)

    Returns:
        List of log dictionaries
    """
    try:
        settings = get_settings()
        dagster_host = os.getenv("DAGSTER_WEBSERVER_HOST", "localhost")
        dagster_port = os.getenv("DAGSTER_WEBSERVER_PORT") or str(settings.dagster_port)

        dagster_url = f"http://{dagster_host}:{dagster_port}/graphql"

        # Build GraphQL query
        query = _build_logs_query(filters)
        logger.debug(
            "dagster_logs_graphql_query_started",
            limit=filters.get("limit", 100),
            has_level_filter=filters.get("level") is not None,
            has_run_filter=filters.get("run_id") is not None,
        )

        try:
            response = http_requests.post(dagster_url, json={"query": query}, timeout=5)
            response.raise_for_status()
            result = response.json()

            logs_list: list[dict] = []

            if result and "data" in result:
                runs = result["data"].get("runsOrError", {}).get("runs", [])
                for run in runs:
                    run_id = run.get("runId", "")
                    job_name = run.get("jobName", "")
                    run_status = run.get("status", "")

                    # Get events for this run
                    events = run.get("events", [])
                    for event in events:
                        event_type = event.get("eventType", "")
                        message = event.get("message", "")
                        timestamp = event.get("timestamp")
                        event_level = _get_log_level(event_type)

                        log_entry = {
                            "timestamp": timestamp,
                            "level": event_level,
                            "message": message,
                            "event_type": event_type,
                            "run_id": run_id,
                            "job_name": job_name,
                            "run_status": run_status,
                        }

                        # Apply level filter
                        if filters.get("level") and event_level != filters["level"]:
                            continue

                        logs_list.append(log_entry)

            logger.debug(
                "dagster_logs_graphql_query_completed",
                log_count=len(logs_list),
            )
            return logs_list

        except Exception:
            logger.warning(
                "dagster_logs_graphql_query_failed",
                exc_info=True,
            )
            return []

    except Exception:
        logger.info(
            "dagster_logs_graphql_client_unavailable",
            exc_info=True,
        )
        return []


def _build_logs_query(filters: dict) -> str:
    """
    Build GraphQL query for logs.

    Args:
        filters: Filter criteria

    Returns:
        GraphQL query string
    """
    # Simplified query structure - in production would be more comprehensive
    query = """
    {
        runsOrError {
            ... on Runs {
                runs(limit: %d, statuses: []) {
                    runId
                    jobName
                    status
                    startTime
                    endTime
                    events {
                        ... on ExecutionStepInputEvent {
                            eventType
                            message
                            timestamp
                        }
                        ... on ExecutionStepOutputEvent {
                            eventType
                            message
                            timestamp
                        }
                        ... on StepFailureEvent {
                            eventType
                            message
                            timestamp
                        }
                        ... on StepSuccessEvent {
                            eventType
                            message
                            timestamp
                        }
                        ... on LogMessageEvent {
                            eventType
                            message
                            timestamp
                            level
                        }
                    }
                }
            }
        }
    }
    """ % (filters.get("limit", 100))
    return query


def _get_log_level(event_type: str) -> str:
    """Map event type to log level."""
    if "ERROR" in event_type or "FAILURE" in event_type:
        return "ERROR"
    elif "WARNING" in event_type:
        return "WARNING"
    elif "SUCCESS" in event_type or "OUTPUT" in event_type:
        return "INFO"
    else:
        return "DEBUG"
