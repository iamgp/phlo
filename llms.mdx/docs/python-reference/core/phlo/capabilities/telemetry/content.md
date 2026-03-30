# telemetry (/docs/python-reference/core/phlo/capabilities/telemetry)



Core telemetry recording helpers.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;TelemetryRecorder&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/telemetry/TelemetryRecorder&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_default_path&#x22;" type="&#x22;() -> Path&#x22;">
      Return the default telemetry output path.

      <PySourceCode>
        ```python
        def _default_path() -> Path:
            """Return the default telemetry output path."""
            env_path = os.environ.get("PHLO_TELEMETRY_PATH")
            if env_path:
                return Path(env_path)
            return Path.cwd() / ".phlo" / "telemetry" / "events.jsonl"
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_telemetry_path&#x22;" type="&#x22;(path=None) -> Path&#x22;">
      Resolve the telemetry JSONL path.

      <PySourceCode>
        ```python
        def get_telemetry_path(path: Path | None = None) -> Path:
            """Resolve the telemetry JSONL path."""
            return path or _default_path()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;iter_telemetry_events&#x22;" type="&#x22;(path=None) -> Iterator[dict[str, Any]]&#x22;">
      Yield telemetry events from the JSONL file.

      <PySourceCode>
        ```python
        def iter_telemetry_events(path: Path | None = None) -> Iterator[dict[str, Any]]:
            """Yield telemetry events from the JSONL file."""
            event_path = get_telemetry_path(path)
            if not event_path.exists():
                return iter(())

            def _iter() -> Iterator[dict[str, Any]]:
                with event_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            payload = json.loads(line)
                        except json.JSONDecodeError:
                            logger.debug(
                                "telemetry_event_decode_failed",
                                path=str(event_path),
                                line=line,
                                exc_info=True,
                            )
                            continue
                        if isinstance(payload, dict):
                            yield payload

            return _iter()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.Iterator[dict[str, typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_serialize_event&#x22;" type="&#x22;(event) -> dict[str, Any]&#x22;">
      Serialize a TelemetryEvent into JSON-friendly primitives.

      <PySourceCode>
        ```python
        def _serialize_event(event: TelemetryEvent) -> dict[str, Any]:
            """Serialize a TelemetryEvent into JSON-friendly primitives."""
            payload = asdict(event)
            payload["timestamp"] = event.timestamp.isoformat()
            return payload
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event&#x22;" type="&#x22;TelemetryEvent&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
