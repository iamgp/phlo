# quality (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/quality)



Quality API Router.

Endpoints for aggregating quality check results from Dagster.
Powers the Quality Center dashboard and asset quality tabs.

This module queries the Dagster GraphQL API to fetch asset check
executions and statuses, normalizing the results into a quality
overview with categorization, scoring, and trending.

Key Endpoints:
GET /overview: Get aggregated quality metrics.
GET /assets/\{key}/checks: Get checks for a specific asset.
GET /assets/\{key}/checks/\{name}/history: Get execution history.
GET /failing: Get all currently failing checks.

Environment Variables:
DAGSTER\_GRAPHQL\_URL: URL for Dagster GraphQL endpoint.

Example:
Getting quality overview:

.. code-block:: bash

curl [http://localhost:4000/api/quality/overview](http://localhost:4000/api/quality/overview)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['quality'])&#x22;" />

<PyAttribute name="&#x22;DEFAULT_DAGSTER_URL&#x22;" type="null" value="&#x22;'http://dagster:3000/graphql'&#x22;" />

<PyAttribute name="&#x22;ASSET_CHECKS_QUERY&#x22;" type="null" value="&#x22;'\\nquery AssetChecksQuery {\\n    assetNodes {\\n        assetKey {\\n            path\\n        }\\n        assetChecksOrError {\\n            __typename\\n            ... on AssetChecks {\\n                checks {\\n                    name\\n                    description\\n                }\\n            }\\n            ... on AssetCheckNeedsMigrationError {\\n                message\\n            }\\n        }\\n    }\\n}\\n'&#x22;" />

<PyAttribute name="&#x22;ASSET_CHECK_EXECUTIONS_QUERY&#x22;" type="null" value="&#x22;'\\nquery AssetCheckExecutionsQuery($assetKey: AssetKeyInput!, $limit: Int!) {\\n    assetCheckExecutions(assetKey: $assetKey, limit: $limit) {\\n        status\\n        runId\\n        timestamp\\n        checkName\\n        evaluation {\\n            severity\\n            metadataEntries {\\n                __typename\\n                label\\n                ... on TextMetadataEntry { text }\\n                ... on IntMetadataEntry { intValue }\\n                ... on FloatMetadataEntry { floatValue }\\n                ... on BoolMetadataEntry { boolValue }\\n                ... on JsonMetadataEntry { jsonString }\\n            }\\n        }\\n    }\\n}\\n'&#x22;" />

<PyAttribute name="&#x22;CheckStatus&#x22;" type="null" value="&#x22;Literal['PASSED', 'FAILED', 'IN_PROGRESS', 'SKIPPED']&#x22;" />

<PyAttribute name="&#x22;Severity&#x22;" type="null" value="&#x22;Literal['WARN', 'ERROR']&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;CheckResult&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/quality/CheckResult&#x22;" />

      <Card title="&#x22;QualityCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/quality/QualityCheck&#x22;" />

      <Card title="&#x22;CategoryStats&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/quality/CategoryStats&#x22;" />

      <Card title="&#x22;RecentCheckExecution&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/quality/RecentCheckExecution&#x22;" />

      <Card title="&#x22;QualityOverview&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/quality/QualityOverview&#x22;" />

      <Card title="&#x22;CheckExecution&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/quality/CheckExecution&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_dagster_url&#x22;" type="&#x22;(override=None) -> str&#x22;">
      Resolve the Dagster GraphQL URL.

      <PySourceCode>
        ```python
        def resolve_dagster_url(override: str | None = None) -> str:
            """Resolve the Dagster GraphQL URL.

            Args:
                override: Optional explicit Dagster GraphQL URL.

            Returns:
                Dagster GraphQL URL from override, environment, or default.

            """
            if override and override.strip():
                return override
            return os.environ.get("DAGSTER_GRAPHQL_URL", DEFAULT_DAGSTER_URL)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;override&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional explicit Dagster GraphQL URL.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Dagster GraphQL URL from override, environment, or default.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;normalize_status&#x22;" type="&#x22;(status) -> CheckStatus&#x22;">
      Normalize a Dagster check execution status.

      <PySourceCode>
        ```python
        def normalize_status(status: str) -> CheckStatus:
            """Normalize a Dagster check execution status.

            Args:
                status: Raw status string from Dagster.

            Returns:
                Normalized check status.

            """
            normalized = status.strip().upper()
            if normalized == "SUCCEEDED":
                return "PASSED"
            if normalized == "FAILED":
                return "FAILED"
            if normalized == "IN_PROGRESS":
                return "IN_PROGRESS"
            return "SKIPPED"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="undefined">
          Raw status string from Dagster.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.quality.CheckStatus&#x22;">
        Normalized check status.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;normalize_severity&#x22;" type="&#x22;(severity) -> Severity&#x22;">
      Normalize a Dagster severity value.

      <PySourceCode>
        ```python
        def normalize_severity(severity: str | None) -> Severity:
            """Normalize a Dagster severity value.

            Args:
                severity: Raw severity value.

            Returns:
                Normalized severity.

            """
            return "WARN" if severity == "WARN" else "ERROR"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Raw severity value.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.quality.Severity&#x22;">
        Normalized severity.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;to_epoch_ms&#x22;" type="&#x22;(value) -> int&#x22;">
      Convert a timestamp value to epoch milliseconds.

      <PySourceCode>
        ```python
        def to_epoch_ms(value: str | int | float) -> int:
            """Convert a timestamp value to epoch milliseconds.

            Args:
                value: Timestamp as ISO string, seconds, or milliseconds.

            Returns:
                Timestamp in epoch milliseconds. Returns 0 when parsing fails.

            """
            if isinstance(value, (int, float)):
                if value > 1_000_000_000_000:
                    return int(value)
                return int(value * 1000)
            try:
                num = float(value.strip())
                if num > 1_000_000_000_000:
                    return int(num)
                return int(num * 1000)
            except ValueError:
                try:
                    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)
                except Exception:
                    return 0
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str | int | float&#x22;" value="undefined">
          Timestamp as ISO string, seconds, or milliseconds.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;">
        Timestamp in epoch milliseconds. Returns 0 when parsing fails.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;to_iso_timestamp&#x22;" type="&#x22;(value) -> str&#x22;">
      Convert a timestamp value to a UTC ISO 8601 string.

      <PySourceCode>
        ```python
        def to_iso_timestamp(value: str | int | float) -> str:
            """Convert a timestamp value to a UTC ISO 8601 string.

            Args:
                value: Timestamp as ISO string, seconds, or milliseconds.

            Returns:
                UTC ISO 8601 timestamp string.

            """
            return datetime.fromtimestamp(to_epoch_ms(value) / 1000, tz=timezone.utc).isoformat()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str | int | float&#x22;" value="undefined">
          Timestamp as ISO string, seconds, or milliseconds.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        UTC ISO 8601 timestamp string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;metadata_entries_to_dict&#x22;" type="&#x22;(entries) -> dict[str, Any]&#x22;">
      Convert Dagster metadata entries into a dictionary.

      <PySourceCode>
        ```python
        def metadata_entries_to_dict(entries: list[dict[str, Any]] | None) -> dict[str, Any]:
            """Convert Dagster metadata entries into a dictionary.

            Args:
                entries: Dagster metadata entry payload.

            Returns:
                Metadata keyed by entry label.

            """
            record: dict[str, Any] = {}
            if not entries:
                return record

            for entry in entries:
                label = entry.get("label")
                if not label:
                    continue
                typename = entry.get("__typename", "")
                if typename == "TextMetadataEntry":
                    record[label] = entry.get("text")
                elif typename == "IntMetadataEntry":
                    record[label] = entry.get("intValue")
                elif typename == "FloatMetadataEntry":
                    record[label] = entry.get("floatValue")
                elif typename == "BoolMetadataEntry":
                    record[label] = entry.get("boolValue")
                elif typename == "JsonMetadataEntry":
                    try:
                        record[label] = json.loads(entry.get("jsonString", "{}"))
                    except Exception:
                        record[label] = entry.get("jsonString")
            return record
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;entries&#x22;" type="&#x22;list[dict[str, Any]] | None&#x22;" value="undefined">
          Dagster metadata entry payload.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Metadata keyed by entry label.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;dagster_query&#x22;" type="&#x22;(client, url, query, variables) -> dict[str, Any] | None&#x22;">
      Execute a GraphQL query against Dagster.

      <PySourceCode>
        ```python
        async def dagster_query(
            client: httpx.AsyncClient, url: str, query: str, variables: dict[str, Any]
        ) -> dict[str, Any] | None:
            """Execute a GraphQL query against Dagster.

            Args:
                client: Shared async HTTP client.
                url: Dagster GraphQL endpoint.
                query: GraphQL query string.
                variables: GraphQL variables payload.

            Returns:
                GraphQL data payload, or `None` when the query fails.

            """
            try:
                response = await client.post(
                    url,
                    json={"query": query, "variables": variables},
                )
                response.raise_for_status()
                result = response.json()
                if result.get("errors"):
                    logger.error("dagster_graphql_error", errors=result["errors"])
                    return None
                return result.get("data")
            except Exception as exc:
                logger.error("dagster_query_failed", error=str(exc))
                return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;client&#x22;" type="&#x22;httpx.AsyncClient&#x22;" value="undefined">
          Shared async HTTP client.
        </PyParameter>

        <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="undefined">
          Dagster GraphQL endpoint.
        </PyParameter>

        <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
          GraphQL query string.
        </PyParameter>

        <PyParameter name="&#x22;variables&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          GraphQL variables payload.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict[str, Any] | None&#x22;">
        GraphQL data payload, or `None` when the query fails.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;fetch_quality_snapshot&#x22;" type="&#x22;(dagster_url, recent_limit=50) -> dict[str, Any] | None&#x22;">
      Fetch and aggregate quality data from Dagster.

      <PySourceCode>
        ```python
        async def fetch_quality_snapshot(dagster_url: str, recent_limit: int = 50) -> dict[str, Any] | None:
            """Fetch and aggregate quality data from Dagster.

            Args:
                dagster_url: Dagster GraphQL endpoint URL.
                recent_limit: Maximum recent executions to return.

            Returns:
                Aggregated quality snapshot, or `None` when fetch fails.

            """
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Get all assets with their checks
                assets_data = await dagster_query(client, dagster_url, ASSET_CHECKS_QUERY, {})
                if not assets_data:
                    return None

                asset_nodes = assets_data.get("assetNodes", [])

                # Filter assets that have checks
                assets_with_checks: list[dict[str, Any]] = []
                for node in asset_nodes:
                    checks_or_error = node.get("assetChecksOrError", {})
                    if checks_or_error.get("__typename") != "AssetChecks":
                        continue
                    checks = checks_or_error.get("checks", [])
                    if not checks:
                        continue
                    assets_with_checks.append(
                        {
                            "asset_key": node.get("assetKey", {}).get("path", []),
                            "checks": checks,
                        }
                    )

                # Step 2: Fetch executions for each asset
                total_checks = 0
                passing_checks = 0
                failing_checks = 0
                warning_checks = 0
                latest_checks: list[QualityCheck] = []
                failing_checks_list: list[QualityCheck] = []
                recent_executions: list[RecentCheckExecution] = []

                for asset in assets_with_checks:
                    asset_key = asset["asset_key"]
                    checks = asset["checks"]
                    per_asset_limit = max(50, len(checks) * 3)

                    exec_data = await dagster_query(
                        client,
                        dagster_url,
                        ASSET_CHECK_EXECUTIONS_QUERY,
                        {"assetKey": {"path": asset_key}, "limit": per_asset_limit},
                    )
                    if not exec_data:
                        continue

                    executions = exec_data.get("assetCheckExecutions", [])
                    total_checks += len(checks)

                    # Get newest execution per check
                    newest_by_check: dict[str, dict[str, Any]] = {}
                    for exec in executions:
                        check_name = exec.get("checkName")
                        if not check_name:
                            continue
                        existing = newest_by_check.get(check_name)
                        if not existing or to_epoch_ms(exec["timestamp"]) > to_epoch_ms(
                            existing["timestamp"]
                        ):
                            newest_by_check[check_name] = exec

                    # Build check records
                    for check_def in checks:
                        check_name = check_def.get("name")
                        latest = newest_by_check.get(check_name)
                        if not latest:
                            continue

                        status = normalize_status(latest.get("status", ""))
                        evaluation = latest.get("evaluation") or {}
                        severity = normalize_severity(evaluation.get("severity"))

                        check = QualityCheck(
                            name=check_name,
                            asset_key=asset_key,
                            description=check_def.get("description"),
                            severity=severity,
                            status=status,
                            last_execution_time=to_iso_timestamp(latest["timestamp"]),
                            last_result=CheckResult(
                                passed=status == "PASSED",
                                metadata=metadata_entries_to_dict(evaluation.get("metadataEntries")),
                            ),
                        )
                        latest_checks.append(check)

                        if status == "PASSED":
                            passing_checks += 1
                        elif status == "FAILED" and severity == "WARN":
                            warning_checks += 1
                        elif status == "FAILED":
                            failing_checks += 1
                            failing_checks_list.append(check)

                    # Build recent executions
                    for exec in executions:
                        evaluation = exec.get("evaluation") or {}
                        recent_executions.append(
                            RecentCheckExecution(
                                asset_key=asset_key,
                                check_name=exec.get("checkName", ""),
                                timestamp=to_iso_timestamp(exec["timestamp"]),
                                passed=normalize_status(exec.get("status", "")) == "PASSED",
                                run_id=exec.get("runId"),
                                severity=normalize_severity(evaluation.get("severity")),
                                status=normalize_status(exec.get("status", "")),
                                metadata=metadata_entries_to_dict(evaluation.get("metadataEntries")),
                            )
                        )

                # Sort recent executions by timestamp desc
                recent_executions.sort(key=lambda e: to_epoch_ms(e.timestamp), reverse=True)

                # Calculate quality score
                evaluated = passing_checks + failing_checks + warning_checks
                quality_score = (
                    round(((passing_checks + warning_checks) / evaluated) * 100) if evaluated > 0 else 0
                )

                # Calculate category stats
                categories = [
                    ("Contract (Pandera)", lambda c: c.name == "pandera_contract"),
                    ("dbt tests", lambda c: c.name.startswith("dbt__")),
                    (
                        "Custom",
                        lambda c: c.name != "pandera_contract" and not c.name.startswith("dbt__"),
                    ),
                ]

                by_category: list[CategoryStats] = []
                for cat_name, predicate in categories:
                    relevant = [c for c in latest_checks if predicate(c)]
                    if not relevant:
                        continue
                    passing = len([c for c in relevant if c.status == "PASSED"])
                    total = len(relevant)
                    by_category.append(
                        CategoryStats(
                            category=cat_name,
                            passing=passing,
                            total=total,
                            percentage=round((passing / total) * 100) if total > 0 else 0,
                        )
                    )

                return {
                    "total_checks": total_checks,
                    "passing_checks": passing_checks,
                    "failing_checks": failing_checks,
                    "warning_checks": warning_checks,
                    "quality_score": quality_score,
                    "by_category": by_category,
                    "recent_executions": recent_executions[:recent_limit],
                    "failing_checks_list": failing_checks_list,
                    "latest_checks": latest_checks,
                }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str&#x22;" value="undefined">
          Dagster GraphQL endpoint URL.
        </PyParameter>

        <PyParameter name="&#x22;recent_limit&#x22;" type="&#x22;int&#x22;" value="&#x22;50&#x22;">
          Maximum recent executions to return.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict[str, Any] | None&#x22;">
        Aggregated quality snapshot, or `None` when fetch fails.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_quality_overview&#x22;" type="&#x22;(dagster_url=None) -> QualityOverview | dict[str, str]&#x22;">
      Get an overview of quality metrics from Dagster.

      Aggregates asset check results into quality score, category breakdowns,
      and recent execution history.

      <PySourceCode>
        ```python
        @router.get("/overview", response_model=QualityOverview | dict)
        async def get_quality_overview(
            dagster_url: str | None = None,
        ) -> QualityOverview | dict[str, str]:
            """Get an overview of quality metrics from Dagster.

            Aggregates asset check results into quality score, category breakdowns,
            and recent execution history.

            Args:
                dagster_url: Optional Dagster GraphQL endpoint override.

            Returns:
                QualityOverview with aggregated metrics, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_dagster_url(dagster_url)

            try:
                snapshot = await fetch_quality_snapshot(url)
                if not snapshot:
                    return {"error": "Failed to fetch quality snapshot from Dagster"}

                return QualityOverview(
                    total_checks=snapshot["total_checks"],
                    passing_checks=snapshot["passing_checks"],
                    failing_checks=snapshot["failing_checks"],
                    warning_checks=snapshot["warning_checks"],
                    quality_score=snapshot["quality_score"],
                    by_category=snapshot["by_category"],
                    recent_executions=snapshot["recent_executions"],
                    failing_checks_list=snapshot["failing_checks_list"],
                )
            except Exception as e:
                logger.exception("Failed to get quality overview")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL endpoint override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;QualityOverview | dict[str, str]&#x22;">
        QualityOverview with aggregated metrics, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_asset_checks&#x22;" type="&#x22;(asset_key_path, dagster_url=None) -> list[QualityCheck] | dict[str, str]&#x22;">
      Get latest checks for a specific asset.

      Fetches and deduplicates check execution results for the specified asset.

      <PySourceCode>
        ```python
        @router.get("/assets/{asset_key_path:path}/checks", response_model=list[QualityCheck] | dict)
        async def get_asset_checks(
            asset_key_path: str,
            dagster_url: str | None = None,
        ) -> list[QualityCheck] | dict[str, str]:
            """Get latest checks for a specific asset.

            Fetches and deduplicates check execution results for the specified asset.

            Args:
                asset_key_path: Slash-delimited Dagster asset key path.
                dagster_url: Optional Dagster GraphQL endpoint override.

            Returns:
                List of QualityCheck objects for the asset, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            asset_key = asset_key_path.split("/")
            url = resolve_dagster_url(dagster_url)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        url,
                        json={
                            "query": ASSET_CHECK_EXECUTIONS_QUERY,
                            "variables": {"assetKey": {"path": asset_key}, "limit": 200},
                        },
                    )
                    response.raise_for_status()
                    result = response.json()

                    if result.get("errors"):
                        return {"error": result["errors"][0].get("message", "GraphQL error")}

                    executions = result.get("data", {}).get("assetCheckExecutions", [])

                    # Group by check name and get newest
                    newest_by_check: dict[str, dict[str, Any]] = {}
                    for exec in executions:
                        check_name = exec.get("checkName")
                        if not check_name:
                            continue
                        existing = newest_by_check.get(check_name)
                        if not existing or to_epoch_ms(exec["timestamp"]) > to_epoch_ms(
                            existing["timestamp"]
                        ):
                            newest_by_check[check_name] = exec

                    checks = []
                    for check_name, exec in sorted(newest_by_check.items()):
                        status = normalize_status(exec.get("status", ""))
                        evaluation = exec.get("evaluation") or {}
                        checks.append(
                            QualityCheck(
                                name=check_name,
                                asset_key=asset_key,
                                severity=normalize_severity(evaluation.get("severity")),
                                status=status,
                                last_execution_time=to_iso_timestamp(exec["timestamp"]),
                                last_result=CheckResult(
                                    passed=status == "PASSED",
                                    metadata=metadata_entries_to_dict(evaluation.get("metadataEntries")),
                                ),
                            )
                        )
                    return checks
            except Exception as e:
                logger.exception("Failed to get asset checks")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_key_path&#x22;" type="&#x22;str&#x22;" value="undefined">
          Slash-delimited Dagster asset key path.
        </PyParameter>

        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL endpoint override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[QualityCheck] | dict[str, str]&#x22;">
        List of QualityCheck objects for the asset, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_check_history&#x22;" type="&#x22;(asset_key_path, check_name, limit=Query(default=20, le=100), dagster_url=None) -> list[CheckExecution] | dict[str, str]&#x22;">
      Get execution history for an asset check.

      Returns historical check execution results filtered by check name.

      <PySourceCode>
        ```python
        @router.get(
            "/assets/{asset_key_path:path}/checks/{check_name}/history",
            response_model=list[CheckExecution] | dict,
        )
        async def get_check_history(
            asset_key_path: str,
            check_name: str,
            limit: int = Query(default=20, le=100),
            dagster_url: str | None = None,
        ) -> list[CheckExecution] | dict[str, str]:
            """Get execution history for an asset check.

            Returns historical check execution results filtered by check name.

            Args:
                asset_key_path: Slash-delimited Dagster asset key path.
                check_name: Check name to filter history by.
                limit: Maximum number of executions to return (default: 20, max: 100).
                dagster_url: Optional Dagster GraphQL endpoint override.

            Returns:
                List of CheckExecution objects, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            asset_key = asset_key_path.split("/")
            url = resolve_dagster_url(dagster_url)

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        url,
                        json={
                            "query": ASSET_CHECK_EXECUTIONS_QUERY,
                            "variables": {"assetKey": {"path": asset_key}, "limit": max(50, limit * 3)},
                        },
                    )
                    response.raise_for_status()
                    result = response.json()

                    if result.get("errors"):
                        return {"error": result["errors"][0].get("message", "GraphQL error")}

                    all_executions = result.get("data", {}).get("assetCheckExecutions", [])

                    # Filter by check name
                    executions = [e for e in all_executions if e.get("checkName") == check_name]

                    # Sort by timestamp descending
                    executions.sort(key=lambda e: to_epoch_ms(e["timestamp"]), reverse=True)

                    return [
                        CheckExecution(
                            timestamp=to_iso_timestamp(e["timestamp"]),
                            passed=normalize_status(e.get("status", "")) == "PASSED",
                            run_id=e.get("runId"),
                            metadata=metadata_entries_to_dict(
                                (e.get("evaluation") or {}).get("metadataEntries")
                            ),
                        )
                        for e in executions[:limit]
                    ]
            except Exception as e:
                logger.exception("Failed to get check history")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_key_path&#x22;" type="&#x22;str&#x22;" value="undefined">
          Slash-delimited Dagster asset key path.
        </PyParameter>

        <PyParameter name="&#x22;check_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Check name to filter history by.
        </PyParameter>

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=20, le=100)&#x22;">
          Maximum number of executions to return (default: 20, max: 100).
        </PyParameter>

        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL endpoint override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[CheckExecution] | dict[str, str]&#x22;">
        List of CheckExecution objects, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_failing_checks&#x22;" type="&#x22;(dagster_url=None) -> list[QualityCheck] | dict[str, str]&#x22;">
      Get all currently failing checks.

      Returns a list of checks with FAILED status from the latest execution snapshot.

      <PySourceCode>
        ```python
        @router.get("/failing", response_model=list[QualityCheck] | dict)
        async def get_failing_checks(
            dagster_url: str | None = None,
        ) -> list[QualityCheck] | dict[str, str]:
            """Get all currently failing checks.

            Returns a list of checks with FAILED status from the latest execution snapshot.

            Args:
                dagster_url: Optional Dagster GraphQL endpoint override.

            Returns:
                List of failing QualityCheck objects, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_dagster_url(dagster_url)

            try:
                snapshot = await fetch_quality_snapshot(url)
                if not snapshot:
                    return {"error": "Failed to fetch quality snapshot from Dagster"}

                return snapshot["failing_checks_list"]
            except Exception as e:
                logger.exception("Failed to get failing checks")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL endpoint override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[QualityCheck] | dict[str, str]&#x22;">
        List of failing QualityCheck objects, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
