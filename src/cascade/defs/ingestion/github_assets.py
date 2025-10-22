# github_assets.py - Dagster assets for ingesting GitHub user events and repository statistics using DLT (Data Load Tool)
# Implements the raw data ingestion layer of the lakehouse, fetching from GitHub API
# and staging data to S3 parquet files, then registering in Iceberg tables

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import dagster as dg
import dlt
import requests
from dagster.preview.freshness import FreshnessPolicy

from cascade.config import config
from cascade.defs.partitions import daily_partition
from cascade.defs.resources.iceberg import IcebergResource


# --- Helper Functions ---
# Utility functions for staging path generation and data processing
def get_staging_path(partition_date: str, table_name: str) -> str:
    """
    Get S3 staging path for a partition.

    Args:
        partition_date: Partition date (YYYY-MM-DD)
        table_name: Table name (e.g., "user_events", "repo_stats")

    Returns:
        S3 path for staging parquet files
    """
    return f"{config.iceberg_staging_path}/{table_name}/{partition_date}"


# --- Dagster Assets ---
# Data ingestion assets that materialize raw data into the lakehouse
@dg.asset(
    name="dlt_github_user_events",
    group_name="github",
    partitions_def=daily_partition,
    description=(
        "GitHub user events ingested via DLT to S3 parquet, "
        "then registered in Iceberg raw.user_events with daily partitioning"
    ),
    compute_kind="dlt+pyiceberg",
    op_tags={"dagster/max_runtime": 300},
    retry_policy=dg.RetryPolicy(max_retries=3, delay=30),
    automation_condition=dg.AutomationCondition.on_cron("0 */1 * * *"),
    freshness_policy=FreshnessPolicy.time_window(fail_window=timedelta(hours=24), warn_window=timedelta(hours=1)),
)
def github_user_events(context, iceberg: IcebergResource) -> dg.MaterializeResult:
    """
    Ingest GitHub user events using two-step pattern:

    1. DLT stages data to S3 as parquet files
    2. PyIceberg registers/appends to Iceberg table

    Features:
    - Daily partitioning by event date
    - S3 parquet staging with filesystem destination
    - Iceberg table management with schema enforcement
    - Comprehensive error handling and logging
    """
    partition_date = context.partition_key
    pipeline_name = f"github_user_events_{partition_date.replace('-', '_')}"
    table_name = f"{config.iceberg_default_namespace}.github_user_events"

    # Calculate date range for the partition
    start_date = datetime.fromisoformat(partition_date)
    end_date = start_date + timedelta(days=1)

    pipelines_base_dir = Path.home() / ".dlt" / "pipelines" / "partitioned"
    pipelines_base_dir.mkdir(parents=True, exist_ok=True)

    context.log.info(f"Starting ingestion for partition {partition_date}")
    context.log.info(f"Date range: {start_date.isoformat()} to {end_date.isoformat()}")
    context.log.info(f"Target table: {table_name}")

    try:
        # Step 1: Fetch data from GitHub API
        context.log.info("Fetching user events from GitHub API...")
        try:
            if not config.github_username:
                raise ValueError("GitHub username not configured")

            url = f"{config.github_base_url}/users/{config.github_username}/events"
            headers = {"Accept": "application/vnd.github+json"}
            if config.github_token:
                headers["Authorization"] = f"token {config.github_token}"

            # GitHub API returns events in reverse chronological order
            # We need to paginate and filter for our date range
            all_events = []
            page = 1
            per_page = 100

            while True:
                params = {"page": page, "per_page": per_page}
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()

                page_events = response.json()
                if not page_events:
                    break

                # Filter events for our date range
                filtered_events = []
                for event in page_events:
                    event_date = datetime.fromisoformat(event["created_at"].replace('Z', '+00:00'))
                    if start_date <= event_date < end_date:
                        filtered_events.append(event)
                    elif event_date < start_date:
                        # Since events are in reverse chronological order,
                        # if we hit an event older than our start date, we can stop
                        break

                all_events.extend(filtered_events)

                # GitHub API limits to 300 events per user, and pagination is limited
                if len(page_events) < per_page or len(all_events) >= 300:
                    break

                page += 1

            context.log.info(f"Successfully fetched {len(all_events)} events from GitHub API")

        except requests.RequestException as e:
            context.log.error(f"Failed to fetch data from GitHub API: {e}")
            raise

        if not all_events:
            context.log.info(f"No events for partition {partition_date}, skipping")
            return dg.MaterializeResult(
                metadata={
                    "partition_date": dg.MetadataValue.text(partition_date),
                    "rows_loaded": dg.MetadataValue.int(0),
                    "status": dg.MetadataValue.text("no_data"),
                }
            )

        # Add cascade ingestion timestamp
        ingestion_timestamp = datetime.utcnow()
        for event in all_events:
            event["_cascade_ingested_at"] = ingestion_timestamp

        # Step 2: Stage to S3 parquet using DLT
        context.log.info("Staging data to parquet via DLT...")
        start_time_ts = time.time()

        staging_path = get_staging_path(partition_date, "user_events")
        local_staging_root = (pipelines_base_dir / pipeline_name / "stage").resolve()
        local_staging_root.mkdir(parents=True, exist_ok=True)

        # Create DLT pipeline with filesystem destination targeting local staging
        filesystem_destination = dlt.destinations.filesystem(
            bucket_url=local_staging_root.as_uri(),
        )

        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            destination=filesystem_destination,
            dataset_name="github",
            pipelines_dir=str(pipelines_base_dir),
        )

        @dlt.resource(name="user_events", write_disposition="replace")
        def provide_user_events() -> Any:
            yield all_events

        # Run DLT pipeline to stage parquet files
        info = pipeline.run(
            provide_user_events(),
            loader_file_format="parquet",
        )

        if not info.load_packages:
            raise RuntimeError("DLT pipeline produced no load packages")

        load_package = info.load_packages[0]
        completed_jobs = load_package.jobs.get("completed_jobs") or []
        if not completed_jobs:
            raise RuntimeError("DLT pipeline completed without producing parquet output")

        parquet_path = Path(completed_jobs[0].file_path)
        if not parquet_path.is_absolute():
            parquet_path = (local_staging_root / parquet_path).resolve()

        context.log.debug(
            "DLT staged parquet to %s (logical %s)",
            parquet_path,
            staging_path,
        )

        dlt_elapsed = time.time() - start_time_ts
        context.log.info(f"DLT staging completed in {dlt_elapsed:.2f}s")

        # Step 3: Ensure Iceberg table exists
        context.log.info(f"Ensuring Iceberg table {table_name} exists...")
        # We'll define the schema in the schemas module
        from cascade.iceberg.schema import get_schema
        schema = get_schema("user_events")
        iceberg.ensure_table(
            table_name=table_name,
            schema=schema,
            partition_spec=None,
        )

        # Step 4: Append to Iceberg table
        context.log.info("Appending data to Iceberg table...")
        iceberg.append_parquet(table_name=table_name, data_path=str(parquet_path))

        total_elapsed = time.time() - start_time_ts
        rows_loaded = len(all_events)
        context.log.info(f"Ingestion completed successfully in {total_elapsed:.2f}s")
        context.log.info(f"Loaded {rows_loaded} rows to {table_name}")

        return dg.MaterializeResult(
            metadata={
                "partition_date": dg.MetadataValue.text(partition_date),
                "rows_loaded": dg.MetadataValue.int(rows_loaded),
                "start_date": dg.MetadataValue.text(start_date.isoformat()),
                "end_date": dg.MetadataValue.text(end_date.isoformat()),
                "table_name": dg.MetadataValue.text(table_name),
                "dlt_elapsed_seconds": dg.MetadataValue.float(dlt_elapsed),
                "total_elapsed_seconds": dg.MetadataValue.float(total_elapsed),
            }
        )

    except requests.RequestException as e:
        context.log.error(f"API request failed for partition {partition_date}: {e}")
        raise RuntimeError(
            f"Failed to fetch data from GitHub API for partition {partition_date}"
        ) from e

    except Exception as e:
        context.log.error(f"Ingestion failed for partition {partition_date}: {e}")
        raise RuntimeError(f"Ingestion failed for partition {partition_date}: {e}") from e


