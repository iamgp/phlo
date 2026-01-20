from __future__ import annotations

from collections.abc import Iterable, Mapping

from phlo.plugins.discovery import ServiceDefinition


def select_services_to_install(
    *,
    all_services: Mapping[str, ServiceDefinition],
    default_services: Iterable[ServiceDefinition],
    enabled_names: Iterable[str],
    disabled_names: Iterable[str],
) -> list[ServiceDefinition]:
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
