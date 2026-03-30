# lineage (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/lineage)



Lineage API Router backed by the neutral lineage sink capability.

Provides endpoints for querying row-level and asset-level lineage data.
Enables data lineage tracking from ingestion through transformation to
consumption, supporting both fine-grained row journeys and coarse-grained
asset dependencies.

Key Endpoints:
GET /rows/\{id}: Get lineage info for a single row.
GET /rows/\{id}/ancestors: Get upstream row lineage.
GET /rows/\{id}/descendants: Get downstream row lineage.
GET /rows/\{id}/journey: Get full row journey (ancestors + descendants).
GET /assets: Get asset lineage graph.

Environment Variables:
PHLO\_LINEAGE\_SINK: Name of the lineage sink provider to use.

Example:
Querying row lineage:

.. code-block:: bash

curl [http://localhost:4000/api/lineage/rows/uuid-123/journey](http://localhost:4000/api/lineage/rows/uuid-123/journey)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['lineage'])&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;RowLineageInfo&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/lineage/RowLineageInfo&#x22;" />

      <Card title="&#x22;LineageJourney&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/lineage/LineageJourney&#x22;" />

      <Card title="&#x22;AssetNode&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/lineage/AssetNode&#x22;" />

      <Card title="&#x22;AssetEdge&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/lineage/AssetEdge&#x22;" />

      <Card title="&#x22;AssetLineageGraph&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/lineage/AssetLineageGraph&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_lineage_sink&#x22;" type="&#x22;() -> LineageSink&#x22;">
      Resolve the configured lineage sink capability.

      <PySourceCode>
        ```python
        def _resolve_lineage_sink() -> LineageSink:
            """Resolve the configured lineage sink capability."""
            discover_capabilities()
            name = os.environ.get(_DEFAULT_LINEAGE_SINK_ENV)
            resolution = resolve_capability("lineage_sink", name)
            if resolution is None:
                available = list_capabilities("lineage_sink")
                if name:
                    raise RuntimeError(f"Lineage sink '{name}' not found. Available providers: {available}")
                if available:
                    raise RuntimeError(
                        "Multiple lineage_sink providers are installed. "
                        f"Set {_DEFAULT_LINEAGE_SINK_ENV} to select one: {available}"
                    )
                raise RuntimeError(
                    "Lineage APIs require a lineage_sink capability. "
                    "Install phlo-lineage or another provider."
                )
            return resolution.provider
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.capabilities.interfaces.LineageSink&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_row_to_lineage_info&#x22;" type="&#x22;(row) -> RowLineageInfo | None&#x22;">
      Convert lineage row payloads into the API model.

      <PySourceCode>
        ```python
        def _row_to_lineage_info(row: dict[str, Any] | None) -> RowLineageInfo | None:
            """Convert lineage row payloads into the API model."""
            if row is None:
                return None
            created_at = row.get("created_at")
            return RowLineageInfo(
                row_id=str(row["row_id"]),
                table_name=str(row["table_name"]),
                source_type=str(row["source_type"]),
                parent_row_ids=[str(value) for value in row.get("parent_row_ids") or []],
                created_at=created_at
                if isinstance(created_at, str)
                else str(created_at)
                if created_at
                else None,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;row&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.lineage.RowLineageInfo | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_coerce_asset_node&#x22;" type="&#x22;(name, payload) -> AssetNode&#x22;">
      Normalize provider-native asset payloads into the API model.

      <PySourceCode>
        ```python
        def _coerce_asset_node(name: str, payload: Any) -> AssetNode:
            """Normalize provider-native asset payloads into the API model."""
            if isinstance(payload, dict):
                return AssetNode(
                    name=name,
                    asset_type=_optional_str(payload.get("asset_type")),
                    status=_optional_str(payload.get("status")),
                    description=_optional_str(payload.get("description")),
                    metadata=_optional_dict(payload.get("metadata")),
                    tags=_optional_dict(payload.get("tags")),
                )
            return AssetNode(
                name=name,
                asset_type=_optional_str(getattr(payload, "asset_type", None)),
                status=_optional_str(getattr(payload, "status", None)),
                description=_optional_str(getattr(payload, "description", None)),
                metadata=_optional_dict(getattr(payload, "metadata", None)),
                tags=_optional_dict(getattr(payload, "tags", None)),
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;payload&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.lineage.AssetNode&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_build_asset_graph&#x22;" type="&#x22;(payload) -> tuple[dict[str, AssetNode], dict[str, list[str]], list[AssetEdge]]&#x22;">
      Normalize provider-native asset graph payloads into the API model.

      <PySourceCode>
        ```python
        def _build_asset_graph(
            payload: Any,
        ) -> tuple[dict[str, AssetNode], dict[str, list[str]], list[AssetEdge]]:
            """Normalize provider-native asset graph payloads into the API model."""
            if isinstance(payload, dict):
                raw_assets = payload.get("assets", {})
                raw_edges = payload.get("edges", {})
                raw_edge_details = payload.get("edge_details", [])
            else:
                raw_assets = getattr(payload, "assets", {})
                raw_edges = getattr(payload, "edges", {})
                raw_edge_details = getattr(payload, "edge_details", [])

            assets = {
                str(name): _coerce_asset_node(str(name), node) for name, node in dict(raw_assets).items()
            }
            edges = {
                str(source): [str(target) for target in targets]
                for source, targets in dict(raw_edges).items()
            }

            edge_details: list[AssetEdge] = []
            if raw_edge_details:
                for edge in raw_edge_details:
                    if isinstance(edge, dict):
                        source = str(edge["source"])
                        target = str(edge["target"])
                        metadata = _optional_dict(edge.get("metadata"))
                        tags = _optional_dict(edge.get("tags"))
                    else:
                        source = str(getattr(edge, "source"))
                        target = str(getattr(edge, "target"))
                        metadata = _optional_dict(getattr(edge, "metadata", None))
                        tags = _optional_dict(getattr(edge, "tags", None))
                    edge_details.append(
                        AssetEdge(source=source, target=target, metadata=metadata, tags=tags)
                    )
            else:
                for source, targets in edges.items():
                    for target in targets:
                        edge_details.append(AssetEdge(source=source, target=target))

            for edge in edge_details:
                assets.setdefault(edge.source, AssetNode(name=edge.source))
                assets.setdefault(edge.target, AssetNode(name=edge.target))

            return assets, edges, edge_details
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;payload&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[dict[str, phlo_api.observatory_api.lineage.AssetNode], dict[str, list[str]], list[phlo_api.observatory_api.lineage.AssetEdge]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_filter_asset_graph&#x22;" type="&#x22;(assets, edges, edge_details, *, asset_key, direction, depth) -> tuple[dict[str, AssetNode], dict[str, list[str]], list[AssetEdge]]&#x22;">
      Filter an asset graph around a focal asset.

      <PySourceCode>
        ```python
        def _filter_asset_graph(
            assets: dict[str, AssetNode],
            edges: dict[str, list[str]],
            edge_details: list[AssetEdge],
            *,
            asset_key: str,
            direction: str,
            depth: int | None,
        ) -> tuple[dict[str, AssetNode], dict[str, list[str]], list[AssetEdge]]:
            """Filter an asset graph around a focal asset."""
            reverse_edges: dict[str, list[str]] = {}
            for source, targets in edges.items():
                for target in targets:
                    reverse_edges.setdefault(target, []).append(source)

            def _walk(
                start: str,
                adjacency: dict[str, list[str]],
                max_depth: int | None,
            ) -> set[str]:
                visited: set[str] = set()
                queue: deque[tuple[str, int]] = deque([(start, 0)])
                while queue:
                    current, current_depth = queue.popleft()
                    if current in visited:
                        continue
                    visited.add(current)
                    if max_depth is not None and current_depth >= max_depth:
                        continue
                    for neighbor in adjacency.get(current, []):
                        if neighbor not in visited:
                            queue.append((neighbor, current_depth + 1))
                visited.discard(start)
                return visited

            upstream = (
                _walk(asset_key, reverse_edges, depth) if direction in {"upstream", "both"} else set()
            )
            downstream = _walk(asset_key, edges, depth) if direction in {"downstream", "both"} else set()
            keep_assets = {asset_key} | upstream | downstream

            filtered_assets = {name: node for name, node in assets.items() if name in keep_assets}
            filtered_edges = {
                source: [target for target in targets if target in keep_assets]
                for source, targets in edges.items()
                if source in keep_assets
            }
            filtered_edge_details = [
                edge for edge in edge_details if edge.source in keep_assets and edge.target in keep_assets
            ]
            return filtered_assets, filtered_edges, filtered_edge_details
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;assets&#x22;" type="&#x22;dict[str, AssetNode]&#x22;" value="null" />

        <PyParameter name="&#x22;edges&#x22;" type="&#x22;dict[str, list[str]]&#x22;" value="null" />

        <PyParameter name="&#x22;edge_details&#x22;" type="&#x22;list[AssetEdge]&#x22;" value="null" />

        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;direction&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;depth&#x22;" type="&#x22;int | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[dict[str, phlo_api.observatory_api.lineage.AssetNode], dict[str, list[str]], list[phlo_api.observatory_api.lineage.AssetEdge]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_optional_str&#x22;" type="&#x22;(value) -> str | None&#x22;">
      <PySourceCode>
        ```python
        def _optional_str(value: Any) -> str | None:
            if value is None:
                return None
            return str(value)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_optional_dict&#x22;" type="&#x22;(value) -> dict[str, Any] | None&#x22;">
      <PySourceCode>
        ```python
        def _optional_dict(value: Any) -> dict[str, Any] | None:
            return value if isinstance(value, dict) else None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any] | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_row_lineage&#x22;" type="&#x22;(row_id) -> RowLineageInfo | dict[str, str]&#x22;">
      Get lineage info for a single row.

      <PySourceCode>
        ```python
        @router.get("/rows/{row_id}", response_model=RowLineageInfo | dict)
        async def get_row_lineage(row_id: str) -> RowLineageInfo | dict[str, str]:
            """Get lineage info for a single row.

            Args:
                row_id: The unique row identifier to look up.

            Returns:
                RowLineageInfo for the current row, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                journey = _resolve_lineage_sink().get_row_journey(row_id=row_id, depth=1)
                current = _row_to_lineage_info(journey.get("current"))
                if current is None:
                    return {"error": f"Row {row_id} not found in lineage store"}
                return current
            except RuntimeError as exc:
                return {"error": str(exc)}
            except Exception as exc:
                logger.exception("lineage_row_lookup_failed")
                return {"error": str(exc)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
          The unique row identifier to look up.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;RowLineageInfo | dict[str, str]&#x22;">
        RowLineageInfo for the current row, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_row_ancestors&#x22;" type="&#x22;(row_id, max_depth=Query(default=10, le=50)) -> list[RowLineageInfo] | dict[str, str]&#x22;">
      Get ancestor rows recursively upstream.

      <PySourceCode>
        ```python
        @router.get("/rows/{row_id}/ancestors", response_model=list[RowLineageInfo] | dict)
        async def get_row_ancestors(
            row_id: str,
            max_depth: int = Query(default=10, le=50),
        ) -> list[RowLineageInfo] | dict[str, str]:
            """Get ancestor rows recursively upstream.

            Args:
                row_id: The unique row identifier to trace upstream.
                max_depth: Maximum depth to traverse (default: 10, max: 50).

            Returns:
                List of RowLineageInfo for ancestor rows, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                journey = _resolve_lineage_sink().get_row_journey(row_id=row_id, depth=max_depth)
                return [_row_to_lineage_info(row) for row in journey.get("ancestors", []) if row]
            except RuntimeError as exc:
                return {"error": str(exc)}
            except Exception as exc:
                logger.exception("lineage_row_ancestors_failed")
                return {"error": str(exc)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
          The unique row identifier to trace upstream.
        </PyParameter>

        <PyParameter name="&#x22;max_depth&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=10, le=50)&#x22;">
          Maximum depth to traverse (default: 10, max: 50).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[RowLineageInfo] | dict[str, str]&#x22;">
        List of RowLineageInfo for ancestor rows, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_row_descendants&#x22;" type="&#x22;(row_id, max_depth=Query(default=10, le=50)) -> list[RowLineageInfo] | dict[str, str]&#x22;">
      Get descendant rows recursively downstream.

      <PySourceCode>
        ```python
        @router.get("/rows/{row_id}/descendants", response_model=list[RowLineageInfo] | dict)
        async def get_row_descendants(
            row_id: str,
            max_depth: int = Query(default=10, le=50),
        ) -> list[RowLineageInfo] | dict[str, str]:
            """Get descendant rows recursively downstream.

            Args:
                row_id: The unique row identifier to trace downstream.
                max_depth: Maximum depth to traverse (default: 10, max: 50).

            Returns:
                List of RowLineageInfo for descendant rows, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                journey = _resolve_lineage_sink().get_row_journey(row_id=row_id, depth=max_depth)
                return [_row_to_lineage_info(row) for row in journey.get("descendants", []) if row]
            except RuntimeError as exc:
                return {"error": str(exc)}
            except Exception as exc:
                logger.exception("lineage_row_descendants_failed")
                return {"error": str(exc)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
          The unique row identifier to trace downstream.
        </PyParameter>

        <PyParameter name="&#x22;max_depth&#x22;" type="&#x22;int&#x22;" value="&#x22;Query(default=10, le=50)&#x22;">
          Maximum depth to traverse (default: 10, max: 50).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list[RowLineageInfo] | dict[str, str]&#x22;">
        List of RowLineageInfo for descendant rows, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_row_journey&#x22;" type="&#x22;(row_id) -> LineageJourney | dict[str, str]&#x22;">
      Get full lineage journey for a row (current, ancestors, descendants).

      <PySourceCode>
        ```python
        @router.get("/rows/{row_id}/journey", response_model=LineageJourney | dict)
        async def get_row_journey(row_id: str) -> LineageJourney | dict[str, str]:
            """Get full lineage journey for a row (current, ancestors, descendants).

            Args:
                row_id: The unique row identifier to trace.

            Returns:
                LineageJourney with current, ancestors, and descendants, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                journey = _resolve_lineage_sink().get_row_journey(row_id=row_id, depth=10)
                return LineageJourney(
                    current=_row_to_lineage_info(journey.get("current")),
                    ancestors=[_row_to_lineage_info(row) for row in journey.get("ancestors", []) if row],
                    descendants=[
                        _row_to_lineage_info(row) for row in journey.get("descendants", []) if row
                    ],
                )
            except RuntimeError as exc:
                return {"error": str(exc)}
            except Exception as exc:
                logger.exception("lineage_row_journey_failed")
                return {"error": str(exc)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;row_id&#x22;" type="&#x22;str&#x22;" value="undefined">
          The unique row identifier to trace.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;LineageJourney | dict[str, str]&#x22;">
        LineageJourney with current, ancestors, and descendants, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_asset_lineage_graph&#x22;" type="&#x22;(asset_key=Query(default=None), direction=Query(default='both', pattern='^(upstream|downstream|both)$'), depth=Query(default=None, ge=1, le=50)) -> AssetLineageGraph | dict[str, str]&#x22;">
      Get the asset lineage graph.

      Returns the full asset graph or a filtered subgraph around a focal asset.

      <PySourceCode>
        ```python
        @router.get("/assets", response_model=AssetLineageGraph | dict)
        async def get_asset_lineage_graph(
            asset_key: str | None = Query(default=None),
            direction: str = Query(default="both", pattern="^(upstream|downstream|both)$"),
            depth: int | None = Query(default=None, ge=1, le=50),
        ) -> AssetLineageGraph | dict[str, str]:
            """Get the asset lineage graph.

            Returns the full asset graph or a filtered subgraph around a focal asset.

            Args:
                asset_key: Optional focal asset key to filter the graph around.
                direction: Direction to traverse: "upstream", "downstream", or "both".
                depth: Optional maximum depth to traverse (1-50).

            Returns:
                AssetLineageGraph with assets and edges, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                assets, edges, edge_details = _build_asset_graph(_resolve_lineage_sink().get_asset_graph())
                if asset_key:
                    if asset_key not in assets:
                        return {"error": f"Asset {asset_key} not found in lineage store"}
                    assets, edges, edge_details = _filter_asset_graph(
                        assets,
                        edges,
                        edge_details,
                        asset_key=asset_key,
                        direction=direction,
                        depth=depth,
                    )
                return AssetLineageGraph(assets=assets, edges=edges, edge_details=edge_details)
            except RuntimeError as exc:
                return {"error": str(exc)}
            except Exception as exc:
                logger.exception("lineage_asset_graph_failed")
                return {"error": str(exc)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Query(default=None)&#x22;">
          Optional focal asset key to filter the graph around.
        </PyParameter>

        <PyParameter name="&#x22;direction&#x22;" type="&#x22;str&#x22;" value="&#x22;Query(default='both', pattern='^(upstream|downstream|both)$')&#x22;">
          Direction to traverse: "upstream", "downstream", or "both".
        </PyParameter>

        <PyParameter name="&#x22;depth&#x22;" type="&#x22;int | None&#x22;" value="&#x22;Query(default=None, ge=1, le=50)&#x22;">
          Optional maximum depth to traverse (1-50).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;AssetLineageGraph | dict[str, str]&#x22;">
        AssetLineageGraph with assets and edges, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
