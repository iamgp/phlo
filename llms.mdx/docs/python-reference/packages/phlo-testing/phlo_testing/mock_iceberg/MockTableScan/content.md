# MockTableScan (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_iceberg/MockTableScan)



Results from scanning a MockTable.

Provides methods to execute scans and return results in various formats.

Attributes [#attributes]

<PyAttribute name="&#x22;table&#x22;" type="null" value="&#x22;table&#x22;">
  MockTable being scanned.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, table) -> None&#x22;">
  Initialize scan for a table.

  <PySourceCode>
    ```python
    def __init__(self, table: MockTable) -> None:
        """Initialize scan for a table.

        Args:
            table: MockTable to scan.

        """
        self.table = table
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table&#x22;" type="&#x22;MockTable&#x22;" value="undefined">
      MockTable to scan.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;to_pandas&#x22;" type="&#x22;(self) -> pd.DataFrame&#x22;">
  Execute scan and return as pandas DataFrame.

  <PySourceCode>
    ```python
    def to_pandas(self) -> pd.DataFrame:
        """Execute scan and return as pandas DataFrame.

        Returns:
            Query results as DataFrame.

        """
        query = f"SELECT * FROM {self.table.full_name}"
        result = self.table._db.execute(query).fetchall()

        if not result:
            # Return empty DataFrame with correct schema
            if isinstance(self.table.schema, dict):
                return pd.DataFrame({col: [] for col in self.table.schema.keys()})
            else:
                return pd.DataFrame({field.name: [] for field in self.table.schema.fields})

        # Get column names from cursor description
        col_names = [desc[0] for desc in self.table._db.description]
        return pd.DataFrame(result, columns=col_names)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
    Query results as DataFrame.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_arrow&#x22;" type="&#x22;(self) -> Any&#x22;">
  Execute scan and return as PyArrow Table.

  <PySourceCode>
    ```python
    def to_arrow(self) -> Any:
        """Execute scan and return as PyArrow Table.

        Returns:
            Query results as Arrow Table.

        Raises:
            ImportError: If PyArrow is not installed.

        """
        try:
            import pyarrow as pa

            df = self.to_pandas()
            return pa.Table.from_pandas(df)
        except ImportError:
            raise ImportError("PyArrow required for to_arrow(). Install: pip install pyarrow")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Query results as Arrow Table.
  </PyFunctionReturn>
</PyFunction>
