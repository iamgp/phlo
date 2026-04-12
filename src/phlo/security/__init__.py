"""phlo.security: regulated access control namespace.

Submodules:
    mode: regulated mode detection (PHLO_REGULATED_MODE env var).
    adapters: SurfaceOperation, RegulatedSurfaceAdapter, EnforcementResult types.
    enforcement: EnforcementContext singleton and enforce() core function.
    gating: surface-level allowlist/blocklist for regulated mode.
    validation: startup validation for regulated mode.
"""

from __future__ import annotations

from phlo.security.adapters import (
    EnforcementResult,
    RegulatedSurfaceAdapter,
    SurfaceActivationStatus,
    SurfaceOperation,
)
from phlo.security.enforcement import EnforcementContext, enforce
from phlo.security.gating import (
    UnsupportedSurfaceError,
    block_direct_dagster_access,
    check_service_allowed,
    get_approved_services,
    get_blocked_services,
    is_service_allowed,
    validate_service_selection,
)
from phlo.security.mode import is_regulated_mode_enabled
from phlo.security.validation import (
    RegulatedModeError,
    RegulatedModeValidationReport,
    require_regulated_mode_validation,
    run_regulated_mode_validation,
)

__all__ = [
    "EnforcementContext",
    "EnforcementResult",
    "RegulatedModeError",
    "RegulatedModeValidationReport",
    "RegulatedSurfaceAdapter",
    "SurfaceActivationStatus",
    "SurfaceOperation",
    "UnsupportedSurfaceError",
    "block_direct_dagster_access",
    "check_service_allowed",
    "enforce",
    "get_approved_services",
    "get_blocked_services",
    "is_regulated_mode_enabled",
    "is_service_allowed",
    "require_regulated_mode_validation",
    "run_regulated_mode_validation",
    "validate_service_selection",
]
