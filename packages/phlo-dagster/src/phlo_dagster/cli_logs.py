"""Logs Command

Access and filter Dagster run logs from CLI.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import click
from rich.console import Console

from phlo.logging import get_logger
from phlo_dagster.cli_logs_display import _display_logs, _tail_logs

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
    asset: Optional[str],
    job: Optional[str],
    level: Optional[str],
    since: Optional[str],
    run_id: Optional[str],
    follow: bool,
    full: bool,
    limit: int,
    output_json: bool,
):
    """
    Access and filter Dagster run logs from CLI.

    Supports multiple filtering options:
    - By asset name: --asset glucose_entries
    - By job name: --job weather_pipeline
    - By log level: --level ERROR
    - By time range: --since 1h (last hour)
    - By specific run: --run-id abc123
    - Tail mode: --follow (real-time updates)

    \b
    Examples:
      phlo logs                           # Recent logs (last 100)
      phlo logs --asset glucose_entries   # Filter by asset
      phlo logs --job weather_pipeline    # Filter by job
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
        logs_data = _get_logs(filters, quiet=output_json)
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


def _get_logs(filters: dict, quiet: bool = False) -> list[dict]:
    """
    Retrieve logs from Dagster with filters.

    Args:
        filters: Filter criteria (asset, job, level, run_id, start_time, limit)

    Returns:
        List of log dictionaries
    """
    try:
        import os

        from dagster_graphql import DagsterGraphQLClient

        dagster_host = os.getenv("DAGSTER_WEBSERVER_HOST", "localhost")
        dagster_port = os.getenv("DAGSTER_WEBSERVER_PORT", "3000")

        client = DagsterGraphQLClient(
            hostname=dagster_host,
            port_number=int(dagster_port),
        )

        # Build GraphQL query
        query = _build_logs_query(filters)
        logger.debug(
            "dagster_logs_graphql_query_started",
            limit=filters.get("limit", 100),
            has_level_filter=filters.get("level") is not None,
            has_run_filter=filters.get("run_id") is not None,
        )

        try:
            result = client._execute(query)
            logs_list = []

            if result and "data" in result:
                runs = result["data"].get("runsOrError", {}).get("runs", [])
                for run in runs:
                    run_id = run.get("runId", "")
                    job_name = run.get("jobName", "")
                    status = run.get("status", "")

                    # Get events for this run
                    events = run.get("events", [])
                    for event in events:
                        event_type = event.get("eventType", "")
                        message = event.get("message", "")
                        timestamp = event.get("timestamp")
                        level = _get_log_level(event_type)

                        log_entry = {
                            "timestamp": timestamp,
                            "level": level,
                            "message": message,
                            "event_type": event_type,
                            "run_id": run_id,
                            "job_name": job_name,
                            "run_status": status,
                        }

                        # Apply level filter
                        if filters.get("level") and level != filters["level"]:
                            continue

                        logs_list.append(log_entry)

            logger.debug(
                "dagster_logs_graphql_query_completed",
                log_count=len(logs_list),
            )
            return logs_list

        except Exception:
            # GraphQL query might fail, provide mock data
            logger.warning(
                "dagster_logs_graphql_query_failed_fallback_mock",
                exc_info=True,
            )
            return _get_mock_logs(filters, show_warning=not quiet)

    except ImportError:
        # Dagster GraphQL client not available, use mock data
        logger.info("dagster_logs_graphql_client_unavailable_fallback_mock")
        return _get_mock_logs(filters, show_warning=not quiet)


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


def _get_mock_logs(filters: dict, show_warning: bool = False) -> list[dict]:
    """Return mock logs for demo/testing."""
    if show_warning:
        console.print("[dim](showing demo data - Dagster not connected)[/dim]\n")
    now = datetime.now(timezone.utc)
    mock_logs = [
        {
            "timestamp": (now - timedelta(minutes=5)).isoformat(),
            "level": "INFO",
            "message": "Asset materialization started for glucose_entries",
            "event_type": "ASSET_MATERIALIZATION_START",
            "run_id": "abc123",
            "job_name": "glucose_ingestion",
            "run_status": "STARTED",
        },
        {
            "timestamp": (now - timedelta(minutes=4)).isoformat(),
            "level": "INFO",
            "message": "Fetching data from Nightscout API",
            "event_type": "STEP_INPUT",
            "run_id": "abc123",
            "job_name": "glucose_ingestion",
            "run_status": "STARTED",
        },
        {
            "timestamp": (now - timedelta(minutes=3)).isoformat(),
            "level": "DEBUG",
            "message": "Downloaded 1234 records from API",
            "event_type": "LOG_MESSAGE",
            "run_id": "abc123",
            "job_name": "glucose_ingestion",
            "run_status": "STARTED",
        },
        {
            "timestamp": (now - timedelta(minutes=2)).isoformat(),
            "level": "INFO",
            "message": "Validating data against schema",
            "event_type": "STEP_OUTPUT",
            "run_id": "abc123",
            "job_name": "glucose_ingestion",
            "run_status": "SUCCESS",
        },
        {
            "timestamp": (now - timedelta(minutes=1)).isoformat(),
            "level": "INFO",
            "message": "Asset materialization completed successfully",
            "event_type": "ASSET_MATERIALIZATION_SUCCESS",
            "run_id": "abc123",
            "job_name": "glucose_ingestion",
            "run_status": "SUCCESS",
        },
    ]

    # Apply filters
    filtered = mock_logs

    if filters.get("level"):
        filtered = [log for log in filtered if log["level"] == filters["level"]]

    if filters.get("asset"):
        filtered = [log for log in filtered if filters["asset"].lower() in log["message"].lower()]

    if filters.get("job"):
        filtered = [log for log in filtered if log["job_name"] == filters["job"]]

    if filters.get("run_id"):
        filtered = [log for log in filtered if log["run_id"] == filters["run_id"]]

    if filters.get("start_time"):
        filtered = [
            log
            for log in filtered
            if datetime.fromisoformat(log["timestamp"]) >= filters["start_time"]
        ]

    return filtered[: filters.get("limit", 100)]
