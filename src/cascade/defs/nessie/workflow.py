# workflow.py - Nessie branching workflow assets for Git-like data versioning
# Defines Dagster assets that manage dynamic pipeline branches and production promotion
# using Nessie branches for isolated data development and controlled promotion

"""
Nessie branching workflows for data engineering.

Provides assets that orchestrate dynamic branch workflows:
- Pipeline branch creation (pipeline/run-{id})
- Validation-gated promotion (pipeline -> main)
- Production tagging
"""

from __future__ import annotations

from datetime import datetime

import dagster as dg
from dagster import AssetExecutionContext, MaterializeResult
from cascade.config import config
from cascade.defs.nessie import NessieResource
from cascade.defs.nessie.branch_manager import BranchManagerResource


# --- Aggregation Function ---
# Builds workflow asset definitions
def build_defs() -> dg.Definitions:
    """Build Nessie workflow definitions."""
    return dg.Definitions(
        assets=[],  # No user-facing Nessie assets - all managed by sensors
    )
