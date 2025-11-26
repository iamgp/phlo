# __init__.py - Schedules module initialization
# Provides schedule utilities for pipeline orchestration

from __future__ import annotations

import dagster as dg

from phlo.defs.jobs import JOBS


def build_defs() -> dg.Definitions:
    """Build schedule definitions.

    Schedules should be defined in user workflows.
    Framework returns jobs only (no schedules by default).
    """
    return dg.Definitions(jobs=JOBS)
