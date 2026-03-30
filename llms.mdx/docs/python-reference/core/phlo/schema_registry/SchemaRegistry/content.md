# SchemaRegistry (/docs/python-reference/core/phlo/schema_registry/SchemaRegistry)



PostgreSQL-backed schema snapshot registry.

Attributes [#attributes]

<PyAttribute name="&#x22;connection_string&#x22;" type="null" value="&#x22;connection_string&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, connection_string)&#x22;">
  <PySourceCode>
    ```python
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;connection_string&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_ensure_schema&#x22;" type="&#x22;(self) -> None&#x22;">
  <PySourceCode>
    ```python
    def _ensure_schema(self) -> None:
        if SchemaRegistry._schema_initialized:
            return
        try:
            self._setup_schema()
            SchemaRegistry._schema_initialized = True
        except Exception as e:
            if "already exists" in str(e).lower():
                SchemaRegistry._schema_initialized = True
            else:
                logger.warning("schema_registry_init_failed", error=str(e))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_setup_schema&#x22;" type="&#x22;(self) -> None&#x22;">
  <PySourceCode>
    ```python
    def _setup_schema(self) -> None:
        sql_path = Path(__file__).parent / "sql" / "001_create_schema_registry.sql"
        with sql_path.open() as f:
            schema_sql = f.read()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
        logger.info("schema_registry_setup_complete")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;snapshot_schema&#x22;" type="&#x22;(self, table_name, schema, *, run_id=None, source='materialization') -> str&#x22;">
  Snapshot a schema. Returns snapshot\_id. Dedupes by (table\_name, schema\_hash).

  <PySourceCode>
    ```python
    def snapshot_schema(
        self,
        table_name: str,
        schema: NormalizedSchema,
        *,
        run_id: str | None = None,
        source: str = "materialization",
    ) -> str:
        """Snapshot a schema. Returns snapshot_id. Dedupes by (table_name, schema_hash)."""
        canonical = _canonical_schema_json(schema)
        schema_hash = _schema_hash(canonical)
        snapshot_id = str(ulid.ULID())

        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO phlo.schema_snapshots
                    (snapshot_id, table_name, schema, schema_hash, run_id, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (table_name, schema_hash) DO UPDATE
                        SET created_at = NOW(),
                            snapshot_id = EXCLUDED.snapshot_id,
                            run_id = EXCLUDED.run_id,
                            source = EXCLUDED.source
                    RETURNING snapshot_id
                    """,
                    (snapshot_id, table_name, canonical, schema_hash, run_id, source),
                )
                row = cur.fetchone()
            conn.commit()

        persisted_snapshot_id = row[0] if row else snapshot_id
        logger.info(
            "schema_snapshot_created",
            table_name=table_name,
            snapshot_id=persisted_snapshot_id,
        )
        return persisted_snapshot_id
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;NormalizedSchema&#x22;" value="null" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;str&#x22;" value="&#x22;'materialization'&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_latest_snapshots&#x22;" type="&#x22;(self, table_name, limit=2) -> list[SchemaSnapshot]&#x22;">
  Get most recent snapshots for a table.

  <PySourceCode>
    ```python
    def get_latest_snapshots(self, table_name: str, limit: int = 2) -> list[SchemaSnapshot]:
        """Get most recent snapshots for a table."""
        self._ensure_schema()
        with psycopg2.connect(self.connection_string) as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT snapshot_id, table_name, schema, schema_hash,
                           created_at, run_id, source
                    FROM phlo.schema_snapshots
                    WHERE table_name = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                (table_name, limit),
            )
            rows = cur.fetchall()
        return [
            SchemaSnapshot(
                snapshot_id=r[0],
                table_name=r[1],
                schema_json=r[2] if isinstance(r[2], str) else json.dumps(r[2]),
                schema_hash=r[3],
                created_at=r[4].isoformat() if r[4] else None,
                run_id=r[5],
                source=r[6],
            )
            for r in rows
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;2&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.schema_registry.SchemaSnapshot]&#x22;" />
</PyFunction>
