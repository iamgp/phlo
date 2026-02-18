"""Settings for phlo-dlt package."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


class DltSettings(BaseConfig):
    """Configuration for DLT ingestion defaults."""

    dlt_default_namespace: str = Field(
        default="raw",
        validation_alias=AliasChoices(
            "DLT_DEFAULT_NAMESPACE",
            "PHLO_DLT_DEFAULT_NAMESPACE",
            "ICEBERG_DEFAULT_NAMESPACE",
            "PHLO_ICEBERG_DEFAULT_NAMESPACE",
        ),
        description="Default namespace/schema used for generated ingestion table names.",
    )


@lru_cache(maxsize=1)
def get_settings() -> DltSettings:
    """Return cached DLT settings instance."""
    return DltSettings()
