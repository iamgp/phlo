# utils (/docs/python-reference/packages/phlo-testing/phlo_testing/utils)



Utility helpers for phlo-testing.

This module provides data normalization utilities for converting between
different data formats commonly used in Phlo testing scenarios.

Example:

> > > from phlo\_testing.utils import to\_dataframe, to\_records
> > > data = \[\{"id": 1, "name": "Alice"}, \{"id": 2, "name": "Bob"}]
> > > df = to\_dataframe(data)
> > > records = to\_records(df)

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;to_dataframe&#x22;" type="&#x22;(data) -> pd.DataFrame&#x22;">
      Normalize data into a pandas DataFrame.

      Converts list of dictionaries or an existing DataFrame into a
      standardized pandas DataFrame format for testing.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > data = \[\{"id": 1, "value": 100}, \{"id": 2, "value": 200}]
        > > > df = to\_dataframe(data)
        > > > print(df.columns)
        > > > Index(\['id', 'value'], dtype='object')
      </Callout>

      <PySourceCode>
        ```python
        def to_dataframe(data: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
            """Normalize data into a pandas DataFrame.

            Converts list of dictionaries or an existing DataFrame into a
            standardized pandas DataFrame format for testing.

            Args:
                data: Input data as either a pandas DataFrame or a list of
                    dictionaries with string keys.

            Returns:
                A pandas DataFrame containing the normalized data.

            Example:
                >>> data = [{"id": 1, "value": 100}, {"id": 2, "value": 200}]
                >>> df = to_dataframe(data)
                >>> print(df.columns)
                Index(['id', 'value'], dtype='object')

            """
            if isinstance(data, pd.DataFrame):
                return data
            return pd.DataFrame(data)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;pd.DataFrame | list[dict[str, Any]]&#x22;" value="undefined">
          Input data as either a pandas DataFrame or a list of
          dictionaries with string keys.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
        A pandas DataFrame containing the normalized data.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;to_records&#x22;" type="&#x22;(data) -> list[dict[str, Any]]&#x22;">
      Normalize data into a list of records.

      Converts a DataFrame or list of dictionaries into a standardized
      list of dictionary records format.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > df = pd.DataFrame(\{"id": \[1, 2], "name": \["Alice", "Bob"]})
        > > > records = to\_records(df)
        > > > print(records)
        > > > \[\{'id': 1, 'name': 'Alice'}, \{'id': 2, 'name': 'Bob'}]
      </Callout>

      <PySourceCode>
        ```python
        def to_records(data: pd.DataFrame | list[dict[str, Any]]) -> list[dict[str, Any]]:
            """Normalize data into a list of records.

            Converts a DataFrame or list of dictionaries into a standardized
            list of dictionary records format.

            Args:
                data: Input data as either a pandas DataFrame or a list of
                    dictionaries with string keys.

            Returns:
                A list of dictionaries where each dictionary represents a row
                with column names as keys.

            Example:
                >>> df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
                >>> records = to_records(df)
                >>> print(records)
                [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]

            """
            df = to_dataframe(data)
            return df.to_dict("records")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;pd.DataFrame | list[dict[str, Any]]&#x22;" value="undefined">
          Input data as either a pandas DataFrame or a list of
          dictionaries with string keys.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        A list of dictionaries where each dictionary represents a row
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
