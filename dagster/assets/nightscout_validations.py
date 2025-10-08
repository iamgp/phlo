"""
Data Quality Validations for Nightscout Glucose Data

This module uses Great Expectations to validate glucose data quality at
multiple points in the pipeline:
1. After raw ingestion (basic structure checks)
2. After enrichment (derived fields validation)
3. Before loading to marts (business logic validation)

Why validate?
- CGM sensors can malfunction or lose calibration
- API data can be incomplete or corrupted
- Catching bad data early prevents downstream analytics issues
- Compliance and audit requirements for health data
"""

from pathlib import Path
from typing import Any

import duckdb
from dagster import AssetExecutionContext, AssetIn, asset
from great_expectations.core import ExpectationSuite
from great_expectations.dataset import SqlAlchemyDataset


@asset(
    group_name="nightscout_quality",
    compute_kind="great_expectations",
    description="Validate raw glucose data meets basic quality standards",
    ins={"int_glucose_enriched": AssetIn(key="int_glucose_enriched")},
)
def validate_glucose_enriched(
    context: AssetExecutionContext, int_glucose_enriched: str
) -> dict[str, Any]:
    """
    Run Great Expectations validation suite on enriched glucose data.

    Validates:
    - Glucose values are in physiological range (20-600 mg/dL)
    - No null values in critical fields
    - Direction/trend values are valid
    - Time-based fields are properly calculated
    - Categorical fields match expected values

    Returns validation results and raises warning if critical checks fail.
    """
    suite_path = Path(__file__).parent.parent.parent / "great_expectations" / "expectations" / "nightscout_suite.json"

    if not suite_path.exists():
        context.log.warning(f"Expectation suite not found at {suite_path}, skipping validation")
        return {"status": "skipped", "reason": "suite_not_found"}

    # Load expectation suite
    suite = ExpectationSuite.read_json(str(suite_path))

    # Query enriched data into memory for validation
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE glucose_enriched AS SELECT * FROM read_parquet('/data/lake/curated/int_glucose_enriched/*.parquet')")

    # Convert to pandas for GE validation (GE expects pandas or SQL connection)
    df = con.execute("SELECT * FROM glucose_enriched").df()
    con.close()

    # Run validation
    context.log.info(f"Running {len(suite.expectations)} expectations on {len(df)} rows")

    # Validate using GE
    from great_expectations.dataset import PandasDataset
    ge_df = PandasDataset(df)

    results = []
    success_count = 0
    failure_count = 0

    for expectation in suite.expectations:
        exp_type = expectation.expectation_type
        kwargs = expectation.kwargs

        try:
            result = getattr(ge_df, exp_type)(**kwargs)
            results.append({
                "expectation": exp_type,
                "success": result["success"],
                "details": result
            })

            if result["success"]:
                success_count += 1
            else:
                failure_count += 1
                context.log.warning(f"Expectation failed: {exp_type} - {result.get('result', {})}")

        except Exception as e:
            context.log.error(f"Error running expectation {exp_type}: {e}")
            failure_count += 1

    # Summary
    total = success_count + failure_count
    success_rate = (success_count / total * 100) if total > 0 else 0

    context.log.info(f"Validation complete: {success_count}/{total} passed ({success_rate:.1f}%)")

    if failure_count > 0:
        context.log.warning(f"{failure_count} expectations failed - review data quality")

    return {
        "status": "completed",
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": success_rate,
        "results": results
    }
