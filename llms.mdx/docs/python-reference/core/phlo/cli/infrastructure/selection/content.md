# selection (/docs/python-reference/core/phlo/cli/infrastructure/selection)



<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;select_services_to_install&#x22;" type="&#x22;(*, all_services, default_services, enabled_names, disabled_names) -> list[ServiceDefinition]&#x22;">
      Resolve final service selection from defaults and CLI overrides.

      <PySourceCode>
        ```python
        def select_services_to_install(
            *,
            all_services: Mapping[str, ServiceDefinition],
            default_services: Iterable[ServiceDefinition],
            enabled_names: Iterable[str],
            disabled_names: Iterable[str],
        ) -> list[ServiceDefinition]:
            """Resolve final service selection from defaults and CLI overrides.

            Args:
                all_services: Mapping of all discovered services by name.
                default_services: Services enabled by default.
                enabled_names: Explicitly enabled service names.
                disabled_names: Explicitly disabled service names.

            Returns:
                Ordered list of services selected for installation.
            """
            disabled = set(disabled_names)
            services_to_install: list[ServiceDefinition] = [
                service for service in default_services if service.name not in disabled
            ]
            seen_names = {service.name for service in services_to_install}

            for name in enabled_names:
                service = all_services.get(name)
                if service is None or name in disabled or name in seen_names:
                    continue
                services_to_install.append(service)
                seen_names.add(name)

            for service in all_services.values():
                if service.profile and service.name not in disabled and service.name not in seen_names:
                    services_to_install.append(service)
                    seen_names.add(service.name)

            return services_to_install
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;all_services&#x22;" type="&#x22;Mapping[str, ServiceDefinition]&#x22;" value="undefined">
          Mapping of all discovered services by name.
        </PyParameter>

        <PyParameter name="&#x22;default_services&#x22;" type="&#x22;Iterable[ServiceDefinition]&#x22;" value="undefined">
          Services enabled by default.
        </PyParameter>

        <PyParameter name="&#x22;enabled_names&#x22;" type="&#x22;Iterable[str]&#x22;" value="undefined">
          Explicitly enabled service names.
        </PyParameter>

        <PyParameter name="&#x22;disabled_names&#x22;" type="&#x22;Iterable[str]&#x22;" value="undefined">
          Explicitly disabled service names.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Ordered list of services selected for installation.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
