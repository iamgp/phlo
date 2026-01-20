"""dbt settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field

from phlo.config.base import BaseConfig


class DbtSettings(BaseConfig):
    """dbt project configuration."""

    dbt_project_dir: str = Field(
        default="workflows/transforms/dbt",
        description="Path to dbt project directory",
    )
    dbt_manifest_path: str = Field(
        default="",
        description="Path to dbt manifest.json after running dbt docs generate",
    )
    dbt_catalog_path: str = Field(
        default="",
        description="Path to dbt catalog.json for column-level documentation",
    )

    def model_post_init(self, __context: object) -> None:
        if not self.dbt_manifest_path:
            object.__setattr__(
                self, "dbt_manifest_path", f"{self.dbt_project_dir}/target/manifest.json"
            )
        if not self.dbt_catalog_path:
            object.__setattr__(
                self, "dbt_catalog_path", f"{self.dbt_project_dir}/target/catalog.json"
            )

    @computed_field
    @property
    def dbt_profiles_dir(self) -> str:
        return f"{self.dbt_project_dir}/profiles"

    @property
    def dbt_project_path(self) -> Path:
        return Path(self.dbt_project_dir)

    @property
    def dbt_profiles_path(self) -> Path:
        return Path(self.dbt_profiles_dir)


@lru_cache(maxsize=1)
def get_settings() -> DbtSettings:
    return DbtSettings()
