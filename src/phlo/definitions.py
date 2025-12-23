# definitions.py - Legacy Dagster entry point
#
# Prefer `phlo.framework.definitions` for project loading. This module remains as a thin alias.

from __future__ import annotations

from phlo.framework.definitions import build_definitions

defs = build_definitions()
