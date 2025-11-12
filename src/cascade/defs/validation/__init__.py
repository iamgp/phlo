"""
Validation package for Cascade data quality gates.

This package contains validation resources and the orchestrator asset that
coordinates all validation gates before promoting branches to main.

Components:
-----------
- PanderaValidatorResource: Validates data using Pandera schemas with severity-based blocking
- DBTValidatorResource: Runs dbt tests and parses results
- FreshnessValidatorResource: Checks data freshness against configured thresholds
- SchemaCompatibilityValidatorResource: Validates schema compatibility between branches
- validation_orchestrator: Asset that runs all validation gates and aggregates results
"""

from cascade.defs.validation.dbt_validator import DBTValidatorResource
from cascade.defs.validation.freshness_validator import FreshnessValidatorResource
from cascade.defs.validation.orchestrator import validation_orchestrator
from cascade.defs.validation.pandera_validator import PanderaValidatorResource
from cascade.defs.validation.schema_validator import SchemaCompatibilityValidatorResource

__all__ = [
    "PanderaValidatorResource",
    "DBTValidatorResource",
    "FreshnessValidatorResource",
    "SchemaCompatibilityValidatorResource",
    "validation_orchestrator",
]
