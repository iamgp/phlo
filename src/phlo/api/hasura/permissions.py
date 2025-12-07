"""Hasura permission management and synchronization."""

import json
from pathlib import Path
from typing import Any, Optional

from phlo.api.hasura.client import HasuraClient


class HasuraPermissionManager:
    """Manages Hasura permissions from YAML/JSON config files."""

    def __init__(self, client: Optional[HasuraClient] = None):
        """Initialize permission manager.

        Args:
            client: HasuraClient instance
        """
        self.client = client or HasuraClient()

    def load_config(self, config_path: str | Path) -> dict[str, Any]:
        """Load permission config from YAML or JSON file.

        Args:
            config_path: Path to config file

        Returns:
            Config dictionary
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

        Args:
            config: Permission configuration dictionary
            verbose: Print progress messages

        Returns:
            Summary of applied permissions
        """
        if verbose:
            print("=" * 60)
            print("Hasura Permission Sync")
            print("=" * 60)
            print()

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
                print(f"Syncing {table_path}...")

            # Sync SELECT permissions
            select_perms = permissions.get("select", {})
            for role, perm_config in select_perms.items():
                if perm_config is False:
                    # Explicitly disabled
                    continue

                try:
                    if verbose:
                        print(f"  SELECT for {role}...", end=" ")

                    filter_expr = perm_config.get("filter", {})
                    columns = perm_config.get("columns", None)

                    self.client.create_select_permission(
                        schema, table, role, filter=filter_expr, columns=columns
                    )

                    results["select"][(table_path, role)] = True
                    if verbose:
                        print("✓")
                except Exception as e:
                    results["select"][(table_path, role)] = False
                    if verbose:
                        print(f"✗ ({str(e)[:50]})")

            # Sync INSERT permissions
            insert_perms = permissions.get("insert", {})
            for role, perm_config in insert_perms.items():
                if perm_config is False:
                    continue

                try:
                    if verbose:
                        print(f"  INSERT for {role}...", end=" ")

                    check = perm_config.get("check", {})
                    columns = perm_config.get("columns", None)
                    set_values = perm_config.get("set", None)

                    self.client.create_insert_permission(
                        schema, table, role, check=check, columns=columns, set=set_values
                    )

                    results["insert"][(table_path, role)] = True
                    if verbose:
                        print("✓")
                except Exception as e:
                    results["insert"][(table_path, role)] = False
                    if verbose:
                        print(f"✗ ({str(e)[:50]})")

        if verbose:
            print()
            print("=" * 60)
            success_count = sum(1 for v in results.values() if v)
            total_count = sum(len(v) for v in results.values())
            print(f"✓ Permission sync completed ({success_count}/{total_count})")
            print("=" * 60)

        return results

    def export_permissions(self) -> dict[str, Any]:
        """Export current Hasura permissions to config format.

        Returns:
            Permission configuration dictionary
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

        Args:
            config: Permission configuration dictionary
            output_path: Path to save file
            format: 'json' or 'yaml'
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
    """Manages role hierarchy for permission inheritance."""

    def __init__(self, hierarchy: Optional[dict[str, list[str]]] = None):
        """Initialize role hierarchy.

        Args:
            hierarchy: Dict of role -> [inherited_roles]
                Default: admin -> [analyst, anon], analyst -> [anon]
        """
        self.hierarchy = hierarchy or {
            "admin": ["analyst", "anon"],
            "analyst": ["anon"],
            "anon": [],
        }

    def get_inherited_roles(self, role: str) -> list[str]:
        """Get all roles inherited by a role.

        Args:
            role: Role name

        Returns:
            List of inherited roles (includes self)
        """
        inherited = [role]

        def visit(r: str) -> None:
            for inherited_role in self.hierarchy.get(r, []):
                if inherited_role not in inherited:
                    inherited.append(inherited_role)
                    visit(inherited_role)

        visit(role)
        return inherited

    def expand_permissions(self, config: dict[str, Any]) -> dict[str, Any]:
        """Expand permissions based on role hierarchy.

        Args:
            config: Permission configuration

        Returns:
            Expanded configuration with inherited permissions
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
