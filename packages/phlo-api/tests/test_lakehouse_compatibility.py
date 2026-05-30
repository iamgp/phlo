from __future__ import annotations

import pytest

from phlo_api.observatory_api.iceberg import get_compatibility


@pytest.mark.anyio
async def test_observatory_reports_iceberg_1_11_lakehouse_compatibility() -> None:
    compatibility = await get_compatibility()

    assert compatibility.target == "apache-iceberg-1.11"
    assert compatibility.rest_catalog["type"] == "rest"
    assert compatibility.rest_catalog["pyiceberg_ref_strategy"] == "uri-path"
    assert compatibility.rest_catalog["trino_ref_strategy"] == "rest-catalog-prefix"
    assert compatibility.engines["trino"]["catalog_type"] == "rest"
    assert compatibility.engines["trino"]["iceberg_table_spec_versions"] == [1, 2]
