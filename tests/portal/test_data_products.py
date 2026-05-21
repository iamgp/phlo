from phlo.governance.catalog import GovernanceCatalog
from phlo.portal.products import build_data_products


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