@dg.asset(
    name="dlt_github_repo_stats",
    group_name="github",
    partitions_def=daily_partition,
    description=(
        "GitHub repository statistics ingested via DLT to S3 parquet, "
        "then registered in Iceberg raw.repo_stats with daily partitioning"
    ),
    compute_kind="dlt+pyiceberg",
    op_tags={"dagster/max_runtime": 600},  # Longer timeout for stats computation
    retry_policy=dg.RetryPolicy(max_retries=3, delay=60),
    automation_condition=dg.AutomationCondition.on_cron("0 2 * * *"),  # Daily at 2 AM
    freshness_policy=FreshnessPolicy.time_window(fail_window=timedelta(hours=48), warn_window=timedelta(hours=24)),
)
def github_repo_stats(context, iceberg: IcebergResource) -> dg.MaterializeResult:
    """
    Ingest GitHub repository statistics using two-step pattern:

    1. DLT stages data to S3 as parquet files
    2. PyIceberg registers/appends to Iceberg table

    Features:
    - Daily partitioning by collection date
    - Multiple stat types: contributors, commit_activity, code_frequency
    - S3 parquet staging with filesystem destination
    - Iceberg table management with schema enforcement
    - Comprehensive error handling and logging
    """
    partition_date = context.partition_key
    pipeline_name = f"github_repo_stats_{partition_date.replace('-', '_')}"
    table_name = f"{config.iceberg_default_namespace}.github_repo_stats"

    pipelines_base_dir = Path.home() / ".dlt" / "pipelines" / "partitioned"
    pipelines_base_dir.mkdir(parents=True, exist_ok=True)

    context.log.info(f"Starting repo stats ingestion for partition {partition_date}")
    context.log.info(f"Target table: {table_name}")

    try:
        # Step 1: Fetch repository statistics from GitHub API
        context.log.info("Fetching repository statistics from GitHub API...")

        if not config.github_username:
            raise ValueError("GitHub username not configured")

        # Get user's repositories first
        repos_url = f"{config.github_base_url}/users/{config.github_username}/repos"
        headers = {"Accept": "application/vnd.github+json"}
        if config.github_token:
            headers["Authorization"] = f"token {config.github_token}"

        repos_response = requests.get(repos_url, headers=headers, timeout=30)
        repos_response.raise_for_status()
        repos = repos_response.json()

        context.log.info(f"Found {len(repos)} repositories for user {config.github_username}")

        all_stats = []

        for repo in repos:
            repo_name = repo["name"]
            repo_full_name = repo["full_name"]
            context.log.info(f"Fetching stats for repository: {repo_full_name}")

            # Fetch different types of statistics
            stat_types = [
                ("contributors", f"/repos/{repo_full_name}/stats/contributors"),
                ("commit_activity", f"/repos/{repo_full_name}/stats/commit_activity"),
                ("code_frequency", f"/repos/{repo_full_name}/stats/code_frequency"),
                ("participation", f"/repos/{repo_full_name}/stats/participation"),
            ]

            repo_stats = {
                "repo_name": repo_name,
                "repo_full_name": repo_full_name,
                "repo_id": repo["id"],
                "collection_date": partition_date,
                "_cascade_ingested_at": datetime.utcnow(),
            }

            for stat_type, endpoint in stat_types:
                try:
                    stat_url = f"{config.github_base_url}{endpoint}"
                    stat_response = requests.get(stat_url, headers=headers, timeout=60)
                    stat_response.raise_for_status()
                    stat_data = stat_response.json()

                    # Store the stat data with a key prefix
                    if stat_data:
                        repo_stats[f"{stat_type}_data"] = stat_data
                        context.log.debug(f"Retrieved {stat_type} stats for {repo_full_name}")
                    else:
                        context.log.debug(f"No {stat_type} stats available for {repo_full_name}")

                except requests.HTTPError as e:
                    if e.response.status_code == 202:
                        # GitHub is computing stats, will be available later
                        context.log.info(f"Stats for {repo_full_name} are being computed by GitHub")
                    elif e.response.status_code == 204:
                        # No stats available for this repo
                        context.log.debug(f"No {stat_type} stats for {repo_full_name}")
                    else:
                        context.log.warning(f"Failed to get {stat_type} stats for {repo_full_name}: {e}")
                except Exception as e:
                    context.log.warning(f"Error fetching {stat_type} stats for {repo_full_name}: {e}")

            all_stats.append(repo_stats)

        context.log.info(f"Successfully collected stats for {len(all_stats)} repositories")

        if not all_stats:
            context.log.info(f"No repository stats collected for partition {partition_date}, skipping")
            return dg.MaterializeResult(
                metadata={
                    "partition_date": dg.MetadataValue.text(partition_date),
                    "rows_loaded": dg.MetadataValue.int(0),
                    "status": dg.MetadataValue.text("no_data"),
                }
            )

        # Step 2: Stage to S3 parquet using DLT
        context.log.info("Staging data to parquet via DLT...")
        start_time_ts = time.time()

        staging_path = get_staging_path(partition_date, "repo_stats")
        local_staging_root = (pipelines_base_dir / pipeline_name / "stage").resolve()
        local_staging_root.mkdir(parents=True, exist_ok=True)

        # Create DLT pipeline with filesystem destination targeting local staging
        filesystem_destination = dlt.destinations.filesystem(
            bucket_url=local_staging_root.as_uri(),
        )

        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            destination=filesystem_destination,
            dataset_name="github",
            pipelines_dir=str(pipelines_base_dir),
        )

        @dlt.resource(name="repo_stats", write_disposition="replace")
        def provide_repo_stats() -> Any:
            yield all_stats

        # Run DLT pipeline to stage parquet files
        info = pipeline.run(
            provide_repo_stats(),
            loader_file_format="parquet",
        )

        if not info.load_packages:
            raise RuntimeError("DLT pipeline produced no load packages")

        load_package = info.load_packages[0]
        completed_jobs = load_package.jobs.get("completed_jobs") or []
        if not completed_jobs:
            raise RuntimeError("DLT pipeline completed without producing parquet output")

        parquet_path = Path(completed_jobs[0].file_path)
        if not parquet_path.is_absolute():
            parquet_path = (local_staging_root / parquet_path).resolve()

        context.log.debug(
            "DLT staged parquet to %s (logical %s)",
            parquet_path,
            staging_path,
        )

        dlt_elapsed = time.time() - start_time_ts
        context.log.info(f"DLT staging completed in {dlt_elapsed:.2f}s")

        # Step 3: Ensure Iceberg table exists
        context.log.info(f"Ensuring Iceberg table {table_name} exists...")
        from cascade.iceberg.schema import get_schema
        schema = get_schema("repo_stats")
        iceberg.ensure_table(
            table_name=table_name,
            schema=schema,
            partition_spec=None,
        )

        # Step 4: Append to Iceberg table
        context.log.info("Appending data to Iceberg table...")
        iceberg.append_parquet(table_name=table_name, data_path=str(parquet_path))

        total_elapsed = time.time() - start_time_ts
        rows_loaded = len(all_stats)
        context.log.info(f"Ingestion completed successfully in {total_elapsed:.2f}s")
        context.log.info(f"Loaded {rows_loaded} rows to {table_name}")

        return dg.MaterializeResult(
            metadata={
                "partition_date": dg.MetadataValue.text(partition_date),
                "rows_loaded": dg.MetadataValue.int(rows_loaded),
                "table_name": dg.MetadataValue.text(table_name),
                "dlt_elapsed_seconds": dg.MetadataValue.float(dlt_elapsed),
                "total_elapsed_seconds": dg.MetadataValue.float(total_elapsed),
            }
        )

    except requests.RequestException as e:
        context.log.error(f"API request failed for partition {partition_date}: {e}")
        raise RuntimeError(
            f"Failed to fetch data from GitHub API for partition {partition_date}"
        ) from e

    except Exception as e:
        context.log.error(f"Ingestion failed for partition {partition_date}: {e}")
        raise RuntimeError(f"Ingestion failed for partition {partition_date}: {e}") from e
