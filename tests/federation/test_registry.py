from phlo.federation.registry import FederationRegistry


def test_registry_parses_connections_and_datasets() -> None:
    registry = FederationRegistry.from_dict(
        {
            "version": 1,
            "connections": [
                {
                    "id": "crm",
                    "type": "postgres",
                    "jdbc_url": "jdbc:postgresql://crm.example.com:5432/app",
                    "secret_ref": "secret/data/crm",
                }
            ],
            "datasets": [
                {
                    "id": "crm.public.accounts",
                    "connection_id": "crm",
                    "remote_name": "public.accounts",
                    "mode": "query",
                }
            ],
        }
    )

    connection = registry.connections["crm"]
    dataset = registry.datasets["crm.public.accounts"]

    assert registry.version == 1
    assert connection.type == "postgres"
    assert connection.jdbc_url == "jdbc:postgresql://crm.example.com:5432/app"
    assert connection.secret_ref == "secret/data/crm"
    assert dataset.connection_id == "crm"
    assert dataset.remote_name == "public.accounts"
    assert dataset.mode == "query"


def test_registry_rejects_unknown_connection() -> None:
    try:
        FederationRegistry.from_dict(
            {
                "version": 1,
                "connections": [],
                "datasets": [
                    {
                        "id": "crm.public.accounts",
                        "connection_id": "missing",
                        "remote_name": "public.accounts",
                    }
                ],
            }
        )
    except ValueError as exc:
        assert (
            str(exc) == "Foreign dataset crm.public.accounts references unknown connection missing"
        )
    else:
        raise AssertionError("Expected unknown connection to fail")


def test_registry_rejects_duplicate_connection_ids() -> None:
    try:
        FederationRegistry.from_dict(
            {
                "version": 1,
                "connections": [
                    {
                        "id": "crm-postgres",
                        "type": "postgres",
                        "jdbc_url": "jdbc:postgresql://primary.example.com:5432/app",
                        "secret_ref": "secret/data/crm-primary",
                    },
                    {
                        "id": "crm-postgres",
                        "type": "postgres",
                        "jdbc_url": "jdbc:postgresql://replica.example.com:5432/app",
                        "secret_ref": "secret/data/crm-replica",
                    },
                ],
                "datasets": [],
            }
        )
    except ValueError as exc:
        assert str(exc) == "Duplicate federation connection id: crm-postgres"
    else:
        raise AssertionError("Expected duplicate connection id to fail")


def test_registry_rejects_duplicate_dataset_ids() -> None:
    try:
        FederationRegistry.from_dict(
            {
                "version": 1,
                "connections": [
                    {
                        "id": "crm",
                        "type": "postgres",
                        "jdbc_url": "jdbc:postgresql://crm.example.com:5432/app",
                        "secret_ref": "secret/data/crm",
                    }
                ],
                "datasets": [
                    {
                        "id": "crm.public.accounts",
                        "connection_id": "crm",
                        "remote_name": "public.accounts",
                    },
                    {
                        "id": "crm.public.accounts",
                        "connection_id": "crm",
                        "remote_name": "public.accounts_archive",
                    },
                ],
            }
        )
    except ValueError as exc:
        assert str(exc) == "Duplicate foreign dataset id: crm.public.accounts"
    else:
        raise AssertionError("Expected duplicate dataset id to fail")


def test_registry_read_model_redacts_connection_details() -> None:
    registry = FederationRegistry.from_dict(
        {
            "version": 1,
            "connections": [
                {
                    "id": "crm",
                    "type": "postgres",
                    "jdbc_url": "jdbc:postgresql://crm.example.com:5432/app",
                    "secret_ref": "secret/data/crm",
                }
            ],
            "datasets": [
                {
                    "id": "crm.public.accounts",
                    "connection_id": "crm",
                    "remote_name": "public.accounts",
                }
            ],
        }
    )

    payload = registry.to_read_model()

    assert payload == {
        "version": 1,
        "connections": [{"id": "crm", "type": "postgres"}],
        "datasets": [
            {
                "id": "crm.public.accounts",
                "connection_id": "crm",
                "remote_name": "public.accounts",
                "mode": "query",
            }
        ],
    }


def test_registry_read_model_is_deterministic() -> None:
    registry = FederationRegistry.from_dict(
        {
            "version": 1,
            "connections": [
                {
                    "id": "z",
                    "type": "postgres",
                    "jdbc_url": "jdbc:postgresql://z.example.com:5432/app",
                    "secret_ref": "secret/data/z",
                },
                {
                    "id": "a",
                    "type": "postgres",
                    "jdbc_url": "jdbc:postgresql://a.example.com:5432/app",
                    "secret_ref": "secret/data/a",
                },
            ],
            "datasets": [
                {"id": "z.remote", "connection_id": "z", "remote_name": "public.z"},
                {"id": "a.remote", "connection_id": "a", "remote_name": "public.a"},
            ],
        }
    )

    payload = registry.to_read_model()

    assert [connection["id"] for connection in payload["connections"]] == ["a", "z"]
    assert [dataset["id"] for dataset in payload["datasets"]] == ["a.remote", "z.remote"]
