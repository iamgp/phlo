# resolver (/docs/python-reference/core/phlo/capabilities/resolver)



Capability resolver for runtime provider selection.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ResolutionResult&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/resolver/ResolutionResult&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;list_capabilities&#x22;" type="&#x22;(capability_type, *, registry=None) -> list[str]&#x22;">
      List registered capability names for a given capability type.

      <PySourceCode>
        ```python
        def list_capabilities(
            capability_type: str,
            *,
            registry: CapabilityRegistry | None = None,
        ) -> list[str]:
            """List registered capability names for a given capability type."""
            registry = registry or get_capability_registry()
            list_method = _CAPABILITY_LISTERS.get(capability_type)
            if not list_method:
                logger.debug("capability_list_unknown_type", capability_type=capability_type)
                return []
            specs = getattr(registry, list_method)()
            logger.debug(
                "capability_listed",
                capability_type=capability_type,
                capability_count=len(specs),
            )
            return [spec.name for spec in specs]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;capability_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;registry&#x22;" type="&#x22;CapabilityRegistry | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;resolve_capability&#x22;" type="&#x22;(capability_type, name=None, *, runtime=None, registry=None) -> ResolutionResult | None&#x22;">
      Resolve a capability provider by type and optional name.

      If `name` is omitted and exactly one provider is installed, resolve it.
      Otherwise return `None` so callers can surface deterministic guidance.

      <PySourceCode>
        ```python
        def resolve_capability(
            capability_type: str,
            name: str | None = None,
            *,
            runtime: RuntimeContext | None = None,
            registry: CapabilityRegistry | None = None,
        ) -> ResolutionResult | None:
            """Resolve a capability provider by type and optional name.

            If ``name`` is omitted and exactly one provider is installed, resolve it.
            Otherwise return ``None`` so callers can surface deterministic guidance.
            """
            registry = registry or get_capability_registry()
            list_method = _CAPABILITY_LISTERS.get(capability_type)
            if not list_method:
                logger.debug(
                    "capability_resolution_unknown_type",
                    capability_type=capability_type,
                    requested_name=name,
                )
                return None

            requested_name = name or configured_capability_name(capability_type, runtime=runtime)
            specs = getattr(registry, list_method)()
            if requested_name is not None:
                for spec in specs:
                    if spec.name == requested_name:
                        logger.debug(
                            "capability_resolved",
                            capability_type=capability_type,
                            capability_name=spec.name,
                        )
                        return ResolutionResult(
                            capability_type=capability_type,
                            name=spec.name,
                            provider=spec.provider,
                            metadata=spec.metadata,
                            support=spec.support,
                        )
                logger.debug(
                    "capability_resolution_name_not_found",
                    capability_type=capability_type,
                    requested_name=requested_name,
                    available_names=[spec.name for spec in specs],
                )
                return None

            if len(specs) != 1:
                logger.debug(
                    "capability_resolution_ambiguous",
                    capability_type=capability_type,
                    candidate_count=len(specs),
                    candidate_names=[spec.name for spec in specs],
                )
                return None
            spec = specs[0]
            logger.debug(
                "capability_resolved_default",
                capability_type=capability_type,
                capability_name=spec.name,
            )
            return ResolutionResult(
                capability_type=capability_type,
                name=spec.name,
                provider=spec.provider,
                metadata=spec.metadata,
                support=spec.support,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;capability_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;registry&#x22;" type="&#x22;CapabilityRegistry | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.resolver.ResolutionResult | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;configured_capability_name&#x22;" type="&#x22;(capability_type, *, runtime=None) -> str | None&#x22;">
      Return the configured provider name for a capability type, if any.

      <PySourceCode>
        ```python
        def configured_capability_name(
            capability_type: str,
            *,
            runtime: RuntimeContext | None = None,
        ) -> str | None:
            """Return the configured provider name for a capability type, if any."""
            if runtime is not None:
                routing = routing_from_context(runtime)
                override = routing.capability_overrides.get(capability_type)
                if override:
                    return override
            env_override = get_settings().phlo_default_capabilities.get(capability_type)
            if env_override:
                return env_override
            return get_capability_defaults_from_config().get(capability_type)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;capability_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;missing_required_capabilities&#x22;" type="&#x22;(plugin, *, registry=None) -> list[str]&#x22;">
      Return capability requirements that are currently unsatisfied.

      <PySourceCode>
        ```python
        def missing_required_capabilities(
            plugin: PluginMetadata,
            *,
            registry: CapabilityRegistry | None = None,
        ) -> list[str]:
            """Return capability requirements that are currently unsatisfied."""
            registry = registry or get_capability_registry()
            missing: list[str] = []

            for capability in plugin.requires_capabilities:
                if ":" in capability:
                    capability_type, expected_name = capability.split(":", 1)
                    if resolve_capability(capability_type, expected_name, registry=registry) is None:
                        missing.append(capability)
                    continue

                if not list_capabilities(capability, registry=registry):
                    missing.append(capability)

            if missing:
                logger.debug(
                    "plugin_required_capabilities_missing",
                    plugin_name=plugin.name,
                    missing_capabilities=missing,
                )
            return missing
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin&#x22;" type="&#x22;PluginMetadata&#x22;" value="null" />

        <PyParameter name="&#x22;registry&#x22;" type="&#x22;CapabilityRegistry | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
