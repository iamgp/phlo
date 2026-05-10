"""Tests for extracted Observatory v2 read models."""

from __future__ import annotations

from phlo_api.observatory_api.v2_cache import ReadModelCache
from phlo_api.observatory_api.v2_services import (
    docker_status_from_container,
    service_name_from_container,
)


def test_read_model_cache_returns_cached_value_before_ttl() -> None:
    cache = ReadModelCache(project_key=lambda: "demo")
    calls: list[str] = []

    first = cache.cached("services", 30, lambda: calls.append("called") or ["postgres"])
    second = cache.cached("services", 30, lambda: calls.append("called") or ["trino"])

    assert first == ["postgres"]
    assert second == ["postgres"]
    assert calls == ["called"]


def test_read_model_cache_clear_removes_values() -> None:
    cache = ReadModelCache(project_key=lambda: "demo")
    cache.cached("services", 30, lambda: ["postgres"])

    cache.clear()
    value = cache.cached("services", 30, lambda: ["trino"])

    assert value == ["trino"]


def test_docker_status_from_running_container() -> None:
    status, health = docker_status_from_container(
        {"State": "running", "Status": "Up 10 seconds"}
    )

    assert status == "running"
    assert health.state == "unknown"


def test_service_name_from_container_matches_known_service_id() -> None:
    assert service_name_from_container("demo-postgres-1", {"postgres"}) == "postgres"
