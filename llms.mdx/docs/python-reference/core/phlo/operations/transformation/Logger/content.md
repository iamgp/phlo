# Logger (/docs/python-reference/core/phlo/operations/transformation/Logger)



Minimal logging protocol for transformation operations.

Functions [#functions]

<PyFunction name="&#x22;info&#x22;" type="&#x22;(self, msg, *args, **kwargs) -> None&#x22;">
  Log an informational transformation message.

  <PySourceCode>
    ```python
    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log an informational transformation message."""
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;msg&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;args&#x22;" type="&#x22;object&#x22;" value="&#x22;()&#x22;" />

    <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;object&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;warning&#x22;" type="&#x22;(self, msg, *args, **kwargs) -> None&#x22;">
  Log a transformation warning message.

  <PySourceCode>
    ```python
    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log a transformation warning message."""
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;msg&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;args&#x22;" type="&#x22;object&#x22;" value="&#x22;()&#x22;" />

    <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;object&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;error&#x22;" type="&#x22;(self, msg, *args, **kwargs) -> None&#x22;">
  Log a transformation error message.

  <PySourceCode>
    ```python
    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log a transformation error message."""
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;msg&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;args&#x22;" type="&#x22;object&#x22;" value="&#x22;()&#x22;" />

    <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;object&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
