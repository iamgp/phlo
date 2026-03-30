# search (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/search)



Search API Router.

Endpoint to aggregate searchable entities for the command palette.
Combines data from Dagster (assets) and Iceberg/Trino (tables, columns).

This module builds a unified search index that enables quick navigation
and discovery across the data platform, including Dagster assets,
Iceberg tables, and table columns.

Key Endpoints:
GET /index: Build the observability search index.

Example:
Building search index:

.. code-block:: bash

curl "[http://localhost:4000/api/search/index?include\_columns=true](http://localhost:4000/api/search/index?include_columns=true)"

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['search'])&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SearchableAsset&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/search/SearchableAsset&#x22;" />

      <Card title="&#x22;SearchableTable&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/search/SearchableTable&#x22;" />

      <Card title="&#x22;SearchableColumn&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/search/SearchableColumn&#x22;" />

      <Card title="&#x22;SearchIndex&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/search/SearchIndex&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_search_index&#x22;" type="&#x22;(dagster_url=None, trino_url=None, catalog=None, branch=None, include_columns=Query(default=True)) -> SearchIndex | dict[str, str]&#x22;">
      Build the observability search index.

      Aggregates searchable entities from Dagster (assets) and Trino (tables, columns).

      <PySourceCode>
        ```python
        @router.get("/index", response_model=SearchIndex | dict)
        async def get_search_index(
            dagster_url: str | None = None,
            trino_url: str | None = None,
            catalog: str | None = None,
            branch: str | None = None,
            include_columns: bool = Query(default=True),
        ) -> SearchIndex | dict[str, str]:
            """Build the observability search index.

            Aggregates searchable entities from Dagster (assets) and Trino (tables, columns).

            Args:
                dagster_url: Optional Dagster GraphQL URL override.
                trino_url: Optional Trino URL override.
                catalog: Trino catalog name (default from resolve_default_catalog).
                branch: Trino schema/branch context.
                include_columns: Whether to include column metadata in results (default: True).

            Returns:
                SearchIndex with assets, tables, and columns, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                effective_catalog = catalog or resolve_default_catalog()
                # Fetch assets and tables in parallel
                assets_result, tables_result = await asyncio.gather(
                    get_assets(dagster_url),
                    get_tables(branch, effective_catalog, None, trino_url),
                )

                # Handle errors
                if isinstance(assets_result, dict) and "error" in assets_result:
                    return {"error": f"Failed to fetch assets: {assets_result['error']}"}
                if isinstance(tables_result, dict) and "error" in tables_result:
                    return {"error": f"Failed to fetch tables: {tables_result['error']}"}

                # Convert assets
                assets = [
                    SearchableAsset(
                        id=asset.id,
                        key_path=asset.key_path,
                        group_name=asset.group_name,
                        compute_kind=asset.compute_kind,
                    )
                    for asset in assets_result
                ]

                # Convert tables
                tables = [
                    SearchableTable(
                        catalog=table.catalog,
                        schema_name=table.schema_name,
                        name=table.name,
                        full_name=table.full_name,
                        layer=table.layer,
                    )
                    for table in tables_result
                ]

                # Fetch columns if requested
                columns: list[SearchableColumn] = []
                if include_columns and tables:
                    # Limit to first 20 tables to avoid overwhelming the system
                    tables_to_fetch = tables[:20]

                    for table in tables_to_fetch:
                        try:
                            schema_result = await get_table_schema(
                                table.name,
                                table.schema_name,
                                None,
                                effective_catalog,
                                trino_url,
                            )
                            if isinstance(schema_result, list):
                                for col in schema_result:
                                    columns.append(
                                        SearchableColumn(
                                            table_name=table.name,
                                            table_schema=table.schema_name,
                                            name=col.name,
                                            type=col.type,
                                        )
                                    )
                        except Exception:
                            pass  # Skip tables that fail

                return SearchIndex(
                    assets=assets,
                    tables=tables,
                    columns=columns,
                    last_updated=datetime.now().isoformat(),
                )
            except Exception as e:
                logger.exception("Failed to build search index")
                return {"error": str(e)}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dagster_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Dagster GraphQL URL override.
        </PyParameter>

        <PyParameter name="&#x22;trino_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional Trino URL override.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Trino catalog name (default from resolve\_default\_catalog).
        </PyParameter>

        <PyParameter name="&#x22;branch&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Trino schema/branch context.
        </PyParameter>

        <PyParameter name="&#x22;include_columns&#x22;" type="&#x22;bool&#x22;" value="&#x22;Query(default=True)&#x22;">
          Whether to include column metadata in results (default: True).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;SearchIndex | dict[str, str]&#x22;">
        SearchIndex with assets, tables, and columns, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
