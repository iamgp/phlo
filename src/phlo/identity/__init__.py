"""Identity bridge for canonical principal resolution.

This module provides the shared authn-to-authz canonicalization bridge that
converts AuthPrincipal (from authentication) to Principal (for authorization).

Exports:
    IdentityBridge: Shared bridge for principal canonicalization.
    IdentityBridgeConfig: Configuration for the identity bridge.
    create_regulated_bridge: Factory for regulated-mode bridge.
    create_regulated_mode_bridge: Deprecated alias for create_regulated_bridge.
    canonicalize_principal: Convenience function for simple use cases.
    DEFAULT_GROUP_ROLE_MAPPING: Default group-to-role mapping.
    APPROVED_PRINCIPAL_TYPES: Set of approved principal types.
"""

from __future__ import annotations

from phlo.identity.bridge import (
    APPROVED_PRINCIPAL_TYPES,
    DEFAULT_GROUP_ROLE_MAPPING,
    IdentityBridge,
    IdentityBridgeConfig,
    canonicalize_principal,
    create_regulated_bridge,
    create_regulated_mode_bridge,
)

__all__ = [
    "APPROVED_PRINCIPAL_TYPES",
    "DEFAULT_GROUP_ROLE_MAPPING",
    "IdentityBridge",
    "IdentityBridgeConfig",
    "canonicalize_principal",
    "create_regulated_bridge",
    "create_regulated_mode_bridge",
]
