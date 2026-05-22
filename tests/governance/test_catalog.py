from phlo.governance.catalog import GovernanceCatalog


def test_catalog_parses_governed_dataset_with_tags_and_masks() -> None:
    catalog = GovernanceCatalog.from_dict(
        {
            "version": 1,
            "datasets": [
                {
                    "id": "warehouse.customers",
                    "owner": "data-platform",
                    "description": "Customer dimension",
                    "tags": {"domain": "crm", "privacy": "restricted"},
                    "classification": "restricted",
                    "columns": {
                        "email": {"classification": "personal", "mask": "email"},
                        "region": {"classification": "internal"},
                    },
                    "row_filters": [
                        {
                            "name": "region_scope",
                            "expression": "region = current_setting('phlo.region')",
                            "applies_to_roles": ["regional_analyst"],
                        }
                    ],
                    "policies": ["allow_analyst_dataset_read"],
                }
            ],
        }
    )

    dataset = catalog.dataset("warehouse.customers")

    assert dataset.owner == "data-platform"
    assert dataset.tags["privacy"] == "restricted"
    assert dataset.columns["email"].mask == "email"
    assert dataset.row_filters[0].applies_to_roles == ("regional_analyst",)
    assert dataset.policies == ("allow_analyst_dataset_read",)


def test_catalog_rejects_duplicate_dataset_ids() -> None:
    try:
        GovernanceCatalog.from_dict(
            {
                "version": 1,
                "datasets": [
                    {"id": "warehouse.customers", "owner": "team-a"},
                    {"id": "warehouse.customers", "owner": "team-b"},
                ],
            }
        )
    except ValueError as exc:
        assert "Duplicate dataset id: warehouse.customers" in str(exc)
    else:
        raise AssertionError("Expected duplicate dataset id to fail")


def test_catalog_serializes_browser_safe_governance_view() -> None:
    catalog = GovernanceCatalog.from_dict(
        {
            "version": 1,
            "datasets": [
                {
                    "id": "warehouse.customers",
                    "owner": "data-platform",
                    "tags": {"privacy": "restricted"},
                    "columns": {"email": {"classification": "personal", "mask": "email"}},
                    "policies": ["allow_analyst_dataset_read"],
                }
            ],
        }
    )

    payload = catalog.to_read_model()

    assert payload == {
        "version": 1,
        "datasets": [
            {
                "id": "warehouse.customers",
                "owner": "data-platform",
                "description": None,
                "classification": None,
                "tags": {"privacy": "restricted"},
                "columns": [
                    {"name": "email", "classification": "personal", "mask": "email", "tags": {}}
                ],
                "row_filters": [],
                "policies": ["allow_analyst_dataset_read"],
            }
        ],
    }


def test_catalog_read_model_is_deterministic() -> None:
    catalog = GovernanceCatalog.from_dict(
        {
            "version": 1,
            "datasets": [
                {
                    "id": "z.table",
                    "owner": "platform",
                    "columns": {"z": {}, "a": {}},
                    "row_filters": [
                        {"name": "z_filter", "expression": "z = true"},
                        {"name": "a_filter", "expression": "a = true"},
                    ],
                },
                {"id": "a.table", "owner": "platform"},
            ],
        }
    )

    payload = catalog.to_read_model()

    assert [dataset["id"] for dataset in payload["datasets"]] == ["a.table", "z.table"]
    z_table = payload["datasets"][1]
    assert [column["name"] for column in z_table["columns"]] == ["a", "z"]
    assert [row_filter["name"] for row_filter in z_table["row_filters"]] == [
        "a_filter",
        "z_filter",
    ]
