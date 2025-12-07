"""
Validation package for Cascade data quality gates.

This package contains validation resources that can be used to validate
data quality in user workflows.

Components:
-----------
- DBTValidatorResource: Runs dbt tests and parses results
- FreshnessValidatorResource: Checks data freshness against configured thresholds
- SchemaCompatibilityValidatorResource: Validates schema compatibility between branches

Note: Asset checks should be defined in user workflows, not in the core framework.
"""

import dagster as dg

from phlo.defs.validation.dbt_validator import DBTValidatorResource
from phlo.defs.validation.freshness_validator import FreshnessValidatorResource
from phlo.defs.validation.schema_validator import SchemaCompatibilityValidatorResource

__all__ = [
    "DBTValidatorResource",
    "FreshnessValidatorResource",
    "SchemaCompatibilityValidatorResource",
]


def build_defs() -> dg.Definitions:
    """Build validation definitions.

    Asset checks should be defined in user workflows using the validation resources.
    This returns empty definitions as the framework doesn't include example checks.
    """
    return dg.Definitions(asset_checks=[])
