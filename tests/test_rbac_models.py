"""Tests for RBAC models and configuration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from phlo.rbac.config import RBACConfigLoader
from phlo.rbac.models import (
    CanonicalRBAC,
    PoliciesConfig,
    PolicyEffect,
    PolicyRule,
    RolesConfig,
)


class TestRolesConfig:
    """Tests for RolesConfig."""

    def test_parse_roles(self):
        """Test parsing roles from dict."""
        data = {
            "version": 1,
            "roles": {
                "viewer": {"inherits": []},
                "analyst": {"inherits": ["viewer"]},
                "admin": {"inherits": ["analyst"]},
            },
        }
        config = RolesConfig.from_dict(data)

        assert config.version == 1
        assert "viewer" in config.roles
        assert "analyst" in config.roles
        assert "admin" in config.roles

    def test_expand_role_hierarchy(self):
        """Test expanding role hierarchy."""
        data = {
            "version": 1,
            "roles": {
                "viewer": {"inherits": []},
                "analyst": {"inherits": ["viewer"]},
                "admin": {"inherits": ["analyst"]},
            },
        }
        config = RolesConfig.from_dict(data)

        expanded = config.expand_role_hierarchy("admin")
        assert "admin" in expanded
        assert "analyst" in expanded
        assert "viewer" in expanded

    def test_expand_unknown_role_raises(self):
        """Test that expanding unknown role raises."""
        data = {
            "version": 1,
            "roles": {
                "viewer": {"inherits": []},
            },
        }
        config = RolesConfig.from_dict(data)

        with pytest.raises(ValueError, match="Unknown role"):
            config.expand_role_hierarchy("unknown_role")

    def test_detect_cycle(self):
        """Test that cycles are detected."""
        data = {
            "version": 1,
            "roles": {
                "role_a": {"inherits": ["role_b"]},
                "role_b": {"inherits": ["role_a"]},
            },
        }
        config = RolesConfig.from_dict(data)

        with pytest.raises(ValueError, match="Cycle"):
            config.expand_role_hierarchy("role_a")

    def test_diamond_hierarchy(self):
        """Test that diamond hierarchies are handled correctly."""
        data = {
            "version": 1,
            "roles": {
                "viewer": {"inherits": []},
                "left": {"inherits": ["viewer"]},
                "right": {"inherits": ["viewer"]},
                "admin": {"inherits": ["left", "right"]},
            },
        }
        config = RolesConfig.from_dict(data)

        expanded = config.expand_role_hierarchy("admin")
        assert "admin" in expanded
        assert "left" in expanded
        assert "right" in expanded
        assert "viewer" in expanded
        assert len(expanded) == 4


class TestPoliciesConfig:
    """Tests for PoliciesConfig."""

    def test_parse_policies(self):
        """Test parsing policies from dict."""
        data = {
            "version": 1,
            "policies": [
                {
                    "policy_id": "allow_analyst_read",
                    "effect": "allow",
                    "principal": {"roles": ["analyst"]},
                    "action": "dataset.read",
                    "resource": {
                        "type": "dataset",
                        "id_pattern": "analytics.*",
                    },
                }
            ],
        }
        config = PoliciesConfig.from_dict(data)

        assert config.version == 1
        assert len(config.policies) == 1
        policy = config.policies[0]
        assert policy.policy_id == "allow_analyst_read"
        assert policy.effect == PolicyEffect.ALLOW
        assert "analyst" in policy.principal_roles

    def test_action_matching(self):
        """Test action matching with wildcards."""
        data = {
            "version": 1,
            "policies": [
                {
                    "policy_id": "allow_all_read",
                    "effect": "allow",
                    "principal": {"roles": ["viewer"]},
                    "action": "*",
                    "resource": {"type": "*", "id_pattern": "*"},
                }
            ],
        }
        config = PoliciesConfig.from_dict(data)

        assert config._action_matches("*", "dataset.read")
        assert config._action_matches("dataset.*", "dataset.read")
        assert not config._action_matches("asset.*", "dataset.read")


class TestCanonicalRBAC:
    """Tests for CanonicalRBAC."""

    def test_from_configs(self):
        """Test creating CanonicalRBAC from configs."""
        roles_data = {
            "version": 1,
            "roles": {
                "viewer": {"inherits": []},
                "analyst": {"inherits": ["viewer"]},
            },
        }
        policies_data = {
            "version": 1,
            "policies": [
                {
                    "policy_id": "allow_analyst_read",
                    "effect": "allow",
                    "principal": {"roles": ["analyst"]},
                    "action": "dataset.read",
                    "resource": {
                        "type": "dataset",
                        "id_pattern": "analytics.*",
                    },
                }
            ],
        }

        roles = RolesConfig.from_dict(roles_data)
        policies = PoliciesConfig.from_dict(policies_data)
        rbac = CanonicalRBAC.from_configs(roles, policies)

        assert rbac.version_hash is not None

    def test_validate(self):
        """Test validation catches errors."""
        roles_data = {
            "version": 1,
            "roles": {
                "viewer": {"inherits": []},
            },
        }
        policies_data = {
            "version": 1,
            "policies": [
                {
                    "policy_id": "allow_unknown_role",
                    "effect": "allow",
                    "principal": {"roles": ["nonexistent_role"]},
                    "action": "dataset.read",
                    "resource": {
                        "type": "dataset",
                        "id_pattern": "*",
                    },
                }
            ],
        }

        roles = RolesConfig.from_dict(roles_data)
        policies = PoliciesConfig.from_dict(policies_data)
        rbac = CanonicalRBAC.from_configs(roles, policies)

        errors = rbac.validate()
        assert len(errors) > 0
        assert "nonexistent_role" in errors[0]


class TestRBACConfigLoader:
    """Tests for RBACConfigLoader."""

    def test_load_from_files(self):
        """Test loading config from files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            auth_dir = base_path / "authorization"
            auth_dir.mkdir(parents=True)

            roles_content = {
                "version": 1,
                "roles": {
                    "viewer": {"inherits": []},
                    "analyst": {"inherits": ["viewer"]},
                },
            }
            policies_content = {
                "version": 1,
                "policies": [
                    {
                        "policy_id": "allow_analyst_read",
                        "effect": "allow",
                        "principal": {"roles": ["analyst"]},
                        "action": "dataset.read",
                        "resource": {
                            "type": "dataset",
                            "id_pattern": "analytics.*",
                        },
                    }
                ],
            }

            with (auth_dir / "roles.yaml").open("w") as f:
                yaml.dump(roles_content, f)
            with (auth_dir / "policies.yaml").open("w") as f:
                yaml.dump(policies_content, f)

            loader = RBACConfigLoader(base_path=base_path)
            rbac = loader.load()

            assert "viewer" in rbac.roles.roles
            assert "analyst" in rbac.roles.roles

    def test_load_missing_files_raises(self):
        """Test that missing files raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            loader = RBACConfigLoader(base_path=base_path)

            with pytest.raises(FileNotFoundError):
                loader.load()

    def test_validate(self):
        """Test validate method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            auth_dir = base_path / "authorization"
            auth_dir.mkdir(parents=True)

            roles_content = {
                "version": 1,
                "roles": {
                    "viewer": {"inherits": []},
                },
            }
            policies_content = {
                "version": 1,
                "policies": [],
            }

            with (auth_dir / "roles.yaml").open("w") as f:
                yaml.dump(roles_content, f)
            with (auth_dir / "policies.yaml").open("w") as f:
                yaml.dump(policies_content, f)

            loader = RBACConfigLoader(base_path=base_path)
            is_valid, errors = loader.validate()

            assert is_valid
            assert len(errors) == 0


