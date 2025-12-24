"""dbt-derived asset checks for GitHub example project.

This demonstrates the dbt quality check naming/metadata contract:
- Check name: dbt/<test_type>/<target>
- Metadata: source/partition_key/failed_count/total_count/query_or_sql/sample
"""

import os

from dagster import AssetCheckExecutionContext, AssetCheckResult, AssetKey, asset_check
from phlo.defs.validation.dbt_validator import DBTValidatorResource

from phlo.config import config
from phlo.quality.contract import QualityCheckContract, dbt_check_name


@asset_check(
    name=dbt_check_name("generic", "fct_github_events"),
    asset=AssetKey(["fct_github_events"]),
    blocking=True,
    description="Runs dbt tests for fct_github_events and reports results via the contract metadata.",
)
def dbt_generic_fct_github_events(
    context: AssetCheckExecutionContext, dbt_validator: DBTValidatorResource
) -> AssetCheckResult:
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

    return AssetCheckResult(
        passed=bool(results.get("all_passed")),
        metadata=contract.to_dagster_metadata(),
    )
