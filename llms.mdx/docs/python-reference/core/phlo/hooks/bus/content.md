# bus (/docs/python-reference/core/phlo/hooks/bus)



Hook bus implementation for dispatching plugin events.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;RegisteredHook&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/bus/RegisteredHook&#x22;" />

      <Card title="&#x22;HookBus&#x22;" href="&#x22;/docs/python-reference/core/phlo/hooks/bus/HookBus&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_event_asset_keys&#x22;" type="&#x22;(event) -> set[str]&#x22;">
      Collect asset keys from hook event payloads.

      <PySourceCode>
        ```python
        def _event_asset_keys(event: HookEvent) -> set[str]:
            """Collect asset keys from hook event payloads."""
            keys: set[str] = set()
            asset_key = getattr(event, "asset_key", None)
            if isinstance(asset_key, str):
                keys.add(asset_key)
            asset_keys = getattr(event, "asset_keys", None)
            if isinstance(asset_keys, Iterable) and not isinstance(asset_keys, (str, bytes)):
                for item in asset_keys:
                    if isinstance(item, str):
                        keys.add(item)
            return keys
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event&#x22;" type="&#x22;HookEvent&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;set[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_plugin_name&#x22;" type="&#x22;(provider) -> str | None&#x22;">
      Resolve a plugin name from a provider metadata attribute.

      <PySourceCode>
        ```python
        def _resolve_plugin_name(provider: Any) -> str | None:
            """Resolve a plugin name from a provider metadata attribute."""
            metadata = getattr(provider, "metadata", None)
            if metadata is None:
                return None
            return getattr(metadata, "name", None)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;provider&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_hook_bus&#x22;" type="&#x22;() -> HookBus&#x22;">
      Return the global hook bus singleton.

      <PySourceCode>
        ```python
        def get_hook_bus() -> HookBus:
            """Return the global hook bus singleton."""
            return _GLOBAL_HOOK_BUS
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.bus.HookBus&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
