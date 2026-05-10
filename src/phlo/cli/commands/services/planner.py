"""Planning helpers for services lifecycle commands."""

from __future__ import annotations

from dataclasses import dataclass, field

import click

from phlo.cli.commands.services.utils import get_enabled_disabled_service_names
from phlo.plugins.discovery import ServiceDefinition
from phlo.utils import dedupe_preserve_order


@dataclass(frozen=True, slots=True)
class ServiceSelectionPlan:
    """Selected services for a services command."""

    selected_services: list[ServiceDefinition]
    disabled_names: set[str] = field(default_factory=set)
    requested_names: list[str] = field(default_factory=list)
    profiles: tuple[str, ...] = ()


def build_service_selection_plan(
    *,
    services: dict[str, ServiceDefinition],
    config: dict,
    profiles: tuple[str, ...],
    requested_names: list[str],
) -> ServiceSelectionPlan:
    unknown_requested = [name for name in requested_names if name not in services]
    if unknown_requested:
        raise click.ClickException(f"Unknown service name(s): {', '.join(unknown_requested)}")

    enabled_names, disabled_names = get_enabled_disabled_service_names(config)
    selected_names: list[str] = []
    if requested_names:
        selected_names.extend(requested_names)
    else:
        selected_names.extend(
            service.name
            for service in services.values()
            if service.default and service.name not in disabled_names
        )
        selected_names.extend(
            service.name
            for service in services.values()
            if service.profile in profiles and service.name not in disabled_names
        )
        selected_names.extend(name for name in enabled_names if name in services)

    selected = [
        services[name]
        for name in dedupe_preserve_order(selected_names)
        if name in services and name not in disabled_names
    ]
    return ServiceSelectionPlan(
        selected_services=selected,
        disabled_names=disabled_names,
        requested_names=requested_names,
        profiles=profiles,
    )
