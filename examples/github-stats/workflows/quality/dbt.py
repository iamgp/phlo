"""dbt-derived asset checks for GitHub example project.

This demonstrates the dbt quality check naming/metadata contract:
- Check name: dbt/<test_type>/<target>
- Metadata: source/partition_key/failed_count/total_count/query_or_sql/sample
"""

from __future__ import annotations

import os

import dagster as dg

from phlo.config import config
from phlo.defs.validation.dbt_validator import DBTValidatorResource
from phlo.quality.contract import QualityCheckContract, dbt_check_name


@dg.asset_check(
    name=dbt_check_name("generic", "fct_github_events"),
    asset=dg.AssetKey(["fct_github_events"]),
    blocking=True,
    description="Runs dbt tests for fct_github_events and reports results via the contract metadata.",
)
def dbt_generic_fct_github_events(
    context: dg.AssetCheckExecutionContext, dbt_validator: DBTValidatorResource
) -> dg.AssetCheckResult:
    branch_name = os.getenv("NESSIE_REF") or config.iceberg_nessie_ref
    results = dbt_validator.run_tests(branch_name=branch_name, select="fct_github_events")

    failures = results.get("failures") or []
    failed_count = int(results.get("failed") or 0)
    total_count = int(results.get("tests_run") or 0)

    contract = QualityCheckContract(
        source="dbt",
        partition_key=None,
        failed_count=failed_count,
        total_count=total_count,
        query_or_sql=f"dbt test --select fct_github_events (NESSIE_REF={branch_name})",
        sample=failures,
    )

    return dg.AssetCheckResult(
        passed=bool(results.get("all_passed")),
        metadata=contract.to_dagster_metadata(),
    )
