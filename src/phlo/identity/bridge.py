"""Identity bridge for canonical principal resolution.

This module provides the shared authn-to-authz canonicalization bridge that
converts AuthPrincipal (from authentication) to Principal (for authorization).

The bridge ensures that all regulated surfaces derive principals consistently
from the same upstream IdP or trusted proxy chain, using canonical RBAC
subject assignments.

Architecture:
    - Input: AuthPrincipal, request/session metadata, canonical RBAC subject assignments
    - Output: Principal with canonical roles and attributes

Regulated Mode Rules:
    - All regulated surfaces must use this bridge for principal resolution
    - Per-surface bespoke group-to-role mapping is forbidden in regulated mode
    - Local role mapping behavior is unsupported in regulated mode
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from phlo.logging import get_logger

if TYPE_CHECKING:
    from phlo.capabilities.interfaces import AuthPrincipal, Principal
    from phlo.rbac.models import CanonicalRBAC

logger = get_logger(__name__)

# Default group-to-role mapping for canonical RBAC
# Only known group names are mapped to canonical roles.
# Unknown groups are discarded to prevent privilege escalation.
DEFAULT_GROUP_ROLE_MAPPING: dict[str, str] = {
    "admin": "admin",
    "operators": "operator",
    "developers": "developer",
    "analysts": "analyst",
    "viewers": "viewer",
}

# Principal types approved for regulated mode
APPROVED_PRINCIPAL_TYPES: frozenset[str] = frozenset(
    {
        "user",  # Human user
        "service",  # Service principal
        "platform",  # Automated platform principal
    }
)


@dataclass(frozen=True)
class IdentityBridgeConfig:
    """Configuration for the identity bridge.

    Attributes:
        group_role_mapping: Mapping from IdP group names to canonical role names.
            Defaults to DEFAULT_GROUP_ROLE_MAPPING if not provided.
        enforce_approved_principal_types: If True, reject principals with
            non-approved principal types. Required in regulated mode.
        propagate_idp_groups: If True, propagate original IdP groups to
            principal attributes for audit purposes. Defaults to True.
        authentication_source_claim: Claim name to extract authentication source
            from AuthPrincipal attributes. Defaults to "authentication_source".
    """

    group_role_mapping: dict[str, str] = field(
        default_factory=lambda: DEFAULT_GROUP_ROLE_MAPPING.copy()
    )
    enforce_approved_principal_types: bool = False
    propagate_idp_groups: bool = True
    authentication_source_claim: str = "authentication_source"
    canonical_rbac: CanonicalRBAC | None = None


class IdentityBridge:
    """Shared authn-to-authz canonicalization bridge.

    This bridge converts AuthPrincipal (authenticated caller identity) to
    Principal (authorization subject) using canonical RBAC subject assignments.

    In regulated mode, all approved surfaces must use this bridge to ensure
    consistent principal resolution across the platform.

    Example:
        >>> from phlo.identity import IdentityBridge, IdentityBridgeConfig
        >>> bridge = IdentityBridge(IdentityBridgeConfig(enforce_approved_principal_types=True))
        >>> principal = bridge.canonicalize(auth_principal, request_context)
    """

    def __init__(self, config: IdentityBridgeConfig | None = None) -> None:
        """Initialize the identity bridge.

        Args:
            config: Bridge configuration. Uses defaults if not provided.
        """
        self.config = config or IdentityBridgeConfig()

    def canonicalize(
        self,
        auth_principal: AuthPrincipal,
        context: dict[str, str] | None = None,
    ) -> Principal:
        """Convert AuthPrincipal to canonical Principal.

        This is the core bridge function that:
        1. Validates the principal type is approved (if enforced)
        2. Maps IdP groups to canonical roles
        3. Applies principal-type default roles
        4. Propagates relevant attributes

        Args:
            auth_principal: Authenticated principal from the authn provider.
            context: Optional request/session context for audit metadata.

        Returns:
            Canonical Principal for authorization decisions.

        Raises:
            ValueError: If principal type is not approved and enforcement is enabled.
        """
        from phlo.capabilities.interfaces import Principal

        # Validate principal type if enforcement is enabled
        if (
            self.config.enforce_approved_principal_types
            and auth_principal.principal_type not in APPROVED_PRINCIPAL_TYPES
        ):
            logger.warning(
                "unapproved_principal_type_rejected",
                subject=auth_principal.subject,
                principal_type=auth_principal.principal_type,
                approved_types=list(APPROVED_PRINCIPAL_TYPES),
            )
            raise ValueError(
                f"Principal type '{auth_principal.principal_type}' is not approved "
                f"for regulated mode. Approved types: {APPROVED_PRINCIPAL_TYPES}"
            )

        # Map groups to canonical roles
        roles = set(self._map_groups_to_roles(auth_principal.groups))
        if self.config.canonical_rbac is not None:
            roles.update(
                self.config.canonical_rbac.effective_roles_for_subject(
                    auth_principal.subject,
                    auth_principal.principal_type,
                )
            )

        # Apply principal-type default roles
        roles = self._apply_principal_type_roles(
            auth_principal.principal_type, tuple(sorted(roles))
        )

        # Build attributes (use getattr for duck-typed principals)
        principal_attributes: dict[str, str] = dict(getattr(auth_principal, "attributes", {}))
        if self.config.propagate_idp_groups:
            # Store original groups for audit
            principal_attributes["idp_groups"] = ",".join(auth_principal.groups)

        # Extract authentication source (use getattr for duck-typed principals)
        issuer = getattr(auth_principal, "issuer", None)
        authentication_source = (
            principal_attributes.get(self.config.authentication_source_claim) or issuer or "unknown"
        )
        principal_attributes["authentication_source"] = authentication_source

        principal = Principal(
            subject=auth_principal.subject,
            principal_type=auth_principal.principal_type,
            roles=roles,
            attributes=principal_attributes,
        )

        logger.debug(
            "principal_canonicalized",
            subject=principal.subject,
            principal_type=principal.principal_type,
            roles=list(principal.roles),
            authentication_source=authentication_source,
        )

        return principal

    def _map_groups_to_roles(self, groups: tuple[str, ...]) -> tuple[str, ...]:
        """Map authentication groups to canonical roles.

        Only known group names are mapped to canonical roles.
        Unknown groups are discarded to prevent privilege escalation
        based on IdP-native group names.

        Args:
            groups: Tuple of group names from the authentication provider.

        Returns:
            Tuple of canonical role names.
        """
        roles: list[str] = []
        for group in groups:
            if group in self.config.group_role_mapping:
                canonical_role = self.config.group_role_mapping[group]
                if canonical_role not in roles:
                    roles.append(canonical_role)
        return tuple(roles)

    def _apply_principal_type_roles(
        self,
        principal_type: str,
        existing_roles: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Apply default roles based on principal type.

        Service principals automatically get the 'service' role if not already present.

        Args:
            principal_type: Type of principal ("user", "service", "platform").
            existing_roles: Current roles from group mapping.

        Returns:
            Tuple of roles including any principal-type defaults.
        """
        if principal_type == "service" and "service" not in existing_roles:
            return (*existing_roles, "service") if existing_roles else ("service",)
        return existing_roles


