from __future__ import annotations

from dataclasses import dataclass

from phlo.capabilities.catalog import CapabilityFamily


@dataclass(frozen=True)
class DummySpec:
    name: str
    value: int


def test_capability_family_registers_and_lists_snapshot() -> None:
    family = CapabilityFamily[DummySpec, str](key=lambda spec: spec.name)

    family.register(DummySpec(name="trino", value=1))
    listed = family.list()
    listed.append(DummySpec(name="duckdb", value=2))

    assert family.list() == [DummySpec(name="trino", value=1)]


def test_capability_family_replaces_same_key() -> None:
    family = CapabilityFamily[DummySpec, str](key=lambda spec: spec.name)

    family.register(DummySpec(name="trino", value=1))
    family.register(DummySpec(name="trino", value=2))

    assert family.list() == [DummySpec(name="trino", value=2)]
