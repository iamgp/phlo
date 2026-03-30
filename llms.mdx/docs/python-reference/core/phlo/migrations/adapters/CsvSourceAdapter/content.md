# CsvSourceAdapter (/docs/python-reference/core/phlo/migrations/adapters/CsvSourceAdapter)



CSV source adapter implementation.

Attributes [#attributes]

<PyAttribute name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="null" />

Functions [#functions]

<PyFunction name="&#x22;validate_config&#x22;" type="&#x22;(self, source) -> list[str]&#x22;">
  <PySourceCode>
    ```python
    def validate_config(self, source: MigrationSource) -> list[str]:
        errors: list[str] = []
        if not source.path:
            errors.append("source.path is required for csv source")
            return errors
        csv_path = Path(source.path)
        if not csv_path.exists():
            errors.append(f"CSV file not found: {csv_path}")
        if source.query:
            errors.append("source.query is not supported for csv source")
        if source.table:
            errors.append("source.table is not supported for csv source")
        return errors
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;MigrationSource&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;read_chunks&#x22;" type="&#x22;(self, source, *, chunk_size=50000) -> Iterator[list[dict[str, Any]]]&#x22;">
  <PySourceCode>
    ```python
    def read_chunks(
        self,
        source: MigrationSource,
        *,
        chunk_size: int = 50_000,
    ) -> Iterator[list[dict[str, Any]]]:
        if not source.path:
            raise ValueError("source.path is required for csv source")

        csv_path = Path(source.path)
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            buffer: list[dict[str, Any]] = []
            for row in reader:
                buffer.append(dict(row))
                if len(buffer) >= chunk_size:
                    yield buffer
                    buffer = []
            if buffer:
                yield buffer
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;MigrationSource&#x22;" value="null" />

    <PyParameter name="&#x22;chunk_size&#x22;" type="&#x22;int&#x22;" value="&#x22;50000&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterator[list[dict[str, typing.Any]]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;estimate_row_count&#x22;" type="&#x22;(self, source) -> int | None&#x22;">
  <PySourceCode>
    ```python
    def estimate_row_count(self, source: MigrationSource) -> int | None:
        if not source.path:
            return None
        csv_path = Path(source.path)
        if not csv_path.exists():
            return None

        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            line_count = sum(1 for _ in handle)
        return max(0, line_count - 1)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;MigrationSource&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int | None&#x22;" />
</PyFunction>
