# dagster (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster)



Dagster API Router.

Endpoints for interacting with the Dagster GraphQL API.
Provides health metrics, asset listing, and materialization history.

This module acts as a proxy to the Dagster GraphQL API, translating
requests/responses into Observatory-compatible formats and providing
higher-level operations like asset graph construction and impact analysis.

Key Endpoints:
GET /connection: Check Dagster connectivity.
GET /health: Get platform health metrics.
GET /assets: List all assets.
GET /assets/\{key}: Get asset details.
GET /assets/\{key}/history: Get materialization history.
GET /graph: Get full asset dependency graph.
GET /graph/neighbors: Get subgraph around an asset.
GET /graph/impact: Get downstream impact analysis.

Environment Variables:
DAGSTER\_GRAPHQL\_URL: URL for Dagster GraphQL endpoint.

Example:
Fetching the asset graph:

.. code-block:: bash

curl [http://localhost:4000/api/dagster/graph](http://localhost:4000/api/dagster/graph)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['dagster'])&#x22;" />

<PyAttribute name="&#x22;DEFAULT_DAGSTER_URL&#x22;" type="null" value="&#x22;'http://dagster:3000/graphql'&#x22;" />

<PyAttribute name="&#x22;VERSION_QUERY&#x22;" type="null" value="&#x22;'\\nquery Version {\\n    version\\n}\\n'&#x22;" />

<PyAttribute name="&#x22;HEALTH_QUERY&#x22;" type="null" value="&#x22;'\\nquery HealthMetrics {\\n    assetsOrError {\\n        ... on AssetConnection {\\n            nodes {\\n                key { path }\\n                assetMaterializations(limit: 1) {\\n                    timestamp\\n                }\\n            }\\n        }\\n        ... on PythonError { message }\\n    }\\n    runsOrError(filter: { statuses: [FAILURE] }, limit: 100) {\\n        ... on Runs {\\n            results {\\n                id\\n                status\\n                startTime\\n                endTime\\n            }\\n        }\\n        ... on PythonError { message }\\n    }\\n}\\n'&#x22;" />

<PyAttribute name="&#x22;ASSETS_QUERY&#x22;" type="null" value="&#x22;'\\nquery AssetsQuery {\\n    assetsOrError {\\n        __typename\\n        ... on AssetConnection {\\n            nodes {\\n                id\\n                key { path }\\n                definition {\\n                    description\\n                    computeKind\\n                    groupName\\n                    hasMaterializePermission\\n                    opNames\\n                }\\n                assetMaterializations(limit: 1) {\\n                    timestamp\\n                    runId\\n                }\\n            }\\n        }\\n        ... on PythonError { message }\\n    }\\n}\\n'&#x22;" />

<PyAttribute name="&#x22;ASSET_GRAPH_QUERY&#x22;" type="null" value="&#x22;'\\nquery AssetGraphQuery {\\n    assetsOrError {\\n        __typename\\n        ... on AssetConnection {\\n            nodes {\\n                id\\n                key { path }\\n                definition {\\n                    description\\n                    computeKind\\n                    groupName\\n                    dependencyKeys { path }\\n                    dependedByKeys { path }\\n                }\\n                assetMaterializations(limit: 1) {\\n                    timestamp\\n                }\\n            }\\n        }\\n        ... on PythonError { message }\\n    }\\n}\\n'&#x22;" />

<PyAttribute name="&#x22;ASSET_DETAILS_QUERY&#x22;" type="null" value="&#x22;'\\nquery AssetDetailsQuery($assetKey: AssetKeyInput!) {\\n    assetOrError(assetKey: $assetKey) {\\n        ... on Asset {\\n            id\\n            key { path }\\n            definition {\\n                description\\n                computeKind\\n                groupName\\n                hasMaterializePermission\\n                opNames\\n                metadataEntries {\\n                    label\\n                    description\\n                    ... on TextMetadataEntry { text }\\n                    ... on TableSchemaMetadataEntry {\\n                        schema {\\n                            columns { name type description }\\n                        }\\n                    }\\n                    ... on TableColumnLineageMetadataEntry {\\n                        lineage {\\n                            columnName\\n                            columnDeps {\\n                                assetKey { path }\\n                                columnName\\n                            }\\n                        }\\n                    }\\n                }\\n                partitionDefinition { description }\\n            }\\n            assetMaterializations(limit: 1) {\\n                timestamp\\n                runId\\n                metadataEntries {\\n                    label\\n                    __typename\\n                    ... on TableSchemaMetadataEntry {\\n                        schema {\\n                            columns { name type description }\\n                        }\\n                    }\\n                    ... on TableColumnLineageMetadataEntry {\\n                        lineage {\\n                            columnName\\n                            columnDeps {\\n                                assetKey { path }\\n                                columnName\\n                            }\\n                        }\\n                    }\\n                }\\n            }\\n        }\\n        ... on AssetNotFoundError { message }\\n    }\\n}\\n'&#x22;" />

<PyAttribute name="&#x22;MATERIALIZATION_HISTORY_QUERY&#x22;" type="null" value="&#x22;'\\nquery MaterializationHistory($assetKey: AssetKeyInput!, $limit: Int!) {\\n    assetOrError(assetKey: $assetKey) {\\n        ... on Asset {\\n            assetMaterializations(limit: $limit) {\\n                timestamp\\n                runId\\n                stepKey\\n                metadataEntries {\\n                    label\\n                    ... on TextMetadataEntry { text }\\n                    ... on IntMetadataEntry { intValue }\\n                    ... on FloatMetadataEntry { floatValue }\\n                }\\n            }\\n        }\\n        ... on AssetNotFoundError { message }\\n    }\\n}\\n'&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DagsterConnectionStatus&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/DagsterConnectionStatus&#x22;" />

      <Card title="&#x22;HealthMetrics&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/HealthMetrics&#x22;" />

      <Card title="&#x22;LastMaterialization&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/LastMaterialization&#x22;" />

      <Card title="&#x22;Asset&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/Asset&#x22;" />

      <Card title="&#x22;ColumnSchema&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/ColumnSchema&#x22;" />

      <Card title="&#x22;ColumnLineageDep&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/ColumnLineageDep&#x22;" />

      <Card title="&#x22;AssetDetails&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/AssetDetails&#x22;" />

      <Card title="&#x22;MaterializationEvent&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/MaterializationEvent&#x22;" />

      <Card title="&#x22;GraphNode&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/GraphNode&#x22;" />

      <Card title="&#x22;GraphEdge&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/GraphEdge&#x22;" />

      <Card title="&#x22;AssetGraphPayload&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/AssetGraphPayload&#x22;" />

      <Card title="&#x22;ImpactedAsset&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster/ImpactedAsset&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_dagster_url&#x22;" type="&#x22;(override=None) -> str&#x22;">
      Resolve the Dagster GraphQL URL from override, environment, or default.

      <PySourceCode>
        ```python
        def resolve_dagster_url(override: str | None = None) -> str:
            """Resolve the Dagster GraphQL URL from override, environment, or default.

            Args:
                override: Optional explicit Dagster GraphQL URL override.

            Returns:
                Resolved Dagster GraphQL URL string.

            Raises:
                None: No exceptions raised directly.

            """
            env_url = os.environ.get("DAGSTER_GRAPHQL_URL")
            if override and override.strip():
                if env_url and override.strip() == "http://localhost:3000/graphql":
                    return env_url
                return override
            return env_url or DEFAULT_DAGSTER_URL
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;override&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional explicit Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Resolved Dagster GraphQL URL string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;graphql_request&#x22;" type="&#x22;(url, query, variables=None, timeout=10.0) -> dict[str, Any]&#x22;">
      Execute a GraphQL request against the Dagster API.

      <PySourceCode>
        ```python
        async def graphql_request(
            url: str, query: str, variables: dict[str, Any] | None = None, timeout: float = 10.0
        ) -> dict[str, Any]:
            """Execute a GraphQL request against the Dagster API.

            Args:
                url: Dagster GraphQL endpoint URL.
                query: GraphQL query string.
                variables: Optional GraphQL variables dictionary.
                timeout: Request timeout in seconds (default: 10.0).

            Returns:
                GraphQL response data as a dictionary.

            Raises:
                httpx.HTTPStatusError: If the HTTP request fails.

            """
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json={"query": query, "variables": variables or {}},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="undefined">
          Dagster GraphQL endpoint URL.
        </PyParameter>

        <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
          GraphQL query string.
        </PyParameter>

        <PyParameter name="&#x22;variables&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
          Optional GraphQL variables dictionary.
        </PyParameter>

        <PyParameter name="&#x22;timeout&#x22;" type="&#x22;float&#x22;" value="&#x22;10.0&#x22;">
          Request timeout in seconds (default: 10.0).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        GraphQL response data as a dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;infer_layer&#x22;" type="&#x22;(key_path) -> str&#x22;">
      Infer logical data layer from asset key path.

      <PySourceCode>
        ```python
        def infer_layer(key_path: str) -> str:
            """Infer logical data layer from asset key path.

            Args:
                key_path: Asset key path string (e.g., "bronze/raw_events").

            Returns:
                Inferred layer name: "source", "bronze", "silver", "gold", "marts", "publish", or "unknown".

            Raises:
                None: No exceptions raised directly.

            """
            path = key_path.lower()
            if "publish" in path or path.startswith("publish_"):
                return "publish"
            if "mart" in path or path.startswith("mrt_"):
                return "marts"
            if "gold" in path or path.startswith("dim_") or path.startswith("fct_"):
                return "gold"
            if "silver" in path or "stg_" in path:
                return "silver"
            if "bronze" in path or "raw" in path:
                return "bronze"
            if path.startswith("dlt_") or "ingest" in path:
                return "bronze"
            if path.startswith("src_") or "source" in path:
                return "source"
            return "unknown"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;key_path&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset key path string (e.g., "bronze/raw\_events").
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Inferred layer name: "source", "bronze", "silver", "gold", "marts", "publish", or "unknown".
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;build_asset_graph_payload&#x22;" type="&#x22;(asset_nodes) -> AssetGraphPayload&#x22;">
      Build the normalized Observatory graph payload from Dagster nodes.

      <PySourceCode>
        ```python
        def build_asset_graph_payload(asset_nodes: list[dict[str, Any]]) -> AssetGraphPayload:
            """Build the normalized Observatory graph payload from Dagster nodes.

            Args:
                asset_nodes: List of Dagster asset node dictionaries from GraphQL.

            Returns:
                AssetGraphPayload containing nodes and edges for the asset graph.

            Raises:
                None: No exceptions raised directly.

            """
            nodes: list[GraphNode] = []
            edges: list[GraphEdge] = []
            known_nodes: set[str] = set()

            for asset in asset_nodes:
                key = asset["key"]["path"]
                key_path = "/".join(key)
                definition = asset.get("definition") or {}
                known_nodes.add(key_path)
                nodes.append(
                    GraphNode(
                        id=asset["id"],
                        key=key,
                        key_path=key_path,
                        label=key[-1] if key else key_path,
                        description=definition.get("description"),
                        compute_kind=definition.get("computeKind"),
                        group_name=definition.get("groupName"),
                        layer=infer_layer(key_path),
                        last_materialization=((asset.get("assetMaterializations") or [None])[0] or {}).get(
                            "timestamp"
                        ),
                        upstream_count=len(definition.get("dependencyKeys") or []),
                        downstream_count=len(definition.get("dependedByKeys") or []),
                    )
                )

            for asset in asset_nodes:
                target_key_path = "/".join(asset["key"]["path"])
                dependencies = (asset.get("definition") or {}).get("dependencyKeys") or []
                for dependency in dependencies:
                    source_key_path = "/".join(dependency["path"])
                    if source_key_path in known_nodes and target_key_path in known_nodes:
                        edges.append(GraphEdge(source=source_key_path, target=target_key_path))

            return AssetGraphPayload(nodes=nodes, edges=edges)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_nodes&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
          List of Dagster asset node dictionaries from GraphQL.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.dagster.AssetGraphPayload&#x22;">
        AssetGraphPayload containing nodes and edges for the asset graph.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;filter_asset_neighbors&#x22;" type="&#x22;(graph, asset_key, direction, depth) -> AssetGraphPayload&#x22;">
      Return a focused subgraph around an asset using BFS traversal.

      <PySourceCode>
        ```python
        def filter_asset_neighbors(
            graph: AssetGraphPayload,
            asset_key: str,
            direction: str,
            depth: int,
        ) -> AssetGraphPayload:
            """Return a focused subgraph around an asset using BFS traversal.

            Args:
                graph: Full asset graph payload containing nodes and edges.
                asset_key: Key of the focal asset to center the subgraph around.
                direction: Direction to traverse: "upstream", "downstream", or "both".
                depth: Maximum depth to traverse from the focal asset.

            Returns:
                AssetGraphPayload containing the filtered subgraph.

            Raises:
                None: No exceptions raised directly.

            """
            upstream: dict[str, list[str]] = {}
            downstream: dict[str, list[str]] = {}

            for edge in graph.edges:
                upstream.setdefault(edge.target, []).append(edge.source)
                downstream.setdefault(edge.source, []).append(edge.target)

            included_nodes = {asset_key}

            def bfs(start_key: str, adjacency: dict[str, list[str]], max_depth: int) -> None:
                """Breadth-first search to find neighbors within a given depth.

                Args:
                    start_key: The starting node key for the search.
                    adjacency: Adjacency list mapping nodes to their neighbors.
                    max_depth: Maximum depth to traverse from the start node.

                Returns:
                    None: Modifies the `included_nodes` set in the enclosing scope.

                Raises:
                    None: No exceptions raised directly.

                """
                queue: list[tuple[str, int]] = [(start_key, 0)]
                visited = {start_key}

                while queue:
                    current, current_depth = queue.pop(0)
                    if current_depth >= max_depth:
                        continue

                    for neighbor in adjacency.get(current, []):
                        if neighbor in visited:
                            continue
                        visited.add(neighbor)
                        included_nodes.add(neighbor)
                        queue.append((neighbor, current_depth + 1))

            if direction in {"upstream", "both"}:
                bfs(asset_key, upstream, depth)
            if direction in {"downstream", "both"}:
                bfs(asset_key, downstream, depth)

            return AssetGraphPayload(
                nodes=[node for node in graph.nodes if node.key_path in included_nodes],
                edges=[
                    edge
                    for edge in graph.edges
                    if edge.source in included_nodes and edge.target in included_nodes
                ],
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;graph&#x22;" type="&#x22;AssetGraphPayload&#x22;" value="undefined">
          Full asset graph payload containing nodes and edges.
        </PyParameter>

        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Key of the focal asset to center the subgraph around.
        </PyParameter>

        <PyParameter name="&#x22;direction&#x22;" type="&#x22;str&#x22;" value="undefined">
          Direction to traverse: "upstream", "downstream", or "both".
        </PyParameter>

        <PyParameter name="&#x22;depth&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum depth to traverse from the focal asset.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.dagster.AssetGraphPayload&#x22;">
        AssetGraphPayload containing the filtered subgraph.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;compute_asset_impact&#x22;" type="&#x22;(graph, asset_key, max_depth) -> list[ImpactedAsset]&#x22;">
      Compute all downstream assets impacted by a given asset.

      <PySourceCode>
        ```python
        def compute_asset_impact(
            graph: AssetGraphPayload, asset_key: str, max_depth: int
        ) -> list[ImpactedAsset]:
            """Compute all downstream assets impacted by a given asset.

            Args:
                graph: Full asset graph payload containing nodes and edges.
                asset_key: Key of the source asset to analyze impact from.
                max_depth: Maximum depth to traverse downstream.

            Returns:
                List of ImpactedAsset objects sorted by depth and label.

            Raises:
                None: No exceptions raised directly.

            """
            node_map = {node.key_path: node for node in graph.nodes}
            downstream: dict[str, list[str]] = {}
            for edge in graph.edges:
                downstream.setdefault(edge.source, []).append(edge.target)

            impacted: list[ImpactedAsset] = []
            visited = {asset_key}
            queue: list[tuple[str, int]] = [(asset_key, 0)]

            while queue:
                current, current_depth = queue.pop(0)
                if current_depth > max_depth:
                    continue

                for child in downstream.get(current, []):
                    if child in visited:
                        continue
                    visited.add(child)
                    node = node_map.get(child)
                    if node is not None:
                        impacted.append(
                            ImpactedAsset(
                                key_path=node.key_path,
                                label=node.label,
                                layer=node.layer,
                                depth=current_depth + 1,
                            )
                        )
                    queue.append((child, current_depth + 1))

            return sorted(impacted, key=lambda item: (item.depth, item.label))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;graph&#x22;" type="&#x22;AssetGraphPayload&#x22;" value="undefined">
          Full asset graph payload containing nodes and edges.
        </PyParameter>

        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Key of the source asset to analyze impact from.
        </PyParameter>

        <PyParameter name="&#x22;max_depth&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum depth to traverse downstream.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of ImpactedAsset objects sorted by depth and label.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;check_connection&#x22;" type="&#x22;(dagster_url=None) -> DagsterConnectionStatus&#x22;">
      Check if Dagster GraphQL endpoint is reachable.

      <PySourceCode>
        ```python
        @router.get("/connection", response_model=DagsterConnectionStatus)
        async def check_connection(dagster_url: str | None = None) -> DagsterConnectionStatus:
            """Check if Dagster GraphQL endpoint is reachable.

            Args:
                dagster_url: Optional Dagster GraphQL URL override.

            Returns:
                DagsterConnectionStatus with connection state and version.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_dagster_url(dagster_url)

            try:
                result = await graphql_request(url, VERSION_QUERY, timeout=5.0)

                if result.get("errors"):
                    return DagsterConnectionStatus(
                        connected=False, error=result["errors"][0].get("message", "GraphQL error")
                    )

                return DagsterConnectionStatus(
                    connected=True, version=result.get("data", {}).get("version")
                )
            except Exception as e:
                return DagsterConnectionStatus(connected=False, error=str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.dagster.DagsterConnectionStatus&#x22;">
        DagsterConnectionStatus with connection state and version.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_health_metrics&#x22;" type="&#x22;(dagster_url=None) -> HealthMetrics | dict[str, str]&#x22;">
      Get aggregated platform health metrics from Dagster.

      <PySourceCode>
        ```python
        @router.get("/health", response_model=HealthMetrics | dict)
        async def get_health_metrics(
            dagster_url: str | None = None,
        ) -> HealthMetrics | dict[str, str]:
            """Get aggregated platform health metrics from Dagster.

            Args:
                dagster_url: Optional Dagster GraphQL URL override.

            Returns:
                HealthMetrics object or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_dagster_url(dagster_url)

            try:
                result = await graphql_request(url, HEALTH_QUERY)

                if result.get("errors"):
                    return {"error": result["errors"][0].get("message", "GraphQL error")}

                data = result.get("data", {})
                assets_or_error = data.get("assetsOrError", {})
                runs_or_error = data.get("runsOrError", {})

                # Handle asset data
                assets_total = 0
                stale_assets = 0
                now = time.time() * 1000
                stale_threshold = 24 * 60 * 60 * 1000  # 24 hours

                if assets_or_error.get("nodes"):
                    nodes = assets_or_error["nodes"]
                    assets_total = len(nodes)

                    for asset in nodes:
                        last_mat = (asset.get("assetMaterializations") or [None])[0]
                        if last_mat:
                            mat_time = float(last_mat.get("timestamp", 0)) * 1000
                            if now - mat_time > stale_threshold:
                                stale_assets += 1
                        else:
                            stale_assets += 1

                # Handle run data
                failed_jobs_24h = 0
                one_day_ago = now - stale_threshold

                if runs_or_error.get("results"):
                    for run in runs_or_error["results"]:
                        start_time = float(run.get("startTime") or 0) * 1000
                        if start_time > one_day_ago:
                            failed_jobs_24h += 1

                quality_checks_passing = 0
                quality_checks_total = 0
                quality_snapshot = await fetch_quality_snapshot(url)
                if quality_snapshot:
                    quality_checks_passing = quality_snapshot["passing_checks"]
                    quality_checks_total = quality_snapshot["total_checks"]

                return HealthMetrics(
                    assets_total=assets_total,
                    assets_healthy=assets_total - stale_assets,
                    failed_jobs_24h=failed_jobs_24h,
                    quality_checks_passing=quality_checks_passing,
                    quality_checks_total=quality_checks_total,
                    stale_assets=stale_assets,
                    last_updated=datetime.now().isoformat(),
                )
            except Exception as e:
                logger.exception("Failed to get health metrics")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;HealthMetrics | dict[str, str]&#x22;">
        HealthMetrics object or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_assets&#x22;" type="&#x22;(dagster_url=None) -> list[Asset] | dict[str, str]&#x22;">
      Get all assets from Dagster.

      <PySourceCode>
        ```python
        @router.get("/assets", response_model=list[Asset] | dict)
        async def get_assets(dagster_url: str | None = None) -> list[Asset] | dict[str, str]:
            """Get all assets from Dagster.

            Args:
                dagster_url: Optional Dagster GraphQL URL override.

            Returns:
                List of Asset objects or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_dagster_url(dagster_url)

            try:
                result = await graphql_request(url, ASSETS_QUERY)

                if result.get("errors"):
                    return {"error": result["errors"][0].get("message", "GraphQL error")}

                data = result.get("data", {})
                assets_or_error = data.get("assetsOrError", {})

                if assets_or_error.get("message"):  # PythonError
                    return {"error": assets_or_error["message"]}

                assets = []
                for node in assets_or_error.get("nodes", []):
                    definition = node.get("definition") or {}
                    mats = node.get("assetMaterializations") or []

                    last_mat = None
                    if mats:
                        last_mat = LastMaterialization(
                            timestamp=mats[0]["timestamp"], run_id=mats[0]["runId"]
                        )

                    assets.append(
                        Asset(
                            id=node["id"],
                            key=node["key"]["path"],
                            key_path="/".join(node["key"]["path"]),
                            description=definition.get("description"),
                            compute_kind=definition.get("computeKind"),
                            group_name=definition.get("groupName"),
                            has_materialize_permission=definition.get("hasMaterializePermission", False),
                            last_materialization=last_mat,
                        )
                    )

                return assets
            except Exception as e:
                logger.exception("Failed to get assets")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[Asset] | dict[str, str]&#x22;">
        List of Asset objects or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_asset_details&#x22;" type="&#x22;(asset_key_path, dagster_url=None) -> AssetDetails | dict[str, str]&#x22;">
      Get detailed information about a single asset.

      <PySourceCode>
        ```python
        @router.get("/assets/{asset_key_path:path}", response_model=AssetDetails | dict)
        async def get_asset_details(
            asset_key_path: str, dagster_url: str | None = None
        ) -> AssetDetails | dict[str, str]:
            """Get detailed information about a single asset.

            Args:
                asset_key_path: Slash-delimited asset key path.
                dagster_url: Optional Dagster GraphQL URL override.

            Returns:
                AssetDetails object or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            if not asset_key_path:
                return {"error": "Asset key is required"}

            url = resolve_dagster_url(dagster_url)
            asset_key = asset_key_path.split("/")

            try:
                result = await graphql_request(url, ASSET_DETAILS_QUERY, {"assetKey": {"path": asset_key}})

                if result.get("errors"):
                    return {"error": result["errors"][0].get("message", "GraphQL error")}

                asset_or_error = result.get("data", {}).get("assetOrError", {})

                if asset_or_error.get("message"):  # AssetNotFoundError
                    return {"error": asset_or_error["message"]}

                definition = asset_or_error.get("definition") or {}
                mats = asset_or_error.get("assetMaterializations") or []

                # Extract columns from metadata
                columns = None
                column_lineage = None

                # Check materialization metadata first, then definition
                for source in [mats[0] if mats else None, definition]:
                    if not source:
                        continue
                    for entry in source.get("metadataEntries", []):
                        if entry.get("schema") and not columns:
                            columns = [
                                ColumnSchema(
                                    name=c["name"],
                                    type=c["type"],
                                    description=c.get("description"),
                                )
                                for c in entry["schema"].get("columns", [])
                            ]
                        if entry.get("lineage") and not column_lineage:
                            column_lineage = {}
                            for lin in entry["lineage"]:
                                column_lineage[lin["columnName"]] = [
                                    ColumnLineageDep(
                                        asset_key=dep["assetKey"]["path"],
                                        column_name=dep["columnName"],
                                    )
                                    for dep in lin.get("columnDeps", [])
                                ]

                last_mat = None
                if mats:
                    last_mat = LastMaterialization(timestamp=mats[0]["timestamp"], run_id=mats[0]["runId"])

                return AssetDetails(
                    id=asset_or_error["id"],
                    key=asset_or_error["key"]["path"],
                    key_path="/".join(asset_or_error["key"]["path"]),
                    description=definition.get("description"),
                    compute_kind=definition.get("computeKind"),
                    group_name=definition.get("groupName"),
                    has_materialize_permission=definition.get("hasMaterializePermission", False),
                    op_names=definition.get("opNames", []),
                    metadata=[
                        {"key": e["label"], "value": e.get("text") or e.get("description") or ""}
                        for e in definition.get("metadataEntries", [])
                        if not e.get("schema")
                    ],
                    columns=columns,
                    column_lineage=column_lineage,
                    partition_definition=(
                        {"description": definition["partitionDefinition"]["description"]}
                        if definition.get("partitionDefinition")
                        else None
                    ),
                    last_materialization=last_mat,
                )
            except Exception as e:
                logger.exception("Failed to get asset details")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_key_path&#x22;" type="&#x22;str&#x22;" value="undefined">
          Slash-delimited asset key path.
        </PyParameter>

        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;AssetDetails | dict[str, str]&#x22;">
        AssetDetails object or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_materialization_history&#x22;" type="&#x22;(asset_key_path, limit=Query(default=20, le=100), dagster_url=None) -> list[MaterializationEvent] | dict[str, str]&#x22;">
      Get materialization history for an asset.

      <PySourceCode>
        ```python
        @router.get(
            "/assets/{asset_key_path:path}/history", response_model=list[MaterializationEvent] | dict
        )
        async def get_materialization_history(
            asset_key_path: str,
            limit: int = Query(default=20, le=100),
            dagster_url: str | None = None,
        ) -> list[MaterializationEvent] | dict[str, str]:
            """Get materialization history for an asset.

            Args:
                asset_key_path: Slash-delimited asset key path.
                limit: Maximum number of materialization events to return.
                dagster_url: Optional Dagster GraphQL URL override.

            Returns:
                List of MaterializationEvent objects or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_dagster_url(dagster_url)
            asset_key = asset_key_path.split("/")

            try:
                result = await graphql_request(
                    url,
                    MATERIALIZATION_HISTORY_QUERY,
                    {"assetKey": {"path": asset_key}, "limit": limit},
                )

                if result.get("errors"):
                    return {"error": result["errors"][0].get("message", "GraphQL error")}

                asset_or_error = result.get("data", {}).get("assetOrError", {})

                if asset_or_error.get("message"):
                    return {"error": asset_or_error["message"]}

                events = []
                for mat in asset_or_error.get("assetMaterializations", []):
                    events.append(
                        MaterializationEvent(
                            timestamp=mat["timestamp"],
                            run_id=mat["runId"],
                            status="SUCCESS",
                            step_key=mat.get("stepKey"),
                            metadata=[
                                {
                                    "key": e["label"],
                                    "value": e.get("text")
                                    or str(e.get("intValue", ""))
                                    or str(e.get("floatValue", ""))
                                    or "",
                                }
                                for e in mat.get("metadataEntries", [])
                            ],
                        )
                    )

                return events
            except Exception as e:
                logger.exception("Failed to get materialization history")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_key_path&#x22;" type="&#x22;str&#x22;" value="undefined">
          Slash-delimited asset key path.
        </PyParameter>

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=20, le=100)&#x22;">
          Maximum number of materialization events to return.
        </PyParameter>

        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[MaterializationEvent] | dict[str, str]&#x22;">
        List of MaterializationEvent objects or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_asset_graph&#x22;" type="&#x22;(dagster_url=None) -> AssetGraphPayload | dict[str, str]&#x22;">
      Get the full asset dependency graph from Dagster.

      <PySourceCode>
        ```python
        @router.get("/graph", response_model=AssetGraphPayload | dict)
        async def get_asset_graph(
            dagster_url: str | None = None,
        ) -> AssetGraphPayload | dict[str, str]:
            """Get the full asset dependency graph from Dagster.

            Args:
                dagster_url: Optional Dagster GraphQL URL override.

            Returns:
                AssetGraphPayload containing nodes and edges, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            url = resolve_dagster_url(dagster_url)

            try:
                result = await graphql_request(url, ASSET_GRAPH_QUERY, timeout=15.0)
                if result.get("errors"):
                    return {"error": result["errors"][0].get("message", "GraphQL error")}

                assets_or_error = result.get("data", {}).get("assetsOrError", {})
                if assets_or_error.get("__typename") == "PythonError" or assets_or_error.get("message"):
                    return {"error": assets_or_error.get("message", "Dagster error")}

                return build_asset_graph_payload(assets_or_error.get("nodes", []))
            except Exception as e:
                logger.exception("Failed to get asset graph")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;AssetGraphPayload | dict[str, str]&#x22;">
        AssetGraphPayload containing nodes and edges, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_asset_neighbors&#x22;" type="&#x22;(asset_key, direction=Query(default='both', pattern='^(upstream|downstream|both)$'), depth=Query(default=2, ge=1, le=10), dagster_url=None) -> AssetGraphPayload | dict[str, str]&#x22;">
      Get a focused graph around a single asset.

      <PySourceCode>
        ```python
        @router.get("/graph/neighbors", response_model=AssetGraphPayload | dict)
        async def get_asset_neighbors(
            asset_key: str,
            direction: str = Query(default="both", pattern="^(upstream|downstream|both)$"),
            depth: int = Query(default=2, ge=1, le=10),
            dagster_url: str | None = None,
        ) -> AssetGraphPayload | dict[str, str]:
            """Get a focused graph around a single asset.

            Args:
                asset_key: Key of the focal asset.
                direction: Direction to traverse: "upstream", "downstream", or "both".
                depth: Maximum depth to traverse (1-10).
                dagster_url: Optional Dagster GraphQL URL override.

            Returns:
                AssetGraphPayload containing the filtered subgraph, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            graph = await get_asset_graph(dagster_url=dagster_url)
            if isinstance(graph, dict):
                return graph
            return filter_asset_neighbors(graph, asset_key=asset_key, direction=direction, depth=depth)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Key of the focal asset.
        </PyParameter>

        <PyParameter name="&#x22;direction&#x22;" type="&#x22;str&#x22;" value="&#x22;Query(default='both', pattern='^(upstream|downstream|both)$')&#x22;">
          Direction to traverse: "upstream", "downstream", or "both".
        </PyParameter>

        <PyParameter name="&#x22;depth&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=2, ge=1, le=10)&#x22;">
          Maximum depth to traverse (1-10).
        </PyParameter>

        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;AssetGraphPayload | dict[str, str]&#x22;">
        AssetGraphPayload containing the filtered subgraph, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_asset_impact&#x22;" type="&#x22;(asset_key, max_depth=Query(default=99, ge=1, le=100), dagster_url=None) -> list[ImpactedAsset] | dict[str, str]&#x22;">
      Get downstream impact analysis for a single asset.

      <PySourceCode>
        ```python
        @router.get("/graph/impact", response_model=list[ImpactedAsset] | dict)
        async def get_asset_impact(
            asset_key: str,
            max_depth: int = Query(default=99, ge=1, le=100),
            dagster_url: str | None = None,
        ) -> list[ImpactedAsset] | dict[str, str]:
            """Get downstream impact analysis for a single asset.

            Args:
                asset_key: Key of the source asset to analyze.
                max_depth: Maximum depth to traverse downstream (1-100).
                dagster_url: Optional Dagster GraphQL URL override.

            Returns:
                List of ImpactedAsset objects or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            graph = await get_asset_graph(dagster_url=dagster_url)
            if isinstance(graph, dict):
                return graph
            return compute_asset_impact(graph, asset_key=asset_key, max_depth=max_depth)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Key of the source asset to analyze.
        </PyParameter>

        <PyParameter name="&#x22;max_depth&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=99, ge=1, le=100)&#x22;">
          Maximum depth to traverse downstream (1-100).
        </PyParameter>

        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[ImpactedAsset] | dict[str, str]&#x22;">
        List of ImpactedAsset objects or error dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
