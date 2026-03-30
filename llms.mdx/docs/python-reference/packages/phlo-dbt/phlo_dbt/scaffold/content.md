# scaffold (/docs/python-reference/packages/phlo-dbt/phlo_dbt/scaffold)



Project scaffold helpers for dbt assets.

This module provides utilities for scaffolding new dbt projects with
Phlo-compatible configuration. It generates dbt\_project.yml files with
appropriate settings and SQLFluff configuration for linting.

Example:

> > > from phlo\_dbt.scaffold import write\_dbt\_scaffold
> > > from pathlib import Path
> > > write\_dbt\_scaffold(
> > > ...     project\_name="analytics",
> > > ...     transforms\_dir=Path("workflows/transforms/dbt"),
> > > ...     project\_dir=Path(".")
> > > ... )

Creates dbt_project.yml and .sqlfluff configuration files [#creates-dbt_projectyml-and-sqlfluff-configuration-files]

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;build_dbt_project&#x22;" type="&#x22;(project_name) -> str&#x22;">
      Build dbt\_project.yml content for a scaffolded project.

      Generates a standard dbt\_project.yml configuration with Phlo-compatible
      defaults, including proper paths, materialization settings, and SSL flags.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > content = build\_dbt\_project("my-analytics")
        > > > print(content)
        > > > name: my\_analytics
        > > > version: 1.0.0
        > > > ...

        > > > Write to file [#write-to-file]
        > > >
        > > > Path("dbt\_project.yml").write\_text(content)
      </Callout>

      <PySourceCode>
        ```python
        def build_dbt_project(project_name: str) -> str:
            """Build dbt_project.yml content for a scaffolded project.

            Generates a standard dbt_project.yml configuration with Phlo-compatible
            defaults, including proper paths, materialization settings, and SSL flags.

            Args:
                project_name: User-provided project name. Will be sanitized (hyphens
                    converted to underscores) for use in dbt configuration.

            Returns:
                dbt project YAML content as a string, ready to write to dbt_project.yml.

            Example:
                >>> content = build_dbt_project("my-analytics")
                >>> print(content)
                name: my_analytics
                version: 1.0.0
                ...

                >>> # Write to file
                >>> Path("dbt_project.yml").write_text(content)

            """
            safe_name = project_name.replace("-", "_")
            return f"""name: {safe_name}
        version: 1.0.0
        config-version: 2

        profile: phlo

        model-paths: ["models"]
        seed-paths: ["seeds"]

        # Opt into new SSL behavior to suppress trino-dbt SSL warning
        flags:
          require_certificate_validation: true

        models:
          {safe_name}:
            +materialized: table
        """
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          User-provided project name. Will be sanitized (hyphens
          converted to underscores) for use in dbt configuration.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        dbt project YAML content as a string, ready to write to dbt\_project.yml.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;build_sqlfluff_config&#x22;" type="&#x22;() -> str&#x22;">
      Build SQLFluff configuration content for Trino + dbt templating.

      Generates a comprehensive SQLFluff configuration optimized for dbt projects
      using Trino as the query engine. Includes settings for Jinja templating,
      indentation, capitalization, and aliasing rules.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > config = build\_sqlfluff\_config()
        > > > Path(".sqlfluff").write\_text(config)
        > > >
        > > > Now SQLFluff will properly lint your dbt SQL files [#now-sqlfluff-will-properly-lint-your-dbt-sql-files]
      </Callout>

      <PySourceCode>
        ```python
        def build_sqlfluff_config() -> str:
            """Build SQLFluff configuration content for Trino + dbt templating.

            Generates a comprehensive SQLFluff configuration optimized for dbt projects
            using Trino as the query engine. Includes settings for Jinja templating,
            indentation, capitalization, and aliasing rules.

            Returns:
                SQLFluff configuration text as a string, ready to write to .sqlfluff.

            Example:
                >>> config = build_sqlfluff_config()
                >>> Path(".sqlfluff").write_text(config)
                >>> # Now SQLFluff will properly lint your dbt SQL files

            """
            return """[sqlfluff]
        dialect = trino
        templater = jinja
        max_line_length = 120
        # Only exclude keywords-as-identifiers rule (requires column renames)
        exclude_rules = RF04

        [sqlfluff:templater:jinja]
        # Ignore undefined jinja variables in dbt
        ignore = templating

        [sqlfluff:rules]
        # Allow trailing commas
        allow_trailing_commas = True

        [sqlfluff:rules:layout.long_lines]
        # Increase line length limit
        max_line_length = 120

        [sqlfluff:rules:layout.indent]
        # Use 4 spaces for indentation
        indent_unit = space
        tab_space_size = 4

        [sqlfluff:rules:capitalisation.keywords]
        # SQL keywords should be lowercase
        capitalisation_policy = lower

        [sqlfluff:rules:aliasing.table]
        # Table aliases are required
        aliasing = explicit
        """
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;">
        SQLFluff configuration text as a string, ready to write to .sqlfluff.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;write_dbt_scaffold&#x22;" type="&#x22;(project_name, transforms_dir, project_dir) -> None&#x22;">
      Write dbt project and sqlfluff config files for a new project.

      Creates the necessary directory structure and configuration files for a new
      dbt project integrated with Phlo. This includes:

      * dbt\_project.yml in the transforms directory
      * .sqlfluff in the project root for SQL linting

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from pathlib import Path
        > > > write\_dbt\_scaffold(
        > > > ...     "analytics\_project",
        > > > ...     transforms\_dir=Path("workflows/transforms/dbt"),
        > > > ...     project\_dir=Path(".")
        > > > ... )

        Creates: [#creates]

        workflows/transforms/dbt/dbt_project.yml [#workflowstransformsdbtdbt_projectyml]

        .sqlfluff [#sqlfluff]
      </Callout>

      <PySourceCode>
        ```python
        def write_dbt_scaffold(project_name: str, transforms_dir: Path, project_dir: Path) -> None:
            """Write dbt project and sqlfluff config files for a new project.

            Creates the necessary directory structure and configuration files for a new
            dbt project integrated with Phlo. This includes:
            - dbt_project.yml in the transforms directory
            - .sqlfluff in the project root for SQL linting

            Args:
                project_name: Name of the dbt project to create.
                transforms_dir: Directory where dbt_project.yml will be written.
                    Created if it doesn't exist.
                project_dir: Project root directory where .sqlfluff will be written.

            Raises:
                OSError: If directory creation or file writing fails.

            Example:
                >>> from pathlib import Path
                >>> write_dbt_scaffold(
                ...     "analytics_project",
                ...     transforms_dir=Path("workflows/transforms/dbt"),
                ...     project_dir=Path(".")
                ... )
                # Creates:
                #   workflows/transforms/dbt/dbt_project.yml
                #   .sqlfluff

            """
            transforms_dir.mkdir(parents=True, exist_ok=True)

            dbt_project_content = build_dbt_project(project_name)
            (transforms_dir / "dbt_project.yml").write_text(dbt_project_content)

            sqlfluff_content = build_sqlfluff_config()
            (project_dir / ".sqlfluff").write_text(sqlfluff_content)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the dbt project to create.
        </PyParameter>

        <PyParameter name="&#x22;transforms_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Directory where dbt\_project.yml will be written.
          Created if it doesn't exist.
        </PyParameter>

        <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Project root directory where .sqlfluff will be written.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
