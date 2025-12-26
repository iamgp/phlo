from __future__ import annotations

from collections.abc import Iterable, Mapping

from phlo.discovery import ServiceDefinition


def select_services_to_install(
    *,
    all_services: Mapping[str, ServiceDefinition],
    default_services: Iterable[ServiceDefinition],
    enabled_names: Iterable[str],
    disabled_names: Iterable[str],
) -> list[ServiceDefinition]:
    disabled = set(disabled_names)
    enabled = list(enabled_names)

    services_to_install: list[ServiceDefinition] = [
        service for service in default_services if service.name not in disabled
    ]

    for name in enabled:
        service = all_services.get(name)
        if service is None or name in disabled:
            continue
        if service not in services_to_install:
            services_to_install.append(service)

    for service in all_services.values():
        if service.profile and service.name not in disabled and service not in services_to_install:
            services_to_install.append(service)

    return services_to_install
