from __future__ import annotations

from collections.abc import Iterator

import pytest

import phlo
from phlo.governance import build_governance_surface

pytestmark = pytest.mark.core_regression


@pytest.fixture(autouse=True)
def _clear_flow_declarations() -> Iterator[None]:
    phlo.clear_flow_declarations()
    yield
    phlo.clear_flow_declarations()


def test_surface_derives_complete_dataset_from_existing_declarations() -> None:
    @phlo.contract(
        table="gold.customer_health",
        owner="data-platform",
        consumers=["cs", phlo.Consumer(name="sales", contact="sales@example.com")],
        pii=True,
        freshness_hours=6,
        lifecycle="production",
    )
    def customer_health_contract() -> None:
        return None

    @phlo.publish(
        table="gold.customer_health",
        audience=["cs", "sales"],
        owner="data-platform",
        freshness_hours=6,
    )
    def publish_customer_health() -> None:
        return None

    @phlo.access(
        table="gold.customer_health",
        roles=["cs_read", "sales_read"],
        pii_columns=["email"],
        policy="read",
    )
    def customer_health_access() -> None:
        return None

    @phlo.observe(table="gold.customer_health", freshness_hours=6)
    def customer_health_observe() -> None:
        return None

    surface = build_governance_surface()

    assert surface.warning_count == 0
    assert surface.dataset("gold.customer_health").to_read_model() == {
        "id": "gold.customer_health",
        "owner": "data-platform",
        "lifecycle": "production",
        "pii": True,
        "published": True,
        "audience": ["cs", "sales"],
        "consumers": [
            {"name": "cs", "contact": None, "usage": None},
            {"name": "sales", "contact": "sales@example.com", "usage": None},
        ],
        "sla": {
            "freshness_hours": 6,
            "quality_threshold": 1.0,
            "max_failures": None,
            "notify": None,
        },
        "access_policies": [
            {
                "key": "access_gold_customer_health",
                "roles": ["cs_read", "sales_read"],
                "pii_columns": ["email"],
                "policy": "read",
                "metadata": {},
            }
        ],
        "observability": {
            "freshness_hours": 6,
            "row_count_change": {},
            "checks": ["freshness_hours"],
        },
        "warnings": [],
    }


def test_surface_warns_when_published_dataset_is_not_governed() -> None:
    @phlo.publish(table="gold.customer_health", audience=["sales"])
    def publish_customer_health() -> None:
        return None

    surface = build_governance_surface()

    assert [warning.code for warning in surface.warnings] == [
        "missing_owner",
        "missing_access_policy",
    ]
    assert surface.to_check_result()["ok"] is False


def test_surface_warns_when_pii_contract_has_no_pii_column_policy() -> None:
    @phlo.contract(
        table="gold.customer_health",
        owner="data-platform",
        pii=True,
        freshness_hours=6,
        lifecycle="production",
    )
    def customer_health_contract() -> None:
        return None

    @phlo.publish(table="gold.customer_health", owner="data-platform")
    def publish_customer_health() -> None:
        return None

    @phlo.access(table="gold.customer_health", roles=["sales_read"])
    def customer_health_access() -> None:
        return None

    surface = build_governance_surface()

    assert [warning.code for warning in surface.warnings] == ["missing_pii_column_policy"]


def test_surface_warns_for_access_policy_without_dataset_declaration() -> None:
    @phlo.access(table="gold.orphaned", roles=["analyst"])
    def orphaned_access() -> None:
        return None

    surface = build_governance_surface()

    assert surface.dataset("gold.orphaned").published is False
    assert [warning.code for warning in surface.warnings] == ["access_policy_without_dataset"]


def test_surface_read_model_is_deterministic() -> None:
    @phlo.publish(table="z.table", owner="team-z")
    def publish_z() -> None:
        return None

    @phlo.publish(table="a.table", owner="team-a")
    def publish_a() -> None:
        return None

    surface = build_governance_surface()

    assert [dataset["id"] for dataset in surface.to_read_model()["datasets"]] == [
        "a.table",
        "z.table",
    ]
