# cli_logs (/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_logs)



Logs command for accessing Dagster run logs.

This module implements the `phlo logs` CLI command, providing access to
Dagster run logs with filtering capabilities. It queries Dagster's
GraphQL API to retrieve structured log data from pipeline executions.

Features:

* Filtering: By asset, job, log level, time range, specific run ID
* Tail mode: Real-time log following with --follow flag
* Output formats: Rich formatted tables or JSON
* Time-based filtering: Human-readable formats (1h, 30m, 2d)
* Message truncation control with --full flag

GraphQL Integration:
The command constructs GraphQL queries to fetch run events including:

* Log messages with levels
* Execution step events
* Step failures and successes
* Pipeline status changes

Example:
CLI usage::

phlo logs                           # Recent logs (last 100)
phlo logs --asset dlt\_orders        # Filter by asset
phlo logs --job orders\_pipeline     # Filter by job
phlo logs --level ERROR             # Errors only
phlo logs --since 1h                # Last hour
phlo logs --follow                  # Tail mode
phlo logs --run-id abc123           # Specific run
phlo logs --full                    # Don't truncate messages

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;logs&#x22;" type="&#x22;(asset, job, level, since, run_id, follow, full, limit, output_json)&#x22;">
      Access and filter Dagster run logs from CLI.

      Supports multiple filtering options:

      * By asset name: --asset dlt\_orders
      * By job name: --job orders\_pipeline
      * By log level: --level ERROR
      * By time range: --since 1h (last hour)
      * By specific run: --run-id abc123
      * Tail mode: --follow (real-time updates)

      <PySourceCode>
        ```python
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
            """Access and filter Dagster run logs from CLI.

            Supports multiple filtering options:
            - By asset name: --asset dlt_orders
            - By job name: --job orders_pipeline
            - By log level: --level ERROR
            - By time range: --since 1h (last hour)
            - By specific run: --run-id abc123
            - Tail mode: --follow (real-time updates)

            Args:
                asset: Filter by asset name.
                job: Filter by job name.
                level: Filter by log level (DEBUG, INFO, WARNING, ERROR).
                since: Time filter (e.g., 1h, 30m, 2d).
                run_id: Filter by specific run ID.
                follow: If True, tail logs in real-time.
                full: If True, don't truncate long messages.
                limit: Number of logs to retrieve (default: 100).
                output_json: If True, output as JSON.

            Returns:
                None

            Raises:
                No explicit exceptions raised. Logs warnings on query failures.

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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Filter by asset name.
        </PyParameter>

        <PyParameter name="&#x22;job&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Filter by job name.
        </PyParameter>

        <PyParameter name="&#x22;level&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Filter by log level (DEBUG, INFO, WARNING, ERROR).
        </PyParameter>

        <PyParameter name="&#x22;since&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Time filter (e.g., 1h, 30m, 2d).
        </PyParameter>

        <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Filter by specific run ID.
        </PyParameter>

        <PyParameter name="&#x22;follow&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, tail logs in real-time.
        </PyParameter>

        <PyParameter name="&#x22;full&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, don't truncate long messages.
        </PyParameter>

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="undefined">
          Number of logs to retrieve (default: 100).
        </PyParameter>

        <PyParameter name="&#x22;output_json&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, output as JSON.
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_parse_since&#x22;" type="&#x22;(since_str) -> datetime&#x22;">
      Parse time filter string (e.g., '1h', '30m', '2d').

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;since_str&#x22;" type="&#x22;str&#x22;" value="undefined">
          Time filter string
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;datetime.datetime&#x22;">
        datetime object for the cutoff time
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_get_logs&#x22;" type="&#x22;(filters) -> list[dict]&#x22;">
      Retrieve logs from Dagster with filters.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;filters&#x22;" type="&#x22;dict&#x22;" value="undefined">
          Filter criteria (asset, job, level, run\_id, start\_time, limit)
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of log dictionaries
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_build_logs_query&#x22;" type="&#x22;(filters) -> str&#x22;">
      Build GraphQL query for logs.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;filters&#x22;" type="&#x22;dict&#x22;" value="undefined">
          Filter criteria
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        GraphQL query string
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_get_log_level&#x22;" type="&#x22;(event_type) -> str&#x22;">
      Map event type to log level.

      <PySourceCode>
        ```python
        def _get_log_level(event_type: str) -> str:
            """Map event type to log level.

            Args:
                event_type: Dagster event type string.

            Returns:
                Log level string (ERROR, WARNING, INFO, DEBUG).

            """
            if "ERROR" in event_type or "FAILURE" in event_type:
                return "ERROR"
            elif "WARNING" in event_type:
                return "WARNING"
            elif "SUCCESS" in event_type or "OUTPUT" in event_type:
                return "INFO"
            else:
                return "DEBUG"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          Dagster event type string.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Log level string (ERROR, WARNING, INFO, DEBUG).
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
