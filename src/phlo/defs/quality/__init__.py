# __init__.py - Quality module initialization
# Quality checks are defined in user workflows, not in the core framework

from __future__ import annotations

import dagster as dg


def build_defs() -> dg.Definitions:
    """Build quality check definitions.
    
    Quality checks should be defined in user workflows using @phlo_quality decorator.
    This returns empty definitions as the framework doesn't include example checks.
    """
    return dg.Definitions(asset_checks=[])