def create_regulated_bridge(
    group_role_mapping: dict[str, str] | None = None,
    canonical_rbac: CanonicalRBAC | None = None,
) -> IdentityBridge:
    """Create an identity bridge configured for regulated mode.

    This is a convenience factory that creates a bridge with regulated-mode
    enforcement enabled.

    Args:
        group_role_mapping: Retained for API compatibility. Regulated bridges
            never translate identity-provider groups into authorization roles.

    Returns:
        IdentityBridge configured for regulated mode.
    """
    config = IdentityBridgeConfig(
        group_role_mapping={},
        enforce_approved_principal_types=True,
        propagate_idp_groups=True,
        canonical_rbac=canonical_rbac,
    )
    return IdentityBridge(config)


def create_regulated_mode_bridge(
    group_role_mapping: dict[str, str] | None = None,
    canonical_rbac: CanonicalRBAC | None = None,
) -> IdentityBridge:
    """Deprecated: use create_regulated_bridge() instead."""
    import warnings

    warnings.warn(
        "create_regulated_mode_bridge() is deprecated, use create_regulated_bridge() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return create_regulated_bridge(group_role_mapping, canonical_rbac)


def canonicalize_principal(
    auth_principal: AuthPrincipal,
    regulated: bool = False,
    context: dict[str, str] | None = None,
) -> Principal:
    """Canonicalize an AuthPrincipal to a Principal.

    This is a convenience function for simple use cases. For more control,
    use the IdentityBridge class directly.

    Args:
        auth_principal: Authenticated principal from the authn provider.
        regulated: If True, enable regulated-mode enforcement.
        context: Optional request/session context.

    Returns:
        Canonical Principal for authorization decisions.
    """
    bridge = create_regulated_bridge() if regulated else IdentityBridge()
    return bridge.canonicalize(auth_principal, context)
