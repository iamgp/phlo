"""Postgres service plugin package."""

from phlo_postgres.plugin import PostgresServicePlugin
from phlo_postgres.publish_target import PostgresPublishTarget
from phlo_postgres.resource import PostgresResource
from phlo_postgres.settings import PostgresSettings, get_settings

__all__ = [
    "PostgresPublishTarget",
    "PostgresResource",
    "PostgresServicePlugin",
    "PostgresSettings",
    "get_settings",
]
__version__ = "0.1.0"