class TestPolicyRule:
    """Tests for PolicyRule."""

    def test_from_dict(self):
        """Test parsing PolicyRule from dict."""
        data = {
            "policy_id": "test_policy",
            "effect": "allow",
            "principal": {"roles": ["viewer"], "attributes": {"team": "data"}},
            "action": "dataset.read",
            "resource": {
                "type": "dataset",
                "id_pattern": "analytics.*",
                "attributes": {"env": "prod"},
            },
        }

        rule = PolicyRule.from_dict(data)

        assert rule.policy_id == "test_policy"
        assert rule.effect == PolicyEffect.ALLOW
        assert rule.principal_roles == ("viewer",)
        assert rule.principal_attributes == {"team": "data"}
        assert rule.action == "dataset.read"
        assert rule.resource_type == "dataset"
        assert rule.resource_id_pattern == "analytics.*"
        assert rule.resource_attributes == {"env": "prod"}

    def test_default_deny_effect(self):
        """Test default effect is deny."""
        data = {
            "policy_id": "test_policy",
            "principal": {"roles": ["viewer"]},
            "action": "dataset.read",
            "resource": {"type": "dataset", "id_pattern": "*"},
        }

        rule = PolicyRule.from_dict(data)

        assert rule.effect == PolicyEffect.DENY
