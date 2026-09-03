"""PyIceberg REST catalog configuration for Polaris.

Both dlt ingestion and snapshot promotion configure PyIceberg identically:
the writer principal authenticates against Polaris's OAuth2 token endpoint
and reads S3 credentials from the environment (production deployments should
prefer Polaris credential vending over static keys).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from phlo_polaris.settings import get_settings


def _pyiceberg_catalog_config() -> dict[str, Any]:
    settings = get_settings()
    return {
        "type": "rest",
        "uri": settings.polaris_rest_catalog_uri(),
        "warehouse": settings.polaris_catalog,
        "credential": settings.writer_credential(),
        "oauth2-server-uri": settings.oauth_token_uri(),
        "s3.endpoint": os.environ.get("ICEBERG_S3_ENDPOINT", "http://minio:9000/"),
        "s3.access-key-id": os.environ.get("ICEBERG_S3_ACCESS_KEY", "minio"),
        "s3.secret-access-key": os.environ.get("ICEBERG_S3_SECRET_KEY", "minio123"),
        "s3.path-style-access": "true",
        "s3.region": os.environ.get("ICEBERG_S3_REGION", "us-east-1"),
    }


@lru_cache(maxsize=4)
def load_pyiceberg_catalog():
    """Load the Polaris-backed PyIceberg REST catalog."""
    from pyiceberg.catalog import load_catalog

    config = _pyiceberg_catalog_config()
    return load_catalog(name=f"polaris_{config['warehouse']}", **config)
