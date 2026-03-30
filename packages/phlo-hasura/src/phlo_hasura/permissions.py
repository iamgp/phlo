"""Hasura permission management and synchronization.

This module provides classes and functions for managing Hasura permissions
from configuration files. It supports YAML and JSON formats, role hierarchies,
and bulk permission operations.

Classes:
    HasuraPermissionManager: Manages permissions from config files.
    RoleHierarchy: Manages role inheritance for permission expansion.

Example:
    >>> from phlo_hasura.permissions import HasuraPermissionManager
    >>> manager = HasuraPermissionManager()
    >>> config = manager.load_config("permissions.yaml")
    >>> manager.sync_permissions(config)

"""

import json
from pathlib import Path
from typing import Any, Optional

from phlo_hasura.client import HasuraClient
from phlo.logging import get_logger

logger = get_logger(__name__)


class HasuraPermissionManager:
    """Manages Hasura permissions from YAML/JSON config files.

    Provides methods for loading permission configurations, synchronizing
    them with Hasura, and exporting current permissions back to config format.

    Attributes:
        client: HasuraClient instance for API operations.

    Example:
        >>> manager = HasuraPermissionManager()
        >>> config = manager.load_config("permissions.yaml")
        >>> manager.sync_permissions(config, verbose=True)
        >>> current = manager.export_permissions()
        >>> manager.save_permissions(current, "backup.json")

    """

    def __init__(self, client: Optional[HasuraClient] = None):
        """Initialize permission manager.

        Args:
            client: HasuraClient instance for API operations. If not provided,
                a new HasuraClient will be instantiated with default settings.

        Example:
            >>> manager = HasuraPermissionManager()
            >>> custom_manager = HasuraPermissionManager(HasuraClient())

        """
        self.client = client or HasuraClient()

    def load_config(self, config_path: str | Path) -> dict[str, Any]:
        """Load permission config from YAML or JSON file.

        Reads a permission configuration file and returns it as a dictionary.
        Supports both .json and .yaml/.yml file extensions.

        Args:
            config_path: Path to the config file (relative or absolute).

        Returns:
            Config dictionary containing permission definitions.

        Raises:
            ImportError: If PyYAML is required but not installed (YAML files only).
            ValueError: If the file format is not supported.
            FileNotFoundError: If the config file does not exist.

        Example:
            >>> config = manager.load_config("permissions.yaml")
            >>> config = manager.load_config("/path/to/config.json")

        """
        config_path = Path(config_path)

        if config_path.suffix == ".json":
            with open(config_path) as f:
                return json.load(f)

        elif config_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
            except ImportError:
                raise ImportError("PyYAML required for YAML config files")

            with open(config_path) as f:
                return yaml.safe_load(f) or {}

        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}")

    def sync_permissions(
        self,
        config: dict[str, Any],
        verbose: bool = True,
    ) -> dict[str, Any]:
        """Apply permissions from config to Hasura.

        Synchronizes permissions defined in the config dictionary with
        the actual Hasura instance. Creates or updates SELECT and INSERT
        permissions for all tables and roles specified.

        Args:
            config: Permission configuration dictionary with structure:
                {
                    "tables": {
                        "schema.table": {
                            "select": {"role": {"filter": {}, "columns": []}},
                            "insert": {"role": {"check": {}, "columns": []}}
                        }
                    }
                }
            verbose: Print progress messages during synchronization.

        Returns:
            Summary dictionary with success/failure status for each permission:
            {
                "select": {(table_path, role): bool},
                "insert": {(table_path, role): bool},
                ...
            }

        Example:
            >>> config = {
            ...     "tables": {
            ...         "api.orders": {
            ...             "select": {"anon": {"filter": {}, "columns": ["*"]}}
            ...         }
            ...     }
            ... }
            >>> results = manager.sync_permissions(config)

        """
        if verbose:
            logger.info("=" * 60)
            logger.info("Hasura Permission Sync")
            logger.info("=" * 60)

        results = {
            "select": {},
            "insert": {},
            "update": {},
            "delete": {},
        }

        tables = config.get("tables", {})

        for table_path, permissions in tables.items():
            schema, table = table_path.rsplit(".", 1)

            if verbose:
                logger.info("Syncing %s...", table_path)

            # Sync SELECT permissions
            select_perms = permissions.get("select", {})
            for role, perm_config in select_perms.items():
                if perm_config is False:
                    # Explicitly disabled
                    continue

                try:
                    if verbose:
                        logger.info("  SELECT for %s...", role)

                    filter_expr = perm_config.get("filter", {})
                    columns = perm_config.get("columns", None)

                    self.client.create_select_permission(
                        schema, table, role, filter=filter_expr, columns=columns
                    )

                    results["select"][(table_path, role)] = True
                    if verbose:
                        logger.info("  SELECT for %s ✓", role)
                except Exception as e:
                    results["select"][(table_path, role)] = False
                    if verbose:
                        logger.warning("  SELECT for %s ✗ (%s)", role, str(e)[:200])

            # Sync INSERT permissions
            insert_perms = permissions.get("insert", {})
            for role, perm_config in insert_perms.items():
                if perm_config is False:
                    continue

                try:
                    if verbose:
                        logger.info("  INSERT for %s...", role)

                    check = perm_config.get("check", {})
                    columns = perm_config.get("columns", None)
                    set_values = perm_config.get("set", None)

                    self.client.create_insert_permission(
                        schema, table, role, check=check, columns=columns, set=set_values
                    )

                    results["insert"][(table_path, role)] = True
                    if verbose:
                        logger.info("  INSERT for %s ✓", role)
                except Exception as e:
                    results["insert"][(table_path, role)] = False
                    if verbose:
                        logger.warning("  INSERT for %s ✗ (%s)", role, str(e)[:200])

        if verbose:
            logger.info("=" * 60)
            flat_results = [ok for group in results.values() for ok in group.values()]
            success_count = sum(1 for ok in flat_results if ok)
            total_count = len(flat_results)
            logger.info("✓ Permission sync completed (%s/%s)", success_count, total_count)
            logger.info("=" * 60)

        return results

    def export_permissions(self) -> dict[str, Any]:
        """Export current Hasura permissions to config format.

        Retrieves the current permission configuration from Hasura and
        formats it as a config dictionary suitable for saving to a file.

        Returns:
            Permission configuration dictionary with structure:
            {
                "tables": {
                    "schema.table": {
                        "select": {"role": {"filter": {}, "columns": []}},
                        "insert": {"role": {"filter": {}, "columns": [], "check": {}}},
                        ...
                    }
                }
            }

        Example:
            >>> config = manager.export_permissions()
            >>> for table, perms in config["tables"].items():
            ...     print(f"{table}: {list(perms.keys())}")

        """
        metadata = self.client.export_metadata()

        config = {"tables": {}}

        for source in metadata.get("sources", []):
            if source.get("name") != "default":
                continue

            for table in source.get("tables", []):
                schema = table.get("table", {}).get("schema", "public")
                table_name = table["table"]["name"]
                table_path = f"{schema}.{table_name}"

                config["tables"][table_path] = {}

                # Extract permissions
                for perm_type in ["select", "insert", "update", "delete"]:
                    perm_key = f"{perm_type}_permissions"
                    perms = table.get(perm_key, [])

                    if not perms:
                        continue

                    config["tables"][table_path][perm_type] = {}

                    for perm in perms:
                        role = perm.get("role")
                        permission = perm.get("permission", {})

                        config["tables"][table_path][perm_type][role] = {
                            "filter": permission.get("filter", {}),
                            "columns": permission.get("columns", ["*"]),
                        }

                        if perm_type == "insert":
                            config["tables"][table_path][perm_type][role]["check"] = permission.get(
                                "check", {}
                            )

        return config

    def save_permissions(
        self, config: dict[str, Any], output_path: str | Path, format: str = "json"
    ) -> None:
        """Save permissions to file.

        Writes a permission configuration dictionary to a file in either
        JSON or YAML format.

        Args:
            config: Permission configuration dictionary to save.
            output_path: Path where the file should be saved.
            format: Output format, either 'json' or 'yaml' (default: 'json').

        Raises:
            ImportError: If PyYAML is required but not installed (YAML format only).
            ValueError: If an unsupported format is specified.

        Example:
            >>> config = manager.export_permissions()
            >>> manager.save_permissions(config, "perms.json")
            >>> manager.save_permissions(config, "perms.yaml", format="yaml")

        """
        output_path = Path(output_path)

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(config, f, indent=2)

        elif format == "yaml":
            try:
                import yaml
            except ImportError:
                raise ImportError("PyYAML required for YAML format")

            with open(output_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        else:
            raise ValueError(f"Unsupported format: {format}")


class RoleHierarchy:
    """Manages role hierarchy for permission inheritance.

    Implements role-based permission inheritance where roles can inherit
    permissions from other roles. For example, an "admin" role might
    inherit all permissions from "analyst" and "anon" roles.

    Attributes:
        hierarchy: Dictionary mapping roles to their inherited roles.

    Example:
        >>> hierarchy = RoleHierarchy()
        >>> inherited = hierarchy.get_inherited_roles("admin")
        >>> print(inherited)  # ['admin', 'analyst', 'anon']
        >>> expanded = hierarchy.expand_permissions(config)

    """

    def __init__(self, hierarchy: Optional[dict[str, list[str]]] = None):
        """Initialize role hierarchy.

        Args:
            hierarchy: Dictionary mapping roles to lists of inherited roles.
                Default hierarchy is:
                - admin -> [analyst, anon]
                - analyst -> [anon]
                - anon -> []

        Example:
            >>> default = RoleHierarchy()
            >>> custom = RoleHierarchy({
            ...     "superuser": ["admin", "user"],
            ...     "admin": ["user"],
            ...     "user": []
            ... })

        """
        self.hierarchy = hierarchy or {
            "admin": ["analyst", "anon"],
            "analyst": ["anon"],
            "anon": [],
        }

    def get_inherited_roles(self, role: str) -> list[str]:
        """Get all roles inherited by a role.

        Performs a depth-first traversal of the role hierarchy to find
        all roles that the specified role inherits from, including itself.

        Args:
            role: Role name to get inherited roles for.

        Returns:
            List of inherited role names including the input role itself.

        Example:
            >>> hierarchy = RoleHierarchy()
            >>> hierarchy.get_inherited_roles("admin")
            ['admin', 'analyst', 'anon']
            >>> hierarchy.get_inherited_roles("anon")
            ['anon']

        """
        inherited = [role]

        def visit(r: str) -> None:
            """Depth-first traversal that accumulates inherited roles."""
            for inherited_role in self.hierarchy.get(r, []):
                if inherited_role not in inherited:
                    inherited.append(inherited_role)
                    visit(inherited_role)

        visit(role)
        return inherited

    def expand_permissions(self, config: dict[str, Any]) -> dict[str, Any]:
        """Expand permissions based on role hierarchy.

        Takes a permission configuration and expands it to include
        all inherited permissions. Higher-level roles receive the
        permissions of their inherited roles.

        Args:
            config: Permission configuration dictionary with tables and roles.

        Returns:
            Expanded configuration with inherited permissions included.
            Each role in the hierarchy receives all permissions from the
            roles it inherits.

        Example:
            >>> config = {
            ...     "tables": {
            ...         "api.users": {
            ...             "select": {"admin": {"filter": {}, "columns": ["*"]}}
            ...         }
            ...     }
            ... }
            >>> expanded = hierarchy.expand_permissions(config)
            >>> # Now includes select permissions for analyst and anon too

        """
        expanded = {"tables": {}}

        for table_path, permissions in config.get("tables", {}).items():
            expanded["tables"][table_path] = {}

            for perm_type in ["select", "insert", "update", "delete"]:
                if perm_type not in permissions:
                    continue

                expanded["tables"][table_path][perm_type] = {}

                for role, perm_config in permissions[perm_type].items():
                    inherited_roles = self.get_inherited_roles(role)

                    for inherited_role in inherited_roles:
                        if inherited_role not in expanded["tables"][table_path][perm_type]:
                            expanded["tables"][table_path][perm_type][inherited_role] = (
                                perm_config.copy()
                            )

        return expanded
