# runtime (/docs/python-reference/core/phlo/capabilities/runtime)



Runtime context protocol and helpers for capability execution.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;RuntimeRouting&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/runtime/RuntimeRouting&#x22;" />

      <Card title="&#x22;RuntimeContext&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/runtime/RuntimeContext&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;capability_overrides_from_tags&#x22;" type="&#x22;(tags) -> dict[str, str]&#x22;">
      Extract capability overrides from canonical runtime tags.

      <PySourceCode>
        ```python
        def capability_overrides_from_tags(tags: Mapping[str, str]) -> dict[str, str]:
            """Extract capability overrides from canonical runtime tags."""
            overrides: dict[str, str] = {}
            for key, value in tags.items():
                if not value:
                    continue
                if key.startswith("phlo/capability/"):
                    capability_type = key.removeprefix("phlo/capability/")
                elif key.startswith("capability/"):
                    capability_type = key.removeprefix("capability/")
                else:
                    continue
                capability_type = capability_type.strip()
                if capability_type:
                    overrides[capability_type] = value
            return overrides
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;tags&#x22;" type="&#x22;Mapping[str, str]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;routing_from_context&#x22;" type="&#x22;(context) -> RuntimeRouting&#x22;">
      Build canonical routing data from a runtime context.

      This helper keeps the initial migration path lightweight for existing
      contexts that expose only tags, resources, and the standard protocol
      fields.

      <PySourceCode>
        ```python
        def routing_from_context(context: RuntimeContext) -> RuntimeRouting:
            """Build canonical routing data from a runtime context.

            This helper keeps the initial migration path lightweight for existing
            contexts that expose only tags, resources, and the standard protocol
            fields.
            """
            direct_routing = getattr(context, "routing", None)
            if isinstance(direct_routing, RuntimeRouting):
                return direct_routing

            resources_value = getattr(context, "resources", {})
            resources = dict(resources_value) if isinstance(resources_value, Mapping) else {}

            tags_value = getattr(context, "tags", {})
            tags = (
                {str(key): str(value) for key, value in tags_value.items()}
                if isinstance(tags_value, Mapping)
                else {}
            )
            feature_flags = {
                key.removeprefix("feature/"): value
                for key, value in tags.items()
                if key.startswith("feature/")
            }
            capability_overrides = capability_overrides_from_tags(tags)
            environment = tags.get("environment") or tags.get("env")
            ref = tags.get("phlo/ref") or tags.get("ref") or tags.get("branch")

            return RuntimeRouting(
                environment=environment,
                ref=ref,
                partition_key=getattr(context, "partition_key", None),
                run_id=getattr(context, "run_id", None),
                resources=resources,
                feature_flags=feature_flags,
                capability_overrides=capability_overrides,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.runtime.RuntimeRouting&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;resolve_runtime_ref&#x22;" type="&#x22;(context, *, support=None, default_ref=None) -> str | None&#x22;">
      Resolve the effective ref for a capability from runtime routing and support metadata.

      <PySourceCode>
        ```python
        def resolve_runtime_ref(
            context: RuntimeContext | None,
            *,
            support: CapabilitySupport | None = None,
            default_ref: str | None = None,
        ) -> str | None:
            """Resolve the effective ref for a capability from runtime routing and support metadata.

            Args:
                context: Runtime context or ``None`` when no orchestrator context exists.
                support: Capability support metadata. When refs are unsupported, routing refs are ignored.
                default_ref: Fallback ref used when the capability supports refs but the runtime omitted one.

            Returns:
                Effective ref name for the capability, or ``None`` when refs are unsupported.
            """
            if support is not None and not support.supports_refs:
                return None
            if context is not None:
                routing = routing_from_context(context)
                if routing.ref:
                    return routing.ref
            return default_ref
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
          Runtime context or `None` when no orchestrator context exists.
        </PyParameter>

        <PyParameter name="&#x22;support&#x22;" type="&#x22;CapabilitySupport | None&#x22;" value="&#x22;None&#x22;">
          Capability support metadata. When refs are unsupported, routing refs are ignored.
        </PyParameter>

        <PyParameter name="&#x22;default_ref&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Fallback ref used when the capability supports refs but the runtime omitted one.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        Effective ref name for the capability, or `None` when refs are unsupported.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
