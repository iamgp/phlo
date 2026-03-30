# adapters (/docs/python-reference/core/phlo/operations/adapters)



Compatibility adapters for sync and async operation contracts.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SyncToAsyncIngesterAdapter&#x22;" href="&#x22;/docs/python-reference/core/phlo/operations/adapters/SyncToAsyncIngesterAdapter&#x22;" />

      <Card title="&#x22;AsyncToSyncIngesterAdapter&#x22;" href="&#x22;/docs/python-reference/core/phlo/operations/adapters/AsyncToSyncIngesterAdapter&#x22;" />

      <Card title="&#x22;SyncToAsyncTransformerAdapter&#x22;" href="&#x22;/docs/python-reference/core/phlo/operations/adapters/SyncToAsyncTransformerAdapter&#x22;" />

      <Card title="&#x22;AsyncToSyncTransformerAdapter&#x22;" href="&#x22;/docs/python-reference/core/phlo/operations/adapters/AsyncToSyncTransformerAdapter&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_ensure_no_running_event_loop&#x22;" type="&#x22;() -> None&#x22;">
      Raise a clear error when sync wrappers are used from an active event loop.

      <PySourceCode>
        ```python
        def _ensure_no_running_event_loop() -> None:
            """Raise a clear error when sync wrappers are used from an active event loop."""

            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return
            raise RuntimeError(
                "Cannot run async operation from sync adapter while an event loop is running. "
                "Use the async operation directly."
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
