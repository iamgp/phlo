from __future__ import annotations

import dagster as dg

from cascade.defs.quality.nightscout import nightscout_glucose_quality_check


def build_defs() -> dg.Definitions:
    return dg.Definitions(asset_checks=[nightscout_glucose_quality_check])
