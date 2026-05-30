from __future__ import annotations

from phlo_nessie.adapters.trino import (
    APACHE_ICEBERG_COMPATIBILITY_TARGET,
    validate_trino_iceberg_rest_catalog_properties,
)


def test_trino_rest_catalog_properties_are_compatible_with_iceberg_1_11() -> None:
    props = {
        "connector.name": "iceberg",
        "iceberg.catalog.type": "rest",
        "iceberg.rest-catalog.uri": "http://nessie:19120/iceberg",
        "iceberg.rest-catalog.warehouse": "warehouse",
        "iceberg.rest-catalog.prefix": "dev",
        "fs.native-s3.enabled": "true",
        "s3.endpoint": "http://minio:9000",
        "s3.path-style-access": "true",
        "s3.region": "us-east-1",
    }

    result = validate_trino_iceberg_rest_catalog_properties(props)

    assert APACHE_ICEBERG_COMPATIBILITY_TARGET == "1.11"
    assert result["compatible"] is True
    assert result["target"] == "apache-iceberg-1.11"
    assert result["checks"] == [
        "iceberg-connector",
        "rest-catalog-type",
        "nessie-iceberg-rest-uri",
        "trino-prefix-property",
        "warehouse-configured",
        "native-s3-enabled",
        "s3-path-style-access",
    ]
