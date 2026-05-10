from __future__ import annotations

import click
import pytest

from phlo.cli.commands.services.planner import build_service_selection_plan
from phlo.plugins.discovery import ServiceDefinition


def _service(
    name: str,
    *,
    default: bool = False,
    profile: str | None = None,
) -> ServiceDefinition:
    return ServiceDefinition.from_dict(
        {"name": name, "image": f"{name}:latest", "default": default, "profile": profile},
        None,
    )


def test_selection_plan_includes_default_and_profile_services() -> None:
    services = {
        "postgres": _service("postgres", default=True),
        "grafana": _service("grafana", profile="observability"),
        "hasura": _service("hasura", profile="api"),
    }

    plan = build_service_selection_plan(
        services=services,
        config={},
        profiles=("observability",),
        requested_names=[],
    )

    assert [service.name for service in plan.selected_services] == ["postgres", "grafana"]
    assert plan.disabled_names == set()


def test_selection_plan_excludes_disabled_services() -> None:
    services = {
        "postgres": _service("postgres", default=True),
        "grafana": _service("grafana", default=True),
    }

    plan = build_service_selection_plan(
        services=services,
        config={"services": {"grafana": {"enabled": False}}},
        profiles=(),
        requested_names=[],
    )

    assert [service.name for service in plan.selected_services] == ["postgres"]
    assert plan.disabled_names == {"grafana"}


def test_selection_plan_rejects_unknown_requested_service() -> None:
    services = {"postgres": _service("postgres", default=True)}

    with pytest.raises(click.ClickException) as exc:
        build_service_selection_plan(
            services=services,
            config={},
            profiles=(),
            requested_names=["missing"],
        )

    assert str(exc.value) == "Unknown service name(s): missing"
