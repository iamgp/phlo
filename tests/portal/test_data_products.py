from phlo.governance.catalog import GovernanceCatalog
from phlo.portal.products import DataProduct, build_access_request, build_data_products


def test_build_data_products_from_governance_catalog() -> None:
    catalog = GovernanceCatalog.from_dict(
        {
            "version": 1,
            "datasets": [
                {
                    "id": "warehouse.customers",
                    "owner": "data-platform",
                    "description": "Customer dimension",
                    "classification": "restricted",
                    "tags": {"domain": "crm"},
                    "policies": ["allow_analyst_dataset_read"],
                }
            ],
        }
    )

    products = build_data_products(catalog=catalog, statuses={"warehouse.customers": "healthy"})

    assert products[0].id == "warehouse.customers"
    assert products[0].title == "warehouse.customers"
    assert products[0].owner == "data-platform"
    assert products[0].status == "healthy"
    assert products[0].certification == "uncertified"
    assert products[0].access_request["policy_ids"] == ["allow_analyst_dataset_read"]


def test_build_data_products_returns_deterministic_order() -> None:
    catalog = GovernanceCatalog.from_dict(
        {
            "version": 1,
            "datasets": [
                {"id": "z.table", "owner": "platform"},
                {"id": "a.table", "owner": "platform"},
            ],
        }
    )

    products = build_data_products(catalog=catalog)

    assert [product.id for product in products] == ["a.table", "z.table"]


def test_data_product_serialization_is_browser_safe() -> None:
    catalog = GovernanceCatalog.from_dict(
        {
            "version": 1,
            "datasets": [
                {
                    "id": "gold.revenue",
                    "owner": "finance",
                    "tags": {"certification": "certified", "domain": "finance"},
                }
            ],
        }
    )

    product = build_data_products(catalog=catalog)[0]

    assert product.to_read_model() == {
        "id": "gold.revenue",
        "title": "gold.revenue",
        "owner": "finance",
        "description": None,
        "domain": "finance",
        "classification": None,
        "certification": "certified",
        "status": "unknown",
        "tags": {"certification": "certified", "domain": "finance"},
        "access_request": {"dataset_id": "gold.revenue", "policy_ids": []},
    }


def test_data_product_access_request_policy_ids_are_isolated_between_serializations() -> None:
    catalog = GovernanceCatalog.from_dict(
        {
            "version": 1,
            "datasets": [
                {
                    "id": "gold.customers",
                    "owner": "crm",
                    "policies": ["original_policy"],
                }
            ],
        }
    )

    product = build_data_products(catalog=catalog)[0]
    payload = product.to_read_model()
    payload["access_request"]["policy_ids"].append("mutated")

    assert product.to_read_model()["access_request"]["policy_ids"] == ["original_policy"]


def test_data_product_nested_access_request_values_are_isolated_between_serializations() -> None:
    product = DataProduct(
        id="gold.customers",
        title="Gold customers",
        owner="crm",
        description=None,
        domain=None,
        classification=None,
        certification="uncertified",
        status="healthy",
        access_request={"dataset_id": "x", "approval": {"steps": ["owner"]}},
    )

    payload = product.to_read_model()
    payload["access_request"]["approval"]["steps"].append("security")

    assert product.to_read_model()["access_request"]["approval"]["steps"] == ["owner"]


def test_build_access_request_payload() -> None:
    payload = build_access_request(
        dataset_id="warehouse.customers",
        requester="alice@example.com",
        reason="Quarterly revenue analysis",
    )

    assert payload == {
        "dataset_id": "warehouse.customers",
        "requester": "alice@example.com",
        "reason": "Quarterly revenue analysis",
        "status": "pending",
    }
