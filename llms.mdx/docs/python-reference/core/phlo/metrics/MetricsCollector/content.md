# MetricsCollector (/docs/python-reference/core/phlo/metrics/MetricsCollector)



Collect metrics from Prometheus, Iceberg, and Postgres.

Attributes [#attributes]

<PyAttribute name="&#x22;settings&#x22;" type="null" value="&#x22;MetricsBackendSettings()&#x22;" />

<PyAttribute name="&#x22;prometheus_url&#x22;" type="&#x22;str | None&#x22;" value="null">
  Get Prometheus URL from config or environment.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  <PySourceCode>
    ```python
    def __init__(self) -> None:
        self.settings = MetricsBackendSettings()
        self._cache = TTLCache(maxsize=100, ttl=30)
        self._prometheus_url: str | None = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;collect_summary&#x22;" type="&#x22;(self, period_hours=24) -> SummaryMetrics&#x22;">
  Collect summary metrics for the platform.

  <PySourceCode>
    ```python
    def collect_summary(self, period_hours: int = 24) -> SummaryMetrics:
        """Collect summary metrics for the platform."""
        cache_key = f"summary_{period_hours}h"
        if cache_key in self._cache:
            return self._cache[cache_key]

        metrics = SummaryMetrics()

        try:
            metrics = cast(SummaryMetrics, self._collect_from_prometheus(period_hours))
        except Exception:
            logger.warning(
                "metrics_collect_prometheus_failed", period_hours=period_hours, exc_info=True
            )

        try:
            postgres_metrics = self._collect_from_postgres(period_hours)
            metrics.total_rows_processed_24h = postgres_metrics.get("rows_processed", 0)
            metrics.total_bytes_written_24h = postgres_metrics.get("bytes_written", 0)
        except Exception:
            logger.warning(
                "metrics_collect_postgres_failed", period_hours=period_hours, exc_info=True
            )

        try:
            iceberg_metrics = self._collect_from_iceberg()
            metrics.active_assets_count = int(iceberg_metrics.get("table_count", 0) or 0)
            metrics.data_growth_bytes = int(iceberg_metrics.get("total_bytes", 0) or 0)
        except Exception:
            logger.warning(
                "metrics_collect_iceberg_failed", period_hours=period_hours, exc_info=True
            )

        self._cache[cache_key] = metrics
        return metrics
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;period_hours&#x22;" type="&#x22;int&#x22;" value="&#x22;24&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.metrics.SummaryMetrics&#x22;" />
</PyFunction>

<PyFunction name="&#x22;collect_asset&#x22;" type="&#x22;(self, asset_name, runs=10) -> AssetMetrics&#x22;">
  Collect metrics for a specific asset.

  <PySourceCode>
    ```python
    def collect_asset(self, asset_name: str, runs: int = 10) -> AssetMetrics:
        """Collect metrics for a specific asset."""
        cache_key = f"asset_{asset_name}_{runs}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        metrics = AssetMetrics(asset_name=asset_name)

        try:
            run_records = self._get_asset_runs_from_postgres(asset_name, limit=runs)
            if run_records:
                metrics.last_10_runs = run_records
                metrics.last_run = run_records[0]

                durations = [
                    record.duration_seconds
                    for record in run_records
                    if record.duration_seconds is not None
                ]
                if durations:
                    metrics.average_duration = sum(durations) / len(durations)

                successful = sum(1 for record in run_records if record.status == "success")
                metrics.failure_rate = 1.0 - (successful / len(run_records))
                metrics.average_rows_per_run = sum(
                    record.rows_processed for record in run_records
                ) / len(run_records)
        except Exception:
            logger.warning(
                "asset_metrics_collect_failed",
                asset_name=asset_name,
                runs=runs,
                exc_info=True,
            )

        try:
            iceberg_metrics = self._get_iceberg_table_stats(asset_name)
            metrics.data_growth_bytes = iceberg_metrics.get("total_bytes", 0)
        except Exception:
            logger.warning("asset_iceberg_stats_failed", asset_name=asset_name, exc_info=True)

        self._cache[cache_key] = metrics
        return metrics
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;runs&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.metrics.AssetMetrics&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_collect_from_prometheus&#x22;" type="&#x22;(self, period_hours) -> SummaryMetrics&#x22;">
  Collect metrics from Prometheus.

  <PySourceCode>
    ```python
    def _collect_from_prometheus(self, period_hours: int) -> SummaryMetrics:
        """Collect metrics from Prometheus."""
        metrics = SummaryMetrics()
        if not self.prometheus_url:
            return metrics

        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={
                    "query": f'increase(dagster_runs_total{{status="success"}}[{period_hours}h])'
                },
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("result"):
                    value = data["data"]["result"][0].get("value", [None, "0"])
                    metrics.successful_runs_24h = int(float(value[1]))

            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={
                    "query": f'increase(dagster_runs_total{{status="failure"}}[{period_hours}h])'
                },
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("result"):
                    value = data["data"]["result"][0].get("value", [None, "0"])
                    metrics.failed_runs_24h = int(float(value[1]))

            metrics.total_runs_24h = metrics.successful_runs_24h + metrics.failed_runs_24h

            for percentile in ["0.5", "0.95", "0.99"]:
                response = requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={
                        "query": (
                            f"histogram_quantile({percentile}, "
                            f"dagster_run_duration_seconds[{period_hours}h])"
                        )
                    },
                    timeout=5,
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("result"):
                        value = data["data"]["result"][0].get("value", [None, "0"])
                        duration = float(value[1])
                        if percentile == "0.5":
                            metrics.p50_duration_seconds = duration
                        elif percentile == "0.95":
                            metrics.p95_duration_seconds = duration
                        else:
                            metrics.p99_duration_seconds = duration
        except Exception:
            logger.debug("prometheus_collection_failed", period_hours=period_hours, exc_info=True)

        return metrics
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;period_hours&#x22;" type="&#x22;int&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.metrics.SummaryMetrics&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_collect_from_postgres&#x22;" type="&#x22;(self, period_hours) -> dict[str, Any]&#x22;">
  Collect metrics from Postgres.

  <PySourceCode>
    ```python
    def _collect_from_postgres(self, period_hours: int) -> dict[str, Any]:
        """Collect metrics from Postgres."""
        metrics: dict[str, Any] = {}
        try:
            conn = psycopg2.connect(
                host=self.settings.postgres_host,
                port=self.settings.postgres_port,
                database=self.settings.postgres_db,
                user=self.settings.postgres_user,
                password=self.settings.postgres_password,
            )
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            since = datetime.now(UTC) - timedelta(hours=period_hours)
            cur.execute(
                """
                SELECT
                    COUNT(*) as run_count,
                    SUM(CASE WHEN event_type = 'PIPELINE_SUCCESS' THEN 1 ELSE 0 END) as success_count
                FROM dagster_event_logs
                WHERE timestamp > %s
                """,
                (since,),
            )
            row = cur.fetchone()
            if row:
                metrics["runs"] = row["run_count"] or 0
                metrics["successful_runs"] = row["success_count"] or 0
            conn.close()
        except Exception:
            logger.debug(
                "postgres_metrics_collection_failed", period_hours=period_hours, exc_info=True
            )
        return metrics
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;period_hours&#x22;" type="&#x22;int&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_collect_from_iceberg&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Collect metrics from Iceberg/Nessie.

  <PySourceCode>
    ```python
    def _collect_from_iceberg(self) -> dict[str, Any]:
        """Collect metrics from Iceberg/Nessie."""
        metrics: dict[str, Any] = {}
        try:
            nessie_url = self.settings.nessie_api_uri()
            response = requests.get(f"{nessie_url}/trees", timeout=5)
            if response.status_code == 200:
                data = response.json()
                tables_count = 0
                namespaces = data.get("trees", [])
                for namespace in namespaces:
                    ns_name = namespace.get("name")
                    if not ns_name:
                        continue
                    try:
                        ns_response = requests.get(
                            f"{nessie_url}/namespaces/{ns_name}/tables",
                            timeout=5,
                        )
                        if ns_response.status_code == 200:
                            tables_count += len(ns_response.json().get("tables", []))
                    except Exception:
                        continue
                metrics["table_count"] = tables_count
                metrics["total_bytes"] = 0
        except Exception:
            logger.debug("iceberg_metrics_collection_failed", exc_info=True)
        return metrics
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_get_asset_runs_from_postgres&#x22;" type="&#x22;(self, asset_name, limit=10) -> list[RunMetrics]&#x22;">
  Get past runs for an asset from Postgres.

  <PySourceCode>
    ```python
    def _get_asset_runs_from_postgres(self, asset_name: str, limit: int = 10) -> list[RunMetrics]:
        """Get past runs for an asset from Postgres."""
        try:
            conn = psycopg2.connect(
                host=self.settings.postgres_host,
                port=self.settings.postgres_port,
                database=self.settings.postgres_db,
                user=self.settings.postgres_user,
                password=self.settings.postgres_password,
            )
        except PsycopgError as exc:
            raise MetricsDependencyError("Postgres unavailable for asset run lookup") from exc

        try:
            escaped_asset_name = (
                asset_name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            with conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        r.run_id,
                        COALESCE(r.start_time, r.create_timestamp) AS start_time,
                        COALESCE(r.end_time, r.update_timestamp) AS end_time,
                        r.status
                    FROM dagster_runs AS r
                    LEFT JOIN run_tags AS t ON t.run_id = r.run_id
                    WHERE r.pipeline_name = %s
                       OR (
                           t.key = 'dagster/asset_selection'
                           AND t.value ILIKE %s ESCAPE '\\'
                       )
                    GROUP BY r.run_id, start_time, end_time, r.status
                    ORDER BY start_time DESC
                    LIMIT %s
                    """,
                    (asset_name, f"%{escaped_asset_name}%", limit),
                )
                rows = cur.fetchall()
        except PsycopgError as exc:
            raise MetricsDependencyError("Failed querying Dagster run history") from exc
        finally:
            conn.close()

        runs: list[RunMetrics] = []
        for row in rows:
            run_id = row.get("run_id")
            if not isinstance(run_id, str) or not run_id:
                raise MetricsMalformedResponseError("Dagster run row missing string run_id")
            start = self._coerce_datetime(row.get("start_time"), "start_time")
            end = self._coerce_datetime(row.get("end_time"), "end_time", allow_none=True)
            runs.append(
                RunMetrics(
                    asset_name=asset_name,
                    run_id=run_id,
                    start_time=start,
                    end_time=end,
                    duration_seconds=(end - start).total_seconds() if end is not None else None,
                    status=self._normalize_status(row.get("status")),
                )
            )
        return runs
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.metrics.RunMetrics]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_get_iceberg_table_stats&#x22;" type="&#x22;(self, table_name) -> dict[str, Any]&#x22;">
  Get table statistics from Iceberg.

  <PySourceCode>
    ```python
    def _get_iceberg_table_stats(self, table_name: str) -> dict[str, Any]:
        """Get table statistics from Iceberg."""
        query_engine = self._load_query_engine()
        catalog = self._resolve_query_engine_catalog()
        if "." in table_name:
            table_schema, raw_table = table_name.split(".", maxsplit=1)
        else:
            table_schema = self._resolve_table_schema(table_name, catalog, query_engine)
            raw_table = table_name

        safe_schema = self._validate_identifier(table_schema, "table_schema")
        safe_table = self._validate_identifier(raw_table, "table_name")
        escaped_files_table = f"{safe_table}$files"
        stats_sql = (
            f"SELECT COALESCE(SUM(file_size_in_bytes), 0), COALESCE(SUM(record_count), 0) "
            f'FROM {catalog}.{safe_schema}."{escaped_files_table}"'
        )

        try:
            row = query_engine.execute(stats_sql, schema=safe_schema)
        except Exception as exc:
            raise MetricsDependencyError(
                f"Failed querying Iceberg table stats for {table_name}"
            ) from exc

        if not isinstance(row, list) or len(row) != 1 or not isinstance(row[0], tuple):
            raise MetricsMalformedResponseError(
                f"Unexpected Iceberg table stats shape for {table_name}: {row!r}"
            )
        stats_row = row[0]
        if len(stats_row) != 2:
            raise MetricsMalformedResponseError(
                f"Unexpected Iceberg table stats shape for {table_name}: {row!r}"
            )

        return {
            "total_bytes": self._coerce_int(stats_row[0], "total_bytes"),
            "row_count": self._coerce_int(stats_row[1], "row_count"),
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_resolve_table_schema&#x22;" type="&#x22;(self, table_name, catalog, query_engine) -> str&#x22;">
  <PySourceCode>
    ```python
    def _resolve_table_schema(
        self, table_name: str, catalog: str, query_engine: QueryEngine
    ) -> str:
        safe_table_name = self._validate_identifier(table_name, "table_name")
        schema_sql = (
            f"SELECT table_schema FROM {catalog}.information_schema.tables "
            f"WHERE table_name = '{safe_table_name}' ORDER BY table_schema LIMIT 1"
        )
        try:
            rows = query_engine.execute(schema_sql)
        except Exception as exc:
            raise MetricsDependencyError(f"Failed resolving schema for {table_name}") from exc

        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], tuple):
            raise MetricsMalformedResponseError(
                f"Could not resolve Iceberg schema for table {table_name}"
            )
        row = rows[0]
        if not row or not isinstance(row[0], str) or not row[0]:
            raise MetricsMalformedResponseError(
                f"Could not resolve Iceberg schema for table {table_name}"
            )
        return self._validate_identifier(row[0], "table_schema")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;query_engine&#x22;" type="&#x22;QueryEngine&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_coerce_datetime&#x22;" type="&#x22;(self, value, field_name, *, allow_none=False) -> datetime | None&#x22;">
  <PySourceCode>
    ```python
    def _coerce_datetime(
        self, value: Any, field_name: str, *, allow_none: bool = False
    ) -> datetime | None:
        if value is None:
            if allow_none:
                return None
            raise MetricsMalformedResponseError(f"Missing required timestamp field {field_name}")
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=UTC)
        if isinstance(value, str):
            normal = value.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(normal)
            except ValueError as exc:
                raise MetricsMalformedResponseError(
                    f"Invalid datetime string for {field_name}: {value!r}"
                ) from exc
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        raise MetricsMalformedResponseError(
            f"Unsupported datetime value type for {field_name}: {type(value).__name__}"
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;field_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;allow_none&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;datetime.datetime | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_coerce_int&#x22;" type="&#x22;(self, value, field_name) -> int&#x22;">
  <PySourceCode>
    ```python
    def _coerce_int(self, value: Any, field_name: str) -> int:
        if isinstance(value, bool):
            raise MetricsMalformedResponseError(
                f"Invalid numeric value for {field_name}: {value!r}"
            )
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if not value.is_integer():
                raise MetricsMalformedResponseError(
                    f"Expected integer-compatible value for {field_name}, got {value!r}"
                )
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
                return int(stripped)
        raise MetricsMalformedResponseError(f"Invalid numeric value for {field_name}: {value!r}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;field_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_normalize_status&#x22;" type="&#x22;(self, value) -> str&#x22;">
  <PySourceCode>
    ```python
    def _normalize_status(self, value: Any) -> str:
        if not isinstance(value, str):
            raise MetricsMalformedResponseError(f"Invalid Dagster status value: {value!r}")
        normalized = value.lower()
        if normalized in {"success", "succeeded"}:
            return "success"
        if normalized in {"failure", "failed", "canceled", "cancelled"}:
            return "failure"
        if normalized in {"running", "started", "starting", "queued", "not_started"}:
            return "running"
        return normalized
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_validate_identifier&#x22;" type="&#x22;(self, value, field_name) -> str&#x22;">
  <PySourceCode>
    ```python
    def _validate_identifier(self, value: str, field_name: str) -> str:
        if not value:
            raise MetricsMalformedResponseError(f"Empty identifier for {field_name}")
        if not all(part and part.replace("_", "").isalnum() for part in value.split(".")):
            raise MetricsMalformedResponseError(f"Invalid identifier for {field_name}: {value!r}")
        return value
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;field_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_load_query_engine&#x22;" type="&#x22;(self) -> QueryEngine&#x22;">
  <PySourceCode>
    ```python
    def _load_query_engine(self) -> QueryEngine:
        discover_capabilities()
        resolution = resolve_capability("query_engine", self.settings.metrics_query_engine)
        if resolution is None:
            target = (
                f"query_engine:{self.settings.metrics_query_engine}"
                if self.settings.metrics_query_engine
                else "query_engine"
            )
            raise MetricsDependencyError(
                f"Query engine capability unavailable for Iceberg metrics ({target})"
            )
        return resolution.provider
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.QueryEngine&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_resolve_query_engine_catalog&#x22;" type="&#x22;(self) -> str&#x22;">
  <PySourceCode>
    ```python
    def _resolve_query_engine_catalog(self) -> str:
        if self.settings.metrics_query_catalog:
            return self._validate_identifier(
                self.settings.metrics_query_catalog,
                "metrics_query_catalog",
            )
        discover_capabilities()
        resolution = resolve_capability("query_engine", self.settings.metrics_query_engine)
        if resolution is None:
            target = (
                f"query_engine:{self.settings.metrics_query_engine}"
                if self.settings.metrics_query_engine
                else "query_engine"
            )
            raise MetricsDependencyError(
                f"Query engine capability unavailable for metrics catalog resolution ({target})"
            )
        for key in ("default_catalog", "catalog", "catalog_name"):
            value = resolution.metadata.get(key)
            if isinstance(value, str) and value:
                return self._validate_identifier(value, "metrics_query_catalog")
        raise MetricsDependencyError(
            "Query engine capability does not declare a default catalog and "
            "metrics_query_catalog is not configured."
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>
