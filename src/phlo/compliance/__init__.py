"""Compliance plane for regulated deployments.

The compliance plane sits on top of phlo.security and provides:
- Tamper-evident audit storage with hash chaining
- Electronic signatures for critical actions
- Validated system manifest capture
- Access governance primitives (dormant accounts, recertification, SoD, break-glass)
- Evidence pack export for validation teams

All compliance features are inert in open mode and active in regulated mode
(when regulated: true in phlo.yaml).
"""

from __future__ import annotations

from phlo.compliance.features import ComplianceFeatures, resolve_compliance_features

__all__ = [
    "ComplianceFeatures",
    "resolve_compliance_features",
]
