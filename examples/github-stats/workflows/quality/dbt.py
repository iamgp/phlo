"""dbt-derived asset checks for GitHub example project.

This demonstrates the dbt quality check naming/metadata contract:
- Check name: dbt/<test_type>/<target>
- Metadata: source/partition_key/failed_count/total_count/query_or_sql/sample
"""

import os

from dagster import AssetCheckExecutionContext, AssetCheckResult, AssetKey, asset_check
from dagster_dbt import DbtCliResource
from phlo_quality.contract import QualityCheckContract, dbt_check_name

from phlo.config import get_settings


@asset_check(
    name=dbt_check_name("generic", "fct_github_events"),
    asset=AssetKey(["fct_github_events"]),
    blocking=True,
    description="Runs dbt tests for fct_github_events and reports results via the contract metadata.",
)
def dbt_generic_fct_github_events(
    context: AssetCheckExecutionContext, dbt_validator: DbtCliResource
) -> AssetCheckResult:
    settings = get_settings()
    branch_name = os.getenv("NESSIE_REF") or settings.iceberg_nessie_ref
    invocation = dbt_validator.cli(["test", "--select", "fct_github_events"], target=branch_name)
    run_results = invocation.get_artifact("run_results.json") or {}
    results = run_results.get("results") or []
    failures = [result.get("message") for result in results if result.get("status") in {"fail"}]
    failed_count = sum(1 for result in results if result.get("status") in {"fail", "error"})
    total_count = len(results)

    contract = QualityCheckContract(
        source="dbt",
        partition_key=None,
        failed_count=failed_count,
        total_count=total_count,
        query_or_sql=f"dbt test --select fct_github_events (NESSIE_REF={branch_name})",
        sample=failures,
    )

    return AssetCheckResult(
        passed=failed_count == 0,
        metadata=contract.to_dagster_metadata(),
    )
