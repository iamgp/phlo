# HasuraPermissionManager (/docs/python-reference/packages/phlo-hasura/phlo_hasura/permissions/HasuraPermissionManager)



Manages Hasura permissions from YAML/JSON config files.

Provides methods for loading permission configurations, synchronizing
them with Hasura, and exporting current permissions back to config format.

Attributes [#attributes]

<PyAttribute name="&#x22;client&#x22;" type="null" value="&#x22;client or HasuraClient()&#x22;">
  HasuraClient instance for API operations.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, client=None)&#x22;">
  Initialize permission manager.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > manager = HasuraPermissionManager()
    > > > custom\_manager = HasuraPermissionManager(HasuraClient())
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;client&#x22;" type="&#x22;Optional[HasuraClient]&#x22;" value="&#x22;None&#x22;">
      HasuraClient instance for API operations. If not provided,
      a new HasuraClient will be instantiated with default settings.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;load_config&#x22;" type="&#x22;(self, config_path) -> dict[str, Any]&#x22;">
  Load permission config from YAML or JSON file.

  Reads a permission configuration file and returns it as a dictionary.
  Supports both .json and .yaml/.yml file extensions.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > config = manager.load\_config("permissions.yaml")
    > > > config = manager.load\_config("/path/to/config.json")
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config_path&#x22;" type="&#x22;str | Path&#x22;" value="undefined">
      Path to the config file (relative or absolute).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Config dictionary containing permission definitions.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;sync_permissions&#x22;" type="&#x22;(self, config, verbose=True) -> dict[str, Any]&#x22;">
  Apply permissions from config to Hasura.

  Synchronizes permissions defined in the config dictionary with
  the actual Hasura instance. Creates or updates SELECT and INSERT
  permissions for all tables and roles specified.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > config = \{
    > > > ...     "tables": \{
    > > > ...         "api.orders": \{
    > > > ...             "select": \{"anon": \{"filter": \{}, "columns": \["\*"]}}
    > > > ...         }
    > > > ...     }
    > > > ... }
    > > > results = manager.sync\_permissions(config)
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Permission configuration dictionary with structure:
      \{
      "tables": \{
      "schema.table": \{
      "select": \{"role": \{"filter": \{}, "columns": \[]}},
      "insert": \{"role": \{"check": \{}, "columns": \[]}}
      }
      }
      }
    </PyParameter>

    <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Print progress messages during synchronization.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Summary dictionary with success/failure status for each permission:
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;export_permissions&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Export current Hasura permissions to config format.

  Retrieves the current permission configuration from Hasura and
  formats it as a config dictionary suitable for saving to a file.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > config = manager.export\_permissions()
    > > > for table, perms in config\["tables"].items():
    > > > ...     print(f"\{table}: \{list(perms.keys())}")
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Permission configuration dictionary with structure:
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;save_permissions&#x22;" type="&#x22;(self, config, output_path, format='json') -> None&#x22;">
  Save permissions to file.

  Writes a permission configuration dictionary to a file in either
  JSON or YAML format.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > config = manager.export\_permissions()
    > > > manager.save\_permissions(config, "perms.json")
    > > > manager.save\_permissions(config, "perms.yaml", format="yaml")
  </Callout>

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Permission configuration dictionary to save.
    </PyParameter>

    <PyParameter name="&#x22;output_path&#x22;" type="&#x22;str | Path&#x22;" value="undefined">
      Path where the file should be saved.
    </PyParameter>

    <PyParameter name="&#x22;format&#x22;" type="&#x22;str&#x22;" value="&#x22;'json'&#x22;">
      Output format, either 'json' or 'yaml' (default: 'json').
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
