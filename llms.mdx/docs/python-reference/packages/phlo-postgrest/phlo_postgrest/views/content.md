# views (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views)



PostgREST API view generation from dbt models.

This module automates the generation of PostgREST-compatible API views from
dbt models. It parses dbt's manifest.json, generates CREATE VIEW statements,
manages database permissions based on dbt tags, and provides tools for
applying or diffing view changes.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PostgrestViewsSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/PostgrestViewsSettings&#x22;" />

      <Card title="&#x22;DbtModel&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/DbtModel&#x22;" />

      <Card title="&#x22;DbtManifestParser&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/DbtManifestParser&#x22;" />

      <Card title="&#x22;ViewGenerator&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/ViewGenerator&#x22;" />

      <Card title="&#x22;PostgreSTViewManager&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/PostgreSTViewManager&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;generate_views&#x22;" type="&#x22;(output=None, apply=False, diff=False, models=None, manifest_path=None, api_schema='api', source_schema=None, verbose=True) -> str&#x22;">
      Generate PostgREST API views from dbt models.

      Main entry point for view generation workflow. Orchestrates parsing
      the dbt manifest, generating SQL, and optionally applying to database or
      showing diffs.

      Supports three output modes:

      * Default: Return SQL string
      * output: Write SQL to file
      * apply: Execute SQL directly against database
      * diff: Show comparison with existing views

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > Generate SQL to stdout [#generate-sql-to-stdout]
        > > >
        > > > sql = generate\_views()

        > > > Apply directly to database [#apply-directly-to-database]
        > > >
        > > > result = generate\_views(apply=True, models="mrt\_\*")
        > > > print(result)
        > > > Views applied successfully

        > > > Show what's changing [#show-whats-changing]
        > > >
        > > > diff = generate\_views(diff=True)
        > > > print(diff)
      </Callout>

      <PySourceCode>
        ```python
        def generate_views(
            output: Optional[str] = None,
            apply: bool = False,
            diff: bool = False,
            models: Optional[str] = None,
            manifest_path: Optional[str] = None,
            api_schema: str = "api",
            source_schema: Optional[str] = None,
            verbose: bool = True,
        ) -> str:
            """Generate PostgREST API views from dbt models.

                Main entry point for view generation workflow. Orchestrates parsing
            the dbt manifest, generating SQL, and optionally applying to database or
            showing diffs.

                Supports three output modes:
                    - Default: Return SQL string
                    - output: Write SQL to file
                    - apply: Execute SQL directly against database
                    - diff: Show comparison with existing views

            Args:
                    output: File path to write SQL (default: return string).
                    apply: Execute SQL against database if True.
                    diff: Show diff summary instead of SQL.
                    models: Glob pattern to filter models (e.g., 'mrt_*').
                    manifest_path: Path to dbt manifest.json.
                    api_schema: Target schema for views (default: 'api').
                    source_schema: Source dbt schema to expose.
                    verbose: Enable progress logging.

            Returns:
                    str: Generated SQL, diff summary, or status message depending on mode.
                    Returns empty string if no models match filter.

            Raises:
                    Exception: If database operations fail when apply=True.

            Example:
                    >>> # Generate SQL to stdout
                    >>> sql = generate_views()

                    >>> # Apply directly to database
                    >>> result = generate_views(apply=True, models="mrt_*")
                    >>> print(result)
                    Views applied successfully

                    >>> # Show what's changing
                    >>> diff = generate_views(diff=True)
                    >>> print(diff)

            """
            if verbose:
                logger.info("=" * 60)
                logger.info("PostgREST API View Generation")
                logger.info("=" * 60)

            # Generate SQL
            generator = ViewGenerator(manifest_path, api_schema, source_schema=source_schema)
            sql = generator.generate_all_views(models)

            if not sql:
                if verbose:
                    logger.info("No models found matching filter")
                return ""

            if verbose:
                logger.info("Generated SQL for %s characters", len(sql))

            # Handle diff
            if diff:
                manager = PostgreSTViewManager()
                diff_output = manager.generate_diff(sql, api_schema)
                if verbose:
                    logger.info("\n%s", diff_output)
                return diff_output

            # Handle apply
            if apply:
                if verbose:
                    logger.info("Applying to database...")
                view_names = sorted(
                    set(re.findall(rf"CREATE OR REPLACE VIEW {re.escape(api_schema)}\.(\w+)", sql))
                )
                logger.info(
                    "postgrest_view_apply_started",
                    schema=api_schema,
                    view_count=len(view_names),
                    view_names=view_names,
                )
                manager = PostgreSTViewManager()
                try:
                    manager.execute_sql(sql, verbose=verbose)
                except Exception:
                    logger.exception(
                        "postgrest_view_apply_failed",
                        schema=api_schema,
                        view_count=len(view_names),
                        view_names=view_names,
                    )
                    raise
                logger.info(
                    "postgrest_view_apply_succeeded",
                    schema=api_schema,
                    view_count=len(view_names),
                    view_names=view_names,
                )
                return "Views applied successfully"

            # Handle output file
            if output:
                output_path = Path(output)
                output_path.write_text(sql)
                if verbose:
                    logger.info("✓ SQL written to %s", output)
                return f"SQL written to {output}"

            # Default: print to stdout
            return sql
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          File path to write SQL (default: return string).
        </PyParameter>

        <PyParameter name="&#x22;apply&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
          Execute SQL against database if True.
        </PyParameter>

        <PyParameter name="&#x22;diff&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
          Show diff summary instead of SQL.
        </PyParameter>

        <PyParameter name="&#x22;models&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Glob pattern to filter models (e.g., 'mrt\_\*').
        </PyParameter>

        <PyParameter name="&#x22;manifest_path&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Path to dbt manifest.json.
        </PyParameter>

        <PyParameter name="&#x22;api_schema&#x22;" type="&#x22;str&#x22;" value="&#x22;'api'&#x22;">
          Target schema for views (default: 'api').
        </PyParameter>

        <PyParameter name="&#x22;source_schema&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Source dbt schema to expose.
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Enable progress logging.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Generated SQL, diff summary, or status message depending on mode.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
