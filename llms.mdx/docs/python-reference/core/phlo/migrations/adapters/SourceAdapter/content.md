# SourceAdapter (/docs/python-reference/core/phlo/migrations/adapters/SourceAdapter)



Protocol for migration source readers.

Attributes [#attributes]

<PyAttribute name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="null">
  Identifier for this adapter (for example csv, postgres).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;validate_config&#x22;" type="&#x22;(self, source) -> list[str]&#x22;">
  Validate source configuration and return errors.

  <PySourceCode>
    ```python
    def validate_config(self, source: MigrationSource) -> list[str]:
        """Validate source configuration and return errors."""
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;MigrationSource&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;read_chunks&#x22;" type="&#x22;(self, source, *, chunk_size=50000) -> Iterator[list[dict[str, Any]]]&#x22;">
  Yield row chunks from the source.

  <PySourceCode>
    ```python
    def read_chunks(
        self,
        source: MigrationSource,
        *,
        chunk_size: int = 50_000,
    ) -> Iterator[list[dict[str, Any]]]:
        """Yield row chunks from the source."""
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
  Estimate source row count if possible.

  <PySourceCode>
    ```python
    def estimate_row_count(self, source: MigrationSource) -> int | None:
        """Estimate source row count if possible."""
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;MigrationSource&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int | None&#x22;" />
</PyFunction>
