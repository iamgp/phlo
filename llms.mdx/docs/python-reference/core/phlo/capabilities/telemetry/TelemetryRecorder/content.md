# TelemetryRecorder (/docs/python-reference/core/phlo/capabilities/telemetry/TelemetryRecorder)



Write telemetry events to a JSONL file.

Attributes [#attributes]

<PyAttribute name="&#x22;path&#x22;" type="null" value="&#x22;path or _default_path()&#x22;" />

<PyAttribute name="&#x22;max_bytes&#x22;" type="null" value="&#x22;max_bytes&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, path=None, max_bytes=20000000) -> None&#x22;">
  <PySourceCode>
    ```python
    def __init__(self, path: Path | None = None, max_bytes: int = 20_000_000) -> None:
        self.path = path or _default_path()
        self.max_bytes = max_bytes
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;max_bytes&#x22;" type="&#x22;int&#x22;" value="&#x22;20000000&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;record&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Append a telemetry event to the JSONL file, rotating if needed.

  <PySourceCode>
    ```python
    def record(self, event: TelemetryEvent) -> None:
        """Append a telemetry event to the JSONL file, rotating if needed."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._rotate_if_needed()
            payload = _serialize_event(event)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")
        except Exception:
            logger.warning("telemetry_record_failed", path=str(self.path), exc_info=True)
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;TelemetryEvent&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_rotate_if_needed&#x22;" type="&#x22;(self) -> None&#x22;">
  Rotate the telemetry file when it exceeds max\_bytes.

  <PySourceCode>
    ```python
    def _rotate_if_needed(self) -> None:
        """Rotate the telemetry file when it exceeds max_bytes."""
        if not self.path.exists():
            return
        if self.path.stat().st_size < self.max_bytes:
            return
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        rotated = self.path.with_name(f"{self.path.stem}.{timestamp}{self.path.suffix}")
        self.path.rename(rotated)
        logger.debug(
            "telemetry_file_rotated",
            source_path=str(self.path),
            rotated_path=str(rotated),
            max_bytes=self.max_bytes,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
