# NativeProcess (/docs/python-reference/core/phlo/plugins/compose/native/NativeProcess)



Represents a running native process.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

<PyAttribute name="&#x22;process&#x22;" type="&#x22;subprocess.Popen[str]&#x22;" value="null" />

<PyAttribute name="&#x22;health_check_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;started_at&#x22;" type="&#x22;float&#x22;" value="&#x22;field(default_factory=(time.time))&#x22;" />

<PyAttribute name="&#x22;log_file&#x22;" type="&#x22;TextIO | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;is_running&#x22;" type="&#x22;bool&#x22;" value="null">
  Check if process is still running.
</PyAttribute>

<PyAttribute name="&#x22;pid&#x22;" type="&#x22;int&#x22;" value="null">
  Get process ID.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;close_log_file&#x22;" type="&#x22;(self) -> None&#x22;">
  Close the process log file handle when one is open.

  <PySourceCode>
    ```python
    def close_log_file(self) -> None:
        """Close the process log file handle when one is open."""

        if self.log_file is None:
            return
        try:
            self.log_file.close()
        except Exception:
            logger.exception("Failed to close log file for native process")
        finally:
            self.log_file = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, process, health_check_url=None, started_at=time.time(), log_file=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;process&#x22;" type="&#x22;subprocess.Popen[str]&#x22;" value="null" />

    <PyParameter name="&#x22;health_check_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;started_at&#x22;" type="&#x22;float&#x22;" value="&#x22;time.time()&#x22;" />

    <PyParameter name="&#x22;log_file&#x22;" type="&#x22;TextIO | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
