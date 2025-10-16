from __future__ import annotations

from dataclasses import replace
from typing import Any

import duckdb
from dlt.common.destination import DestinationCapabilitiesContext
from dlt.destinations.impl.duckdb.configuration import DuckDbClientConfiguration
from dlt.destinations.impl.duckdb.duck import (
    HINT_TO_POSTGRES_ATTR,
    DuckDbClient,
)
from dlt.destinations.impl.duckdb.factory import duckdb as DuckDbFactory
from dlt.destinations.impl.duckdb.sql_client import DuckDbSqlClient

from cascade.ducklake import (
    DuckLakeRuntimeConfig,
    build_ducklake_runtime_config,
    configure_ducklake_connection,
)


class DuckLakeSqlClient(DuckDbSqlClient):
    """DuckDB SQL client that eagerly attaches DuckLake on connection open."""

    def __init__(
        self,
        dataset_name: str,
        staging_dataset_name: str,
        credentials: Any,
        capabilities: DestinationCapabilitiesContext,
        runtime: DuckLakeRuntimeConfig,
    ) -> None:
        super().__init__(dataset_name, staging_dataset_name, credentials, capabilities)
        self._runtime = runtime

    def open_connection(self):
        conn = super().open_connection()
        configure_ducklake_connection(
            conn,
            runtime=self._runtime,
            ensure_schemas={self.dataset_name, self.staging_dataset_name},
            read_only=self.credentials.read_only,
        )
        return conn


class DuckLakeClient(DuckDbClient):
    """DuckDB destination client extended to bootstrap DuckLake connections."""

    runtime_config: DuckLakeRuntimeConfig | None = None

    def __init__(
        self,
        schema,
        config: DuckDbClientConfiguration,
        capabilities: DestinationCapabilitiesContext,
    ) -> None:
        super().__init__(schema, config, capabilities)

        runtime_base = self.runtime_config or build_ducklake_runtime_config()
        runtime = replace(
            runtime_base,
            default_dataset=self.sql_client.dataset_name,
            staging_dataset=self.sql_client.staging_dataset_name,
        )
        self.runtime_config = runtime

        self.sql_client = DuckLakeSqlClient(
            self.sql_client.dataset_name,
            self.sql_client.staging_dataset_name,
            config.credentials,
            capabilities,
            runtime,
        )
        self.active_hints = HINT_TO_POSTGRES_ATTR if self.config.create_indexes else {}
        self.type_mapper = self.capabilities.get_type_mapper()


class DuckLake(DuckDbFactory):
    """DLT destination factory wiring DuckLake-specific client."""

    def __init__(
        self,
        credentials: Any = None,
        create_indexes: bool = False,
        destination_name: str | None = None,
        environment: str | None = None,
        runtime_config: DuckLakeRuntimeConfig | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        super().__init__(
            credentials=credentials,
            create_indexes=create_indexes,
            destination_name=destination_name,
            environment=environment,
            **kwargs,
        )
        self._runtime_config = runtime_config or build_ducklake_runtime_config()
        DuckLakeClient.runtime_config = self._runtime_config

    @property
    def client_class(self):
        DuckLakeClient.runtime_config = self._runtime_config
        return DuckLakeClient


def build_destination(
    *args: Any,
    runtime_config: DuckLakeRuntimeConfig | None = None,
    **kwargs: Any,
) -> DuckLake:
    """
    Convenience helper returning a DuckLake destination for DLT pipelines.
    
    Uses /dbt/dbt.db file so DLT and dbt share the same DuckDB connection
    and both write to the attached DuckLake catalog.
    """
    kwargs["credentials"] = duckdb.connect(database="/dbt/dbt.db")
    return DuckLake(*args, runtime_config=runtime_config, **kwargs)
