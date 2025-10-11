from __future__ import annotations

import os

import dagster as dg
from dagster_airbyte import AirbyteResource
from dagster_dbt import DbtCliResource


def _build_airbyte_resource() -> AirbyteResource:
    airbyte_host = os.getenv("AIRBYTE_HOST", "airbyte-server")
    airbyte_port = os.getenv("AIRBYTE_API_PORT", "8001")
    return AirbyteResource(host=airbyte_host, port=airbyte_port)


def _build_dbt_resource() -> DbtCliResource:
    return DbtCliResource(
        project_dir="/dbt",
        profiles_dir="/dbt/profiles",
    )


def build_defs() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "airbyte": _build_airbyte_resource(),
            "dbt": _build_dbt_resource(),
        }
    )
