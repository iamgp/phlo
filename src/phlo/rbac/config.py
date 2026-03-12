"""Configuration loader for canonical RBAC files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from phlo.rbac.models import CanonicalRBAC, PoliciesConfig, RolesConfig


class RBACConfigLoader:
    """Loads and validates canonical RBAC configuration files."""

    def __init__(self, base_path: Path | None = None):
        """Initialize the RBAC config loader.

        Args:
            base_path: Base path for RBAC config files. Defaults to .phlo in cwd.
        """
        self._base_path = base_path or Path.cwd() / ".phlo"

    @property
    def base_path(self) -> Path:
        """Return the base path for RBAC config files."""
        return self._base_path

    def load_roles(self, path: Path | None = None) -> RolesConfig:
        """Load roles configuration from YAML file.

        Args:
            path: Path to roles.yaml. Defaults to base_path/authorization/roles.yaml.

        Returns:
            Parsed RolesConfig.

        Raises:
            FileNotFoundError: If the roles file doesn't exist.
            ValueError: If the roles file is invalid.
        """
        if path is None:
            path = self._base_path / "authorization" / "roles.yaml"

        if not path.exists():
            raise FileNotFoundError(f"Roles config not found: {path}")

        with path.open() as f:
            data = yaml.safe_load(f) or {}

        try:
            return RolesConfig.from_dict(data)
        except Exception as e:
            raise ValueError(f"Invalid roles config: {e}") from e

    def load_policies(self, path: Path | None = None) -> PoliciesConfig:
        """Load policies configuration from YAML file.

        Args:
            path: Path to policies.yaml. Defaults to base_path/authorization/policies.yaml.

        Returns:
            Parsed PoliciesConfig.

        Raises:
            FileNotFoundError: If the policies file doesn't exist.
            ValueError: If the policies file is invalid.
        """
        if path is None:
            path = self._base_path / "authorization" / "policies.yaml"

        if not path.exists():
            raise FileNotFoundError(f"Policies config not found: {path}")

        with path.open() as f:
            data = yaml.safe_load(f) or {}

        try:
            return PoliciesConfig.from_dict(data)
        except Exception as e:
            raise ValueError(f"Invalid policies config: {e}") from e

    def load(self) -> CanonicalRBAC:
        """Load the complete canonical RBAC configuration.

        Returns:
            Combined CanonicalRBAC model.

        Raises:
            FileNotFoundError: If required config files don't exist.
            ValueError: If the configuration is invalid.
        """
        roles = self.load_roles()
        policies = self.load_policies()

        rbac = CanonicalRBAC.from_configs(roles, policies)

        errors = rbac.validate()
        if errors:
            raise ValueError(f"Invalid RBAC configuration: {errors}")

        return rbac

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the RBAC configuration.

        Returns:
            Tuple of (is_valid, error_messages).
        """
        try:
            rbac = self.load()
            errors = rbac.validate()
            return len(errors) == 0, errors
        except Exception as e:
            return False, [str(e)]

    def compute_version_hash(self) -> str:
        """Compute a hash of the current RBAC configuration.

        Returns:
            SHA256 hash of the configuration (truncated to 16 chars).

        Raises:
            FileNotFoundError: If required config files don't exist.
        """
        roles_path = self._base_path / "authorization" / "roles.yaml"
        policies_path = self._base_path / "authorization" / "policies.yaml"

        content: dict[str, Any] = {}
        if roles_path.exists():
            with roles_path.open() as f:
                content["roles"] = yaml.safe_load(f) or {}
        if policies_path.exists():
            with policies_path.open() as f:
                content["policies"] = yaml.safe_load(f) or {}

        json_content = json.dumps(content, sort_keys=True)
        return hashlib.sha256(json_content.encode()).hexdigest()[:16]
