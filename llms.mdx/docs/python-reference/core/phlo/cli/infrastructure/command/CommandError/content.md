# CommandError (/docs/python-reference/core/phlo/cli/infrastructure/command/CommandError)



Error raised when a subprocess command exits with a non-zero status.

Attributes [#attributes]

<PyAttribute name="&#x22;cmd&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

<PyAttribute name="&#x22;returncode&#x22;" type="&#x22;int&#x22;" value="null" />

<PyAttribute name="&#x22;stdout&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;stderr&#x22;" type="&#x22;str&#x22;" value="null" />

Functions [#functions]

<PyFunction name="&#x22;__post_init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Populate RuntimeError args tuple for consistent exception rendering.

  <PySourceCode>
    ```python
    def __post_init__(self) -> None:
        """Populate RuntimeError args tuple for consistent exception rendering."""

        object.__setattr__(self, "args", (self.cmd, self.returncode, self.stdout, self.stderr))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__str__&#x22;" type="&#x22;(self) -> str&#x22;">
  Render a readable command failure message.

  <PySourceCode>
    ```python
    def __str__(self) -> str:
        """Render a readable command failure message."""

        cmd = " ".join(self.cmd)
        stderr = self.stderr.strip()
        if stderr:
            return f"Command failed ({self.returncode}): {cmd}\n{stderr}"
        return f"Command failed ({self.returncode}): {cmd}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, cmd, returncode, stdout, stderr) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;cmd&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

    <PyParameter name="&#x22;returncode&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;stdout&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;stderr&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
