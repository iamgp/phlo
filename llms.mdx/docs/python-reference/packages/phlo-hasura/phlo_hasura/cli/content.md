# cli (/docs/python-reference/packages/phlo-hasura/phlo_hasura/cli)



Hasura CLI commands for Phlo.

This module provides Click CLI commands for managing Hasura GraphQL metadata,
including table tracking, relationship setup, permission management, and
metadata export/import operations.

Commands:
track: Auto-discover and track tables in Hasura.
relationships: Auto-create relationships from foreign keys.
permissions: Set up default permissions for tracked tables.
auto\_setup: Complete auto-configuration (tables, relationships, permissions).
export: Export current Hasura metadata to file.
apply: Apply Hasura metadata from file.
status: Show Hasura tracking status.
sync-permissions: Sync permissions from config file.

Example:
$ phlo hasura track --schema api --verbose
$ phlo hasura auto-setup --schema marts
$ phlo hasura export --output metadata.json

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_log_error_and_raise&#x22;" type="&#x22;(exception, log_context, error_msg) -> None&#x22;">
      Log an error and raise a ClickException.

      <PySourceCode>
        ```python
        def _log_error_and_raise(exception: Exception, log_context: dict, error_msg: str) -> None:
            """Log an error and raise a ClickException.

            Args:
                exception: The exception that occurred.
                log_context: Dictionary of context for structured logging.
                error_msg: The message to display to the user.

            Raises:
                click.ClickException: Always raises with the provided error message.

            """
            logger.exception("hasura_command_failed", **log_context)
            raise click.ClickException(str(exception))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;exception&#x22;" type="&#x22;Exception&#x22;" value="undefined">
          The exception that occurred.
        </PyParameter>

        <PyParameter name="&#x22;log_context&#x22;" type="&#x22;dict&#x22;" value="undefined">
          Dictionary of context for structured logging.
        </PyParameter>

        <PyParameter name="&#x22;error_msg&#x22;" type="&#x22;str&#x22;" value="undefined">
          The message to display to the user.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;hasura&#x22;" type="&#x22;() -> None&#x22;">
      Hasura GraphQL metadata management CLI.

      Provides commands for managing Hasura metadata including table tracking,
      relationship configuration, permission setup, and metadata export/import.

      Example:
      $ phlo hasura --help
      $ phlo hasura track --schema api
      $ phlo hasura export --output metadata.json

      <PySourceCode>
        ```python
        @click.group()
        def hasura() -> None:
            """Hasura GraphQL metadata management CLI.

            Provides commands for managing Hasura metadata including table tracking,
            relationship configuration, permission setup, and metadata export/import.

            Example:
                $ phlo hasura --help
                $ phlo hasura track --schema api
                $ phlo hasura export --output metadata.json

            """
            pass
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;track&#x22;" type="&#x22;(schema, exclude, verbose) -> None&#x22;">
      Auto-discover and track tables in Hasura.

      Discovers all tables in the specified schema and tracks them in Hasura,
      optionally excluding specific tables. Prints a summary of successfully
      tracked tables.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo hasura track --schema api
        $ phlo hasura track --schema marts --exclude staging\_table --verbose
      </Callout>

      <PySourceCode>
        ```python
        @hasura.command()
        @click.option(
            "--schema",
            default="api",
            help="Schema to track tables from (default: api)",
        )
        @click.option(
            "--exclude",
            multiple=True,
            help="Tables to exclude from tracking",
        )
        @click.option(
            "-v",
            "--verbose",
            is_flag=True,
            help="Verbose output",
        )
        def track(schema: str, exclude: tuple, verbose: bool) -> None:
            """Auto-discover and track tables in Hasura.

            Discovers all tables in the specified schema and tracks them in Hasura,
            optionally excluding specific tables. Prints a summary of successfully
            tracked tables.

            Args:
                schema: Schema name to discover tables from (default: "api").
                exclude: Tuple of table names to exclude from tracking.
                verbose: Enable verbose output showing per-table progress.

            Raises:
                click.ClickException: If an error occurs during tracking.

            Example:
                $ phlo hasura track --schema api
                $ phlo hasura track --schema marts --exclude staging_table --verbose

            """
            try:
                exclude_list = list(exclude) if exclude else None

                tracker = HasuraTableTracker()
                results = tracker.track_tables(
                    schema,
                    exclude=exclude_list,
                    verbose=verbose,
                )

                tracked = sum(1 for v in results.values() if v)
                total = len(results)

                if verbose:
                    click.echo()
                click.echo(f"Tracked {tracked}/{total} tables")

            except Exception as e:
                _log_error_and_raise(
                    e, {"schema": schema, "exclude_count": len(exclude), "verbose": verbose}, str(e)
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Schema name to discover tables from (default: "api").
        </PyParameter>

        <PyParameter name="&#x22;exclude&#x22;" type="&#x22;tuple&#x22;" value="undefined">
          Tuple of table names to exclude from tracking.
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Enable verbose output showing per-table progress.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;relationships&#x22;" type="&#x22;(schema, verbose) -> None&#x22;">
      Auto-create relationships from foreign keys.

      Analyzes foreign key constraints in the specified schema and automatically
      creates object relationships (many-to-one) in Hasura metadata.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo hasura relationships --schema api
        $ phlo hasura relationships --schema marts --verbose
      </Callout>

      <PySourceCode>
        ```python
        @hasura.command()
        @click.option(
            "--schema",
            default="api",
            help="Schema to set up relationships for (default: api)",
        )
        @click.option(
            "-v",
            "--verbose",
            is_flag=True,
            help="Verbose output",
        )
        def relationships(schema: str, verbose: bool) -> None:
            """Auto-create relationships from foreign keys.

            Analyzes foreign key constraints in the specified schema and automatically
            creates object relationships (many-to-one) in Hasura metadata.

            Args:
                schema: Schema name to analyze foreign keys in (default: "api").
                verbose: Enable verbose output showing per-relationship progress.

            Raises:
                click.ClickException: If an error occurs during relationship creation.

            Example:
                $ phlo hasura relationships --schema api
                $ phlo hasura relationships --schema marts --verbose

            """
            try:
                tracker = HasuraTableTracker()
                results = tracker.setup_relationships(schema, verbose=verbose)

                successful = sum(1 for v in results.values() if v)
                total = len(results)

                if verbose:
                    click.echo()
                click.echo(f"Created {successful}/{total} relationships")

            except Exception as e:
                _log_error_and_raise(e, {"schema": schema, "verbose": verbose}, str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Schema name to analyze foreign keys in (default: "api").
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Enable verbose output showing per-relationship progress.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;permissions&#x22;" type="&#x22;(schema, verbose) -> None&#x22;">
      Set up default permissions for tracked tables.

      Creates default SELECT permissions for standard roles (anon, analyst, admin)
      on all tracked tables in the specified schema.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo hasura permissions --schema api
        $ phlo hasura permissions --schema marts --verbose
      </Callout>

      <PySourceCode>
        ```python
        @hasura.command()
        @click.option(
            "--schema",
            default="api",
            help="Schema to set up permissions for (default: api)",
        )
        @click.option(
            "-v",
            "--verbose",
            is_flag=True,
            help="Verbose output",
        )
        def permissions(schema: str, verbose: bool) -> None:
            """Set up default permissions for tracked tables.

            Creates default SELECT permissions for standard roles (anon, analyst, admin)
            on all tracked tables in the specified schema.

            Args:
                schema: Schema name to configure permissions for (default: "api").
                verbose: Enable verbose output showing per-permission progress.

            Raises:
                click.ClickException: If an error occurs during permission setup.

            Example:
                $ phlo hasura permissions --schema api
                $ phlo hasura permissions --schema marts --verbose

            """
            try:
                tracker = HasuraTableTracker()
                results = tracker.setup_default_permissions(schema, verbose=verbose)

                successful = sum(1 for v in results.values() if v)
                total = len(results)

                if verbose:
                    click.echo()
                click.echo(f"Created {successful}/{total} permissions")

            except Exception as e:
                _log_error_and_raise(e, {"schema": schema, "verbose": verbose}, str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Schema name to configure permissions for (default: "api").
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Enable verbose output showing per-permission progress.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;auto_setup&#x22;" type="&#x22;(schema, verbose) -> None&#x22;">
      Auto-track tables, set up relationships and permissions.

      Complete auto-configuration that runs track, relationships, and permissions
      in sequence for the specified schema. Provides a one-command setup for
      new schemas.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo hasura auto-setup --schema api
        $ phlo hasura auto-setup --schema marts --verbose
      </Callout>

      <PySourceCode>
        ```python
        @hasura.command()
        @click.option(
            "--schema",
            default="api",
            help="Schema to auto-track (default: api)",
        )
        @click.option(
            "-v",
            "--verbose",
            is_flag=True,
            help="Verbose output",
        )
        def auto_setup(schema: str, verbose: bool) -> None:
            """Auto-track tables, set up relationships and permissions.

            Complete auto-configuration that runs track, relationships, and permissions
            in sequence for the specified schema. Provides a one-command setup for
            new schemas.

            Args:
                schema: Schema name to auto-configure (default: "api").
                verbose: Enable verbose output showing all operations.

            Raises:
                click.ClickException: If an error occurs during any step.

            Example:
                $ phlo hasura auto-setup --schema api
                $ phlo hasura auto-setup --schema marts --verbose

            """
            try:
                auto_track(schema, verbose=verbose)
            except Exception as e:
                _log_error_and_raise(e, {"schema": schema, "verbose": verbose}, str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Schema name to auto-configure (default: "api").
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Enable verbose output showing all operations.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;export&#x22;" type="&#x22;(output) -> None&#x22;">
      Export current Hasura metadata to file.

      Exports the complete Hasura metadata (including tracked tables,
      relationships, and permissions) to a JSON file.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo hasura export --output hasura\_metadata.json
      </Callout>

      <PySourceCode>
        ```python
        @hasura.command()
        @click.option(
            "--output",
            type=click.Path(),
            required=True,
            help="Output file path for metadata",
        )
        def export(output: str) -> None:
            """Export current Hasura metadata to file.

            Exports the complete Hasura metadata (including tracked tables,
            relationships, and permissions) to a JSON file.

            Args:
                output: Path to save the exported metadata JSON file.

            Raises:
                click.ClickException: If an error occurs during export.

            Example:
                $ phlo hasura export --output hasura_metadata.json

            """
            try:
                syncer = HasuraMetadataSync()
                syncer.export_metadata(output)
                click.echo(f"Metadata exported to {output}")
            except Exception as e:
                _log_error_and_raise(e, {"output_path": output}, str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output&#x22;" type="&#x22;str&#x22;" value="undefined">
          Path to save the exported metadata JSON file.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;apply_meta&#x22;" type="&#x22;(input) -> None&#x22;">
      Apply Hasura metadata from file.

      Imports and applies Hasura metadata from a previously exported JSON file.
      This will replace the current metadata with the contents of the file.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo hasura apply --input hasura\_metadata.json
      </Callout>

      <PySourceCode>
        ```python
        @hasura.command(name="apply")
        @click.option(
            "--input",
            type=click.Path(exists=True),
            required=True,
            help="Input metadata file",
        )
        def apply_meta(input: str) -> None:
            """Apply Hasura metadata from file.

            Imports and applies Hasura metadata from a previously exported JSON file.
            This will replace the current metadata with the contents of the file.

            Args:
                input: Path to the metadata JSON file to import.

            Raises:
                click.ClickException: If the file doesn't exist or import fails.

            Example:
                $ phlo hasura apply --input hasura_metadata.json

            """
            try:
                syncer = HasuraMetadataSync()
                syncer.import_metadata(input)
                click.echo(f"Metadata applied from {input}")
            except Exception as e:
                _log_error_and_raise(e, {"input_path": input}, str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;input&#x22;" type="&#x22;str&#x22;" value="undefined">
          Path to the metadata JSON file to import.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;status&#x22;" type="&#x22;() -> None&#x22;">
      Show Hasura tracking status.

      Displays a summary of all tracked tables organized by schema,
      showing which tables are currently configured in Hasura metadata.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo hasura status
      </Callout>

      <PySourceCode>
        ```python
        @hasura.command()
        def status() -> None:
            """Show Hasura tracking status.

            Displays a summary of all tracked tables organized by schema,
            showing which tables are currently configured in Hasura metadata.

            Raises:
                click.ClickException: If an error occurs fetching status.

            Example:
                $ phlo hasura status

            """
            try:
                client = HasuraClient()
                tracked = client.get_tracked_tables()

                click.echo("Tracked tables by schema:")
                click.echo()

                for schema in sorted(tracked.keys()):
                    tables = tracked[schema]
                    click.echo(f"  {schema}: {len(tables)} tables")
                    for table in sorted(tables):
                        click.echo(f"    - {table}")

            except Exception as e:
                _log_error_and_raise(e, {}, str(e))
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;sync_permissions&#x22;" type="&#x22;(config) -> None&#x22;">
      Sync permissions from config file.

      Applies permission configurations from a YAML or JSON file to Hasura.
      The config file should define tables, roles, and their respective
      SELECT/INSERT/UPDATE/DELETE permissions.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        $ phlo hasura sync-permissions --config permissions.yaml
      </Callout>

      <PySourceCode>
        ```python
        @hasura.command(name="sync-permissions")
        @click.option(
            "--config",
            type=click.Path(exists=True),
            required=True,
            help="Permission config file (JSON/YAML)",
        )
        def sync_permissions(config: str) -> None:
            """Sync permissions from config file.

            Applies permission configurations from a YAML or JSON file to Hasura.
            The config file should define tables, roles, and their respective
            SELECT/INSERT/UPDATE/DELETE permissions.

            Args:
                config: Path to the permission configuration file (YAML or JSON).

            Raises:
                click.ClickException: If the file doesn't exist or sync fails.

            Example:
                $ phlo hasura sync-permissions --config permissions.yaml

            """
            try:
                manager = HasuraPermissionManager()
                config_dict = manager.load_config(config)
                manager.sync_permissions(config_dict, verbose=True)
                click.echo("Permissions synced")
            except Exception as e:
                _log_error_and_raise(e, {"config_path": config}, str(e))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config&#x22;" type="&#x22;str&#x22;" value="undefined">
          Path to the permission configuration file (YAML or JSON).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
