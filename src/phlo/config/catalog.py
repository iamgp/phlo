from pydantic import Field

from phlo.config.base import BaseConfig


class CatalogConfig(BaseConfig):
    """Nessie Git-like catalog and Iceberg table management configuration."""

    nessie_version: str = Field(default="0.106.0", description="Nessie version")
    nessie_port: int = Field(default=19120, description="Nessie REST API port")
    nessie_host: str = Field(default="nessie", description="Nessie service hostname")
    nessie_api_version: str = Field(default="v1", description="Nessie API version")

    iceberg_warehouse_path: str = Field(
        default="s3://lake/warehouse", description="S3 path for Iceberg warehouse"
    )
    iceberg_staging_path: str = Field(
        default="s3://lake/stage", description="S3 path for staging parquet files"
    )
    iceberg_default_namespace: str = Field(
        default="raw", description="Default namespace/schema for Iceberg tables"
    )
    iceberg_nessie_ref: str = Field(
        default="main", description="Default Nessie branch/tag for Iceberg operations"
    )

    branch_retention_days: int = Field(
        default=7, description="Days to retain pipeline branches after successful merge"
    )
    branch_retention_days_failed: int = Field(
        default=14,
        description="Days to retain pipeline branches that failed validation",
    )
    auto_promote_enabled: bool = Field(
        default=True,
        description="Enable automatic promotion to main after validation passes",
    )
    branch_cleanup_enabled: bool = Field(
        default=False,
        description="Enable automatic branch cleanup (set True in production)",
    )

    freshness_blocks_promotion: bool = Field(
        default=False,
        description="Whether freshness policy failures should block promotion to main",
    )
    pandera_critical_level: str = Field(
        default="error",
        description="Pandera check severity that blocks promotion (error|warning|info)",
    )

    validation_retry_enabled: bool = Field(
        default=True, description="Enable automatic retry of failed validations"
    )
    validation_retry_max_attempts: int = Field(
        default=3, description="Maximum number of validation retry attempts"
    )
    validation_retry_delay_seconds: int = Field(
        default=300, description="Delay between validation retry attempts (seconds)"
    )

    @property
    def nessie_uri(self) -> str:
        """Return Nessie REST API URI for Iceberg catalog (base URL)."""
        return f"http://{self.nessie_host}:{self.nessie_port}/api"

    @property
    def nessie_api_v1_uri(self) -> str:
        """Return Nessie API v1 URI for direct API calls."""
        return f"http://{self.nessie_host}:{self.nessie_port}/api/v1"

    @property
    def nessie_iceberg_rest_uri(self) -> str:
        """
        Return Nessie REST catalog URI for Iceberg (without branch).

        The branch/tag is specified via the 'prefix' parameter when configuring
        the catalog, matching how Trino's iceberg.rest-catalog.prefix works.
        """
        return f"http://{self.nessie_host}:{self.nessie_port}/iceberg"

    def get_iceberg_warehouse_for_branch(self, branch: str = "main") -> str:
        """
        Get the S3 warehouse path for a specific Nessie branch.

        Args:
            branch: Nessie branch name (default: main)

        Returns:
            S3 warehouse path for the branch

        Note:
            Nessie manages branch isolation internally via the prefix parameter.
            All branches share the same physical warehouse location.
        """
        return self.iceberg_warehouse_path
