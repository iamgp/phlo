# loki (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/loki)



Loki Log Querying API Router.

Endpoints for querying logs from Loki.
Supports correlation by run\_id, asset\_key, job\_name, and partition\_key.

This module provides a unified interface to query structured logs from
the Loki log aggregation system. It supports filtering by various
correlation IDs to enable debugging of data pipelines and operations.

Key Endpoints:
GET /connection: Check Loki connectivity.
GET /query: Query logs with filters.
GET /runs/\{run\_id}: Query logs for a specific Dagster run.
GET /assets/\{asset\_key}: Query logs for a specific asset.
GET /labels: Get available log label keys.

Environment Variables:
LOKI\_URL: URL for the Loki server.

Example:
Querying logs for a Dagster run:

.. code-block:: bash

curl [http://localhost:4000/api/loki/runs/abc-123](http://localhost:4000/api/loki/runs/abc-123)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['loki'])&#x22;" />

<PyAttribute name="&#x22;DEFAULT_LOKI_URL&#x22;" type="null" value="&#x22;'http://loki:3100'&#x22;" />

<PyAttribute name="&#x22;LogLevel&#x22;" type="null" value="&#x22;Literal['debug', 'info', 'warn', 'error']&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LogEntry&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/loki/LogEntry&#x22;" />

      <Card title="&#x22;LogQueryResult&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/loki/LogQueryResult&#x22;" />

      <Card title="&#x22;LokiConnectionStatus&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/loki/LokiConnectionStatus&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_loki_url&#x22;" type="&#x22;(override=None) -> str&#x22;">
      Resolve the Loki base URL.

      <PySourceCode>
        ```python
        def resolve_loki_url(override: str | None = None) -> str:
            """Resolve the Loki base URL.

            Args:
                override: Optional explicit Loki URL.

            Returns:
                Loki URL from override, environment, or default.

            """
            if override and override.strip():
                return override
            return os.environ.get("LOKI_URL", DEFAULT_LOKI_URL)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;override&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional explicit Loki URL.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Loki URL from override, environment, or default.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;build_log_query&#x22;" type="&#x22;(run_id=None, asset_key=None, job=None, partition_key=None, check_name=None, level=None, service=None) -> str&#x22;">
      Build a LogQL query with optional filters.

      <PySourceCode>
        ```python
        def build_log_query(
            run_id: str | None = None,
            asset_key: str | None = None,
            job: str | None = None,
            partition_key: str | None = None,
            check_name: str | None = None,
            level: LogLevel | None = None,
            service: str | None = None,
        ) -> str:
            """Build a LogQL query with optional filters.

            Args:
                run_id: Optional Dagster run identifier.
                asset_key: Optional asset key filter.
                job: Optional job name filter.
                partition_key: Optional partition key filter.
                check_name: Optional check name filter.
                level: Optional log level filter.
                service: Optional service/container selector.

            Returns:
                LogQL query string.

            """
            label_matchers = []
            json_filters = []

            # Service filter - required by Loki
            if service:
                label_matchers.append(f'container=~".*{service}.*"')
            else:
                label_matchers.append('container=~".+"')

            # JSON filters for correlation
            if run_id:
                json_filters.append(f'run_id="{run_id}"')
            if asset_key:
                json_filters.append(f'asset_key="{asset_key}"')
            if job:
                json_filters.append(f'job_name="{job}"')
            if partition_key:
                json_filters.append(f'partition_key="{partition_key}"')
            if check_name:
                json_filters.append(f'check_name="{check_name}"')
            if level:
                json_filters.append(f'level="{level}"')

            label_selector = ", ".join(label_matchers)
            json_pipeline = " | json | " + " | ".join(json_filters) if json_filters else " | json"

            return "{" + label_selector + "}" + json_pipeline
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster run identifier.
        </PyParameter>

        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional asset key filter.
        </PyParameter>

        <PyParameter name="&#x22;job&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional job name filter.
        </PyParameter>

        <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional partition key filter.
        </PyParameter>

        <PyParameter name="&#x22;check_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional check name filter.
        </PyParameter>

        <PyParameter name="&#x22;level&#x22;" type="&#x22;LogLevel | None&#x22;" value="&#x22;None&#x22;">
          Optional log level filter.
        </PyParameter>

        <PyParameter name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional service/container selector.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        LogQL query string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;parse_loki_response&#x22;" type="&#x22;(response) -> list[LogEntry]&#x22;">
      Parse Loki query response into log entries.

      <PySourceCode>
        ```python
        def parse_loki_response(response: dict[str, Any]) -> list[LogEntry]:
            """Parse Loki query response into log entries.

            Args:
                response: Loki query API response payload.

            Returns:
                Parsed log entries sorted by timestamp descending.

            """
            entries = []

            for stream in response.get("data", {}).get("result", []):
                stream_labels = stream.get("stream", {})
                for timestamp_ns, line in stream.get("values", []):
                    try:
                        parsed = json.loads(line)
                        entries.append(
                            LogEntry(
                                timestamp=datetime.fromtimestamp(
                                    int(timestamp_ns) / 1_000_000_000
                                ).isoformat(),
                                level=parsed.get("level", "info"),
                                message=parsed.get("msg") or parsed.get("message") or line,
                                metadata={
                                    k: v
                                    for k, v in {
                                        "run_id": parsed.get("run_id"),
                                        "asset_key": parsed.get("asset_key"),
                                        "job_name": parsed.get("job_name"),
                                        "partition_key": parsed.get("partition_key"),
                                        "fn": parsed.get("fn"),
                                        "durationMs": str(parsed.get("durationMs"))
                                        if parsed.get("durationMs")
                                        else None,
                                    }.items()
                                    if v
                                },
                            )
                        )
                    except Exception:
                        # Non-JSON log line
                        entries.append(
                            LogEntry(
                                timestamp=datetime.fromtimestamp(
                                    int(timestamp_ns) / 1_000_000_000
                                ).isoformat(),
                                level="info",
                                message=line,
                                metadata=stream_labels,
                            )
                        )

            # Sort by timestamp descending
            entries.sort(key=lambda e: e.timestamp, reverse=True)
            return entries
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;response&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Loki query API response payload.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Parsed log entries sorted by timestamp descending.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;check_connection&#x22;" type="&#x22;(loki_url=None) -> LokiConnectionStatus&#x22;">
      Check whether Loki is reachable.

      <PySourceCode>
        ```python
        @router.get("/connection", response_model=LokiConnectionStatus)
        async def check_connection(loki_url: str | None = None) -> LokiConnectionStatus:
            """Check whether Loki is reachable.

            Args:
                loki_url: Optional Loki URL override.

            Returns:
                LokiConnectionStatus with connection state and version info.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_loki_url(loki_url)

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{url}/ready")

                    if response.status_code != 200:
                        return LokiConnectionStatus(
                            connected=False,
                            error=f"HTTP {response.status_code}: {response.reason_phrase}",
                        )

                    # Get version
                    try:
                        build_response = await client.get(f"{url}/loki/api/v1/status/buildinfo")
                        version = (
                            build_response.json().get("version", "unknown")
                            if build_response.status_code == 200
                            else "unknown"
                        )
                    except Exception:
                        version = "unknown"

                    return LokiConnectionStatus(connected=True, version=version)
            except Exception as e:
                return LokiConnectionStatus(connected=False, error=str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;loki_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Loki URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.loki.LokiConnectionStatus&#x22;">
        LokiConnectionStatus with connection state and version info.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;query_logs&#x22;" type="&#x22;(start, end, run_id=None, asset_key=None, job=None, partition_key=None, check_name=None, level=None, service=None, limit=Query(default=100, le=1000), loki_url=None) -> LogQueryResult | dict[str, str]&#x22;">
      Query logs with correlation filters.

      Executes a LogQL query against Loki with optional filters for run\_id,
      asset\_key, job, partition\_key, check\_name, level, and service.

      <PySourceCode>
        ```python
        @router.get("/query", response_model=LogQueryResult | dict)
        async def query_logs(
            start: str,
            end: str,
            run_id: str | None = None,
            asset_key: str | None = None,
            job: str | None = None,
            partition_key: str | None = None,
            check_name: str | None = None,
            level: LogLevel | None = None,
            service: str | None = None,
            limit: int = Query(default=100, le=1000),
            loki_url: str | None = None,
        ) -> LogQueryResult | dict[str, str]:
            """Query logs with correlation filters.

            Executes a LogQL query against Loki with optional filters for run_id,
            asset_key, job, partition_key, check_name, level, and service.

            Args:
                start: Query start time as ISO 8601 timestamp.
                end: Query end time as ISO 8601 timestamp.
                run_id: Optional Dagster run identifier filter.
                asset_key: Optional asset key filter.
                job: Optional job name filter.
                partition_key: Optional partition key filter.
                check_name: Optional check name filter.
                level: Optional log level filter (debug, info, warn, error).
                service: Optional service/container selector.
                limit: Maximum number of log entries (default: 100, max: 1000).
                loki_url: Optional Loki URL override.

            Returns:
                LogQueryResult with entries and has_more flag, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_loki_url(loki_url)

            try:
                query = build_log_query(run_id, asset_key, job, partition_key, check_name, level, service)

                # Convert ISO timestamps to nanoseconds
                start_ns = int(
                    datetime.fromisoformat(start.replace("Z", "+00:00")).timestamp() * 1_000_000_000
                )
                end_ns = int(datetime.fromisoformat(end.replace("Z", "+00:00")).timestamp() * 1_000_000_000)

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{url}/loki/api/v1/query_range",
                        params={
                            "query": query,
                            "start": str(start_ns),
                            "end": str(end_ns),
                            "limit": str(limit),
                            "direction": "backward",
                        },
                    )
                    response.raise_for_status()
                    result = response.json()

                    entries = parse_loki_response(result)
                    return LogQueryResult(entries=entries, has_more=len(entries) == limit)
            except Exception as e:
                logger.exception("Failed to query logs")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;start&#x22;" type="&#x22;str&#x22;" value="undefined">
          Query start time as ISO 8601 timestamp.
        </PyParameter>

        <PyParameter name="&#x22;end&#x22;" type="&#x22;str&#x22;" value="undefined">
          Query end time as ISO 8601 timestamp.
        </PyParameter>

        <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster run identifier filter.
        </PyParameter>

        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional asset key filter.
        </PyParameter>

        <PyParameter name="&#x22;job&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional job name filter.
        </PyParameter>

        <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional partition key filter.
        </PyParameter>

        <PyParameter name="&#x22;check_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional check name filter.
        </PyParameter>

        <PyParameter name="&#x22;level&#x22;" type="&#x22;LogLevel | None&#x22;" value="&#x22;None&#x22;">
          Optional log level filter (debug, info, warn, error).
        </PyParameter>

        <PyParameter name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional service/container selector.
        </PyParameter>

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=100, le=1000)&#x22;">
          Maximum number of log entries (default: 100, max: 1000).
        </PyParameter>

        <PyParameter name="&#x22;loki_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Loki URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;LogQueryResult | dict[str, str]&#x22;">
        LogQueryResult with entries and has\_more flag, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;query_run_logs&#x22;" type="&#x22;(run_id, level=None, limit=Query(default=500, le=2000), loki_url=None) -> LogQueryResult | dict[str, str]&#x22;">
      Query logs for a Dagster run.

      <PySourceCode>
        ```python
        @router.get("/runs/{run_id}", response_model=LogQueryResult | dict)
        async def query_run_logs(
            run_id: str,
            level: LogLevel | None = None,
            limit: int = Query(default=500, le=2000),
            loki_url: str | None = None,
        ) -> LogQueryResult | dict[str, str]:
            """Query logs for a Dagster run.

            Args:
                run_id: Dagster run identifier.
                level: Optional log level filter.
                limit: Maximum number of log entries.
                loki_url: Optional Loki URL override.

            Returns:
                Query result with log entries or an error dictionary.

            """
            # Query last 24 hours
            end = datetime.now()
            start = end - timedelta(hours=24)

            return await query_logs(
                start=start.isoformat(),
                end=end.isoformat(),
                run_id=run_id,
                level=level,
                limit=limit,
                loki_url=loki_url,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str&#x22;" value="undefined">
          Dagster run identifier.
        </PyParameter>

        <PyParameter name="&#x22;level&#x22;" type="&#x22;LogLevel | None&#x22;" value="&#x22;None&#x22;">
          Optional log level filter.
        </PyParameter>

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=500, le=2000)&#x22;">
          Maximum number of log entries.
        </PyParameter>

        <PyParameter name="&#x22;loki_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Loki URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;LogQueryResult | dict[str, str]&#x22;">
        Query result with log entries or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;query_asset_logs&#x22;" type="&#x22;(asset_key, partition_key=None, level=None, hours_back=Query(default=24, le=168), limit=Query(default=200, le=1000), loki_url=None) -> LogQueryResult | dict[str, str]&#x22;">
      Query logs for an asset.

      <PySourceCode>
        ```python
        @router.get("/assets/{asset_key:path}", response_model=LogQueryResult | dict)
        async def query_asset_logs(
            asset_key: str,
            partition_key: str | None = None,
            level: LogLevel | None = None,
            hours_back: int = Query(default=24, le=168),
            limit: int = Query(default=200, le=1000),
            loki_url: str | None = None,
        ) -> LogQueryResult | dict[str, str]:
            """Query logs for an asset.

            Args:
                asset_key: Asset key.
                partition_key: Optional partition key filter.
                level: Optional log level filter.
                hours_back: Hours to include before now.
                limit: Maximum number of log entries.
                loki_url: Optional Loki URL override.

            Returns:
                Query result with log entries or an error dictionary.

            """
            end = datetime.now()
            start = end - timedelta(hours=hours_back)

            return await query_logs(
                start=start.isoformat(),
                end=end.isoformat(),
                asset_key=asset_key,
                partition_key=partition_key,
                level=level,
                limit=limit,
                loki_url=loki_url,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset key.
        </PyParameter>

        <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional partition key filter.
        </PyParameter>

        <PyParameter name="&#x22;level&#x22;" type="&#x22;LogLevel | None&#x22;" value="&#x22;None&#x22;">
          Optional log level filter.
        </PyParameter>

        <PyParameter name="&#x22;hours_back&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=24, le=168)&#x22;">
          Hours to include before now.
        </PyParameter>

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=200, le=1000)&#x22;">
          Maximum number of log entries.
        </PyParameter>

        <PyParameter name="&#x22;loki_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Loki URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;LogQueryResult | dict[str, str]&#x22;">
        Query result with log entries or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_log_labels&#x22;" type="&#x22;(loki_url=None) -> dict[str, Any]&#x22;">
      Get available Loki label keys.

      <PySourceCode>
        ```python
        @router.get("/labels", response_model=dict)
        async def get_log_labels(loki_url: str | None = None) -> dict[str, Any]:
            """Get available Loki label keys.

            Args:
                loki_url: Optional Loki URL override.

            Returns:
                Label key list payload or an error dictionary.

            """
            url = resolve_loki_url(loki_url)

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{url}/loki/api/v1/labels")
                    response.raise_for_status()
                    result = response.json()
                    return {"labels": result.get("data", [])}
            except Exception as e:
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;loki_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Loki URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Label key list payload or an error dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
