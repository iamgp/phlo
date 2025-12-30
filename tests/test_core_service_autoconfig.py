"""Integration tests for core service auto-configuration."""

from __future__ import annotations

import re
from typing import Iterable

import pytest
from phlo_dagster.plugin import DagsterServicePlugin
from phlo_minio.plugin import MinioServicePlugin
from phlo_nessie.plugin import NessieServicePlugin
from phlo_postgres.plugin import PostgresServicePlugin
from phlo_trino.plugin import TrinoServicePlugin

pytestmark = pytest.mark.integration

PLACEHOLDER_RE = re.compile(r"\$\{([A-Z0-9_]+)(?::-[^}]+)?\}")


class ServiceFixture:
    def __init__(self, name: str, definition: dict[str, object]):
        self.name = name
        self.definition = definition


CORE_SERVICES = {
    "postgres": ServiceFixture("postgres", PostgresServicePlugin().service_definition),
    "minio": ServiceFixture("minio", MinioServicePlugin().service_definition),
    "nessie": ServiceFixture("nessie", NessieServicePlugin().service_definition),
    "trino": ServiceFixture("trino", TrinoServicePlugin().service_definition),
    "dagster": ServiceFixture("dagster", DagsterServicePlugin().service_definition),
}


def _extract_placeholders(value: str) -> set[str]:
    return {match.group(1) for match in PLACEHOLDER_RE.finditer(value)}


def _collect_placeholders(values: Iterable[object]) -> set[str]:
    placeholders: set[str] = set()
    for item in values:
        if isinstance(item, str):
            placeholders.update(_extract_placeholders(item))
    return placeholders


def _collect_service_placeholders(definition: dict[str, object]) -> set[str]:
    placeholders: set[str] = set()

    image = definition.get("image")
    if isinstance(image, str):
        placeholders.update(_extract_placeholders(image))

    build = definition.get("build")
    if isinstance(build, dict):
        args = build.get("args")
        if isinstance(args, dict):
            placeholders.update(_collect_placeholders(args.values()))

    compose = definition.get("compose")
    if isinstance(compose, dict):
        environment = compose.get("environment")
        if isinstance(environment, dict):
            placeholders.update(_collect_placeholders(environment.values()))
        ports = compose.get("ports")
        if isinstance(ports, list):
            placeholders.update(_collect_placeholders(ports))

    return placeholders


def test_core_service_dependencies_are_declared() -> None:
    expected = {
        "dagster": {"postgres", "minio", "nessie", "trino"},
        "nessie": {"postgres", "minio"},
        "trino": {"nessie", "minio"},
        "postgres": set(),
        "minio": set(),
    }

    for name, fixture in CORE_SERVICES.items():
        depends_on = fixture.definition.get("depends_on", [])
        if isinstance(depends_on, list):
            assert set(depends_on) == expected[name]
        else:
            assert expected[name] == set()


def test_core_service_hooks_configured_for_auto_setup() -> None:
    dagster_hooks = CORE_SERVICES["dagster"].definition.get("hooks", {})
    assert isinstance(dagster_hooks, dict)
    post_start = dagster_hooks.get("post_start", [])
    assert isinstance(post_start, list)
    assert any(
        hook.get("name") == "dbt-compile" and hook.get("requires") == "phlo_dbt"
        for hook in post_start
        if isinstance(hook, dict)
    )

    nessie_hooks = CORE_SERVICES["nessie"].definition.get("hooks", {})
    assert isinstance(nessie_hooks, dict)
    post_start = nessie_hooks.get("post_start", [])
    assert isinstance(post_start, list)
    assert any(hook.get("name") == "init-branches" for hook in post_start if isinstance(hook, dict))


def test_core_service_placeholders_defined_in_env_vars() -> None:
    available_env = set()
    placeholders: set[str] = set()
    for fixture in CORE_SERVICES.values():
        env_vars = fixture.definition.get("env_vars", {})
        if isinstance(env_vars, dict):
            available_env.update(env_vars.keys())
        placeholders.update(_collect_service_placeholders(fixture.definition))

    allowed_extras = {"SUPERSET_ADMIN_PASSWORD"}
    missing = placeholders - available_env - allowed_extras
    assert not missing
