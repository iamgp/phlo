# TestAssetResult (/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/TestAssetResult)



Result from test\_asset\_execution.

Encapsulates the outcome of testing an asset function including
success status, returned data, and any errors.

Attributes [#attributes]

<PyAttribute name="&#x22;success&#x22;" type="null" value="&#x22;success&#x22;">
  Whether the asset execution succeeded.
</PyAttribute>

<PyAttribute name="&#x22;data&#x22;" type="null" value="&#x22;data&#x22;">
  Resulting DataFrame if available.
</PyAttribute>

<PyAttribute name="&#x22;error&#x22;" type="null" value="&#x22;error&#x22;">
  Exception if execution failed.
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="null" value="&#x22;metadata or {}&#x22;">
  Additional metadata about the execution.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, success, data=None, error=None, metadata=None)&#x22;">
  Initialize test result.

  <PySourceCode>
    ```python
    def __init__(
        self,
        success: bool,
        data: Optional[pd.DataFrame] = None,
        error: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize test result.

        Args:
            success: Whether execution succeeded.
            data: Optional DataFrame with results.
            error: Optional exception if failed.
            metadata: Optional dictionary of metadata.

        """
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;success&#x22;" type="&#x22;bool&#x22;" value="undefined">
      Whether execution succeeded.
    </PyParameter>

    <PyParameter name="&#x22;data&#x22;" type="&#x22;Optional[pd.DataFrame]&#x22;" value="&#x22;None&#x22;">
      Optional DataFrame with results.
    </PyParameter>

    <PyParameter name="&#x22;error&#x22;" type="&#x22;Optional[Exception]&#x22;" value="&#x22;None&#x22;">
      Optional exception if failed.
    </PyParameter>

    <PyParameter name="&#x22;metadata&#x22;" type="&#x22;Optional[Dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Optional dictionary of metadata.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;__repr__&#x22;" type="&#x22;(self) -> str&#x22;">
  String representation.

  <PySourceCode>
    ```python
    def __repr__(self) -> str:
        """String representation.

        Returns:
            String with status and row count.

        """
        status = "SUCCESS" if self.success else "FAILED"
        rows = len(self.data) if self.data is not None else 0
        return f"TestAssetResult(status={status}, rows={rows})"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    String with status and row count.
  </PyFunctionReturn>
</PyFunction>
