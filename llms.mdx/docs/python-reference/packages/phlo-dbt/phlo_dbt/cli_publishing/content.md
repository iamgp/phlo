# cli_publishing (/docs/python-reference/packages/phlo-dbt/phlo_dbt/cli_publishing)



Publishing configuration scaffolding.

Generates `publishing.yaml` entries from a dbt manifest.

This module provides utilities to scaffold and manage publishing configuration
for dbt models. It extracts model metadata from dbt manifests and generates
configuration for publishing data to downstream systems like Postgres.

Example:

> > > Via CLI: [#via-cli]
> > >
> > > phlo dbt publishing scaffold --select mrt_* --output publishing.yaml [#phlo-dbt-publishing-scaffold---select-mrt_---output-publishingyaml]
> > >
> > > Programmatically: [#programmatically]
> > >
> > > from phlo\_dbt.cli\_publishing import scaffold\_publishing\_config
> > > config = scaffold\_publishing\_config(
> > > ...     existing\_config=\{},
> > > ...     model\_names=\["mrt\_orders", "mrt\_customers"],
> > > ...     source\_key="analytics",
> > > ...     iceberg\_schema="marts",
> > > ...     group="publishing",
> > > ...     asset\_name="publish\_analytics\_marts",
> > > ...     description="Published analytics marts"
> > > ... )

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_normalize_select_patterns&#x22;" type="&#x22;(select) -> list[str]&#x22;">
      Normalize CLI selection values into glob patterns.

      <PySourceCode>
        ```python
        def _normalize_select_patterns(select: Iterable[str]) -> list[str]:
            """Normalize CLI selection values into glob patterns.

            Args:
                select: Raw ``--select`` values.

            Returns:
                Flattened, trimmed pattern list.

            """
            patterns: list[str] = []
            for raw in select:
                for part in raw.split(","):
                    part = part.strip()
                    if part:
                        patterns.append(part)
            return patterns
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;select&#x22;" type="&#x22;Iterable[str]&#x22;" value="undefined">
          Raw `--select` values.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Flattened, trimmed pattern list.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_select_models&#x22;" type="&#x22;(model_names, patterns) -> list[str]&#x22;">
      Filter model names using glob patterns.

      <PySourceCode>
        ```python
        def _select_models(model_names: list[str], patterns: list[str]) -> list[str]:
            """Filter model names using glob patterns.

            Args:
                model_names: Available model names.
                patterns: Glob patterns to match.

            Returns:
                Selected model names preserving input order.

            """
            if not patterns:
                return model_names

            selected: list[str] = []
            for name in model_names:
                if any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns):
                    selected.append(name)
            return selected
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;model_names&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          Available model names.
        </PyParameter>

        <PyParameter name="&#x22;patterns&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          Glob patterns to match.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Selected model names preserving input order.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_load_yaml&#x22;" type="&#x22;(path) -> dict[str, Any]&#x22;">
      Load a YAML mapping from disk.

      <PySourceCode>
        ```python
        def _load_yaml(path: Path) -> dict[str, Any]:
            """Load a YAML mapping from disk.

            Args:
                path: YAML file path.

            Returns:
                Parsed mapping, or an empty mapping if file is missing.

            Raises:
                ValueError: If root YAML value is not a mapping.

            """
            if not path.exists():
                return {}
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                raise ValueError(f"Expected YAML mapping at root in {path}")
            return data
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          YAML file path.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Parsed mapping, or an empty mapping if file is missing.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_dump_yaml&#x22;" type="&#x22;(data) -> str&#x22;">
      Serialize configuration mapping to YAML text.

      <PySourceCode>
        ```python
        def _dump_yaml(data: dict[str, Any]) -> str:
            """Serialize configuration mapping to YAML text.

            Args:
                data: Mapping to serialize.

            Returns:
                YAML string.

            """
            return yaml.safe_dump(data, sort_keys=False)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Mapping to serialize.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        YAML string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_load_manifest_models&#x22;" type="&#x22;(manifest_path) -> dict[str, dict[str, Any]]&#x22;">
      Load dbt models from a manifest file.

      <PySourceCode>
        ```python
        def _load_manifest_models(manifest_path: Path) -> dict[str, dict[str, Any]]:
            """Load dbt models from a manifest file.

            Args:
                manifest_path: Path to ``manifest.json``.

            Returns:
                Model metadata keyed by model name.

            Raises:
                click.ClickException: If file read or JSON parsing fails.

            """
            try:
                manifest = json.loads(manifest_path.read_text())
            except OSError as e:
                logger.exception("dbt_publishing_manifest_read_failed", manifest_path=str(manifest_path))
                raise click.ClickException(f"Failed to read manifest: {manifest_path} ({e})") from e
            except json.JSONDecodeError as e:
                logger.exception("dbt_publishing_manifest_invalid_json", manifest_path=str(manifest_path))
                raise click.ClickException(f"Invalid JSON in manifest: {manifest_path} ({e})") from e

            models: dict[str, dict[str, Any]] = {}
            for unique_id, node in (manifest.get("nodes") or {}).items():
                if not isinstance(unique_id, str) or not unique_id.startswith("model."):
                    continue
                if not isinstance(node, dict):
                    continue
                name = node.get("name")
                if isinstance(name, str) and name:
                    models[name] = node
            return models
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;manifest_path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to `manifest.json`.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Model metadata keyed by model name.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;scaffold_publishing_config&#x22;" type="&#x22;(*, existing_config, model_names, source_key, iceberg_schema, group, asset_name, description) -> dict[str, Any]&#x22;">
      Merge scaffolded publishing config into an existing mapping.

      <PySourceCode>
        ```python
        def scaffold_publishing_config(
            *,
            existing_config: dict[str, Any],
            model_names: list[str],
            source_key: str,
            iceberg_schema: str,
            group: str,
            asset_name: str,
            description: str,
        ) -> dict[str, Any]:
            """Merge scaffolded publishing config into an existing mapping.

            Args:
                existing_config: Existing publishing configuration.
                model_names: dbt model names to include.
                source_key: Source key under ``publishing``.
                iceberg_schema: Iceberg schema for table mapping values.
                group: Dagster group name for generated entry.
                asset_name: Asset name for generated entry.
                description: Human-readable entry description.

            Returns:
                Updated publishing configuration mapping.

            Raises:
                ValueError: If existing config shape is invalid.

            """
            config: dict[str, Any] = dict(existing_config)
            publishing = config.get("publishing", {})
            if publishing is None:
                publishing = {}
            if not isinstance(publishing, dict):
                raise ValueError("Expected `publishing` to be a mapping in publishing.yaml")

            existing_entry = publishing.get(source_key, {}) or {}
            if not isinstance(existing_entry, dict):
                raise ValueError(f"Expected publishing.{source_key} to be a mapping in publishing.yaml")

            entry: dict[str, Any] = dict(existing_entry)
            entry.setdefault("name", asset_name)
            entry.setdefault("group", group)
            entry.setdefault("description", description)

            tables_existing = entry.get("tables", {}) or {}
            if not isinstance(tables_existing, dict):
                raise ValueError(f"Expected publishing.{source_key}.tables to be a mapping")

            tables: dict[str, str] = {str(k): str(v) for k, v in tables_existing.items()}
            for model_name in model_names:
                tables.setdefault(model_name, f"{iceberg_schema}.{model_name}")
            entry["tables"] = tables

            deps_existing = entry.get("dependencies", []) or []
            if not isinstance(deps_existing, list):
                raise ValueError(f"Expected publishing.{source_key}.dependencies to be a list")
            dependencies = [str(dep) for dep in deps_existing]
            for model_name in model_names:
                if model_name not in dependencies:
                    dependencies.append(model_name)
            entry["dependencies"] = dependencies

            publishing[source_key] = entry
            config["publishing"] = publishing
            return config
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;existing_config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Existing publishing configuration.
        </PyParameter>

        <PyParameter name="&#x22;model_names&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          dbt model names to include.
        </PyParameter>

        <PyParameter name="&#x22;source_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source key under `publishing`.
        </PyParameter>

        <PyParameter name="&#x22;iceberg_schema&#x22;" type="&#x22;str&#x22;" value="undefined">
          Iceberg schema for table mapping values.
        </PyParameter>

        <PyParameter name="&#x22;group&#x22;" type="&#x22;str&#x22;" value="undefined">
          Dagster group name for generated entry.
        </PyParameter>

        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset name for generated entry.
        </PyParameter>

        <PyParameter name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="undefined">
          Human-readable entry description.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Updated publishing configuration mapping.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;publishing&#x22;" type="&#x22;()&#x22;">
      Manage publishing configuration.

      <PySourceCode>
        ```python
        @click.group()
        def publishing():
            """Manage publishing configuration."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;scaffold_cmd&#x22;" type="&#x22;(manifest, output, select_patterns, source_key, iceberg_schema, group, asset_name, dry_run)&#x22;">
      Scaffold `publishing.yaml` from a dbt manifest.

      Idempotent: re-running preserves existing config and only adds missing tables/dependencies.

      <PySourceCode>
        ```python
        @publishing.command("scaffold")
        @click.option(
            "--manifest",
            type=click.Path(dir_okay=False, path_type=Path),
            help="Path to dbt manifest.json (default: from settings)",
        )
        @click.option(
            "--output",
            type=click.Path(dir_okay=False, path_type=Path),
            default=Path("publishing.yaml"),
            show_default=True,
            help="Path to write publishing.yaml",
        )
        @click.option(
            "--select",
            "select_patterns",
            multiple=True,
            default=("mrt_*",),
            show_default=True,
            help="Model name glob(s) to include (comma-separated allowed)",
        )
        @click.option(
            "--source",
            "source_key",
            default=None,
            help="publishing.<source> key to write under (default: project name)",
        )
        @click.option(
            "--iceberg-schema",
            default="marts",
            show_default=True,
            help="Iceberg schema to reference in tables mapping",
        )
        @click.option(
            "--group",
            default="publishing",
            show_default=True,
            help="Dagster group_name for the publishing asset",
        )
        @click.option(
            "--asset-name",
            default=None,
            help="Dagster asset name to generate (default: publish_<source>_marts)",
        )
        @click.option(
            "--dry-run",
            is_flag=True,
            help="Print YAML to stdout instead of writing output file",
        )
        def scaffold_cmd(
            manifest: Path | None,
            output: Path,
            select_patterns: tuple[str, ...],
            source_key: str | None,
            iceberg_schema: str,
            group: str,
            asset_name: str | None,
            dry_run: bool,
        ):
            """Scaffold `publishing.yaml` from a dbt manifest.

            Idempotent: re-running preserves existing config and only adds missing tables/dependencies.
            """
            manifest_path = manifest or Path(get_settings().dbt_manifest_path)
            logger.info(
                "dbt_publishing_scaffold_started",
                manifest_path=str(manifest_path),
                output_path=str(output),
                dry_run=dry_run,
                select_patterns=list(select_patterns),
            )
            if not manifest_path.is_absolute():
                manifest_path = (Path.cwd() / manifest_path).resolve()
            if not manifest_path.exists():
                logger.warning(
                    "dbt_publishing_manifest_missing",
                    manifest_path=str(manifest_path),
                )
                raise click.ClickException(f"dbt manifest not found at {manifest_path}")

            models = _load_manifest_models(manifest_path)
            all_model_names = sorted(models.keys())

            patterns = _normalize_select_patterns(select_patterns)
            selected_model_names = _select_models(all_model_names, patterns)
            if not selected_model_names:
                logger.warning(
                    "dbt_publishing_no_models_selected",
                    manifest_path=str(manifest_path),
                    patterns=patterns,
                    available_model_count=len(all_model_names),
                )
                raise click.ClickException(f"No models matched selection: {', '.join(patterns)}")

            resolved_source_key = source_key or get_project_name()
            resolved_asset_name = asset_name or f"publish_{resolved_source_key}_marts"
            resolved_description = (
                f"Publish {len(selected_model_names)} dbt marts to Postgres via Trino (scaffolded)."
            )

            existing_config = _load_yaml(output)
            updated_config = scaffold_publishing_config(
                existing_config=existing_config,
                model_names=selected_model_names,
                source_key=resolved_source_key,
                iceberg_schema=iceberg_schema,
                group=group,
                asset_name=resolved_asset_name,
                description=resolved_description,
            )

            rendered = _dump_yaml(updated_config)
            if dry_run:
                logger.info(
                    "dbt_publishing_scaffold_rendered",
                    source_key=resolved_source_key,
                    selected_model_count=len(selected_model_names),
                    output_mode="stdout",
                )
                click.echo(rendered)
                return

            output.write_text(rendered)
            logger.info(
                "dbt_publishing_scaffold_written",
                source_key=resolved_source_key,
                selected_model_count=len(selected_model_names),
                output_path=str(output),
            )
            click.echo(f"Wrote {output}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;manifest&#x22;" type="&#x22;Path | None&#x22;" value="null" />

        <PyParameter name="&#x22;output&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;select_patterns&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />

        <PyParameter name="&#x22;source_key&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;iceberg_schema&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;group&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;dry_run&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
