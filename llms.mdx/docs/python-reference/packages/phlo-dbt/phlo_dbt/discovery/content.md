# discovery (/docs/python-reference/packages/phlo-dbt/phlo_dbt/discovery)



dbt project discovery for auto-wiring.

This module provides utilities for automatically discovering dbt projects
within the workspace. It searches common locations and environment variables
to locate dbt\_project.yml files, enabling zero-configuration setup in many cases.

Example:

> > > from phlo\_dbt.discovery import find\_dbt\_projects, get\_dbt\_project\_dir
> > >
> > > Find all dbt projects in workspace [#find-all-dbt-projects-in-workspace]
> > >
> > > projects = find\_dbt\_projects()
> > > for project in projects:
> > > ...     print(f"Found: \{project}")
> > >
> > > Get the primary project directory [#get-the-primary-project-directory]
> > >
> > > project\_dir = get\_dbt\_project\_dir()
> > > print(f"Using: \{project\_dir}")

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;DEFAULT_SEARCH_PATHS&#x22;" type="null" value="&#x22;['workflows/transforms/dbt']&#x22;" />

<PyAttribute name="&#x22;projects&#x22;" type="null" value="&#x22;find_dbt_projects()&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;find_dbt_projects&#x22;" type="&#x22;(root_dir=None, search_paths=None) -> list[Path]&#x22;">
      Discover dbt projects in the workspace.

      Searches for dbt\_project.yml files in specified paths relative to the root
      directory. Returns paths to directories containing valid dbt projects.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > Find projects in default locations [#find-projects-in-default-locations]
        > > >
        > > > projects = find\_dbt\_projects()
        > > > print(projects)
        > > > \[PosixPath('workflows/transforms/dbt')]
        > > >
        > > > Search custom locations [#search-custom-locations]
        > > >
        > > > projects = find\_dbt\_projects(
        > > > ...     root\_dir="/custom/path",
        > > > ...     search\_paths=\["analytics/dbt", "data/transforms"]
        > > > ... )
      </Callout>

      <PySourceCode>
        ```python
        def find_dbt_projects(
            root_dir: str | Path | None = None,
            search_paths: list[str] | None = None,
        ) -> list[Path]:
            """Discover dbt projects in the workspace.

            Searches for dbt_project.yml files in specified paths relative to the root
            directory. Returns paths to directories containing valid dbt projects.

            Args:
                root_dir: Root directory to search from. Defaults to current working directory.
                search_paths: List of relative paths to search. Defaults to DEFAULT_SEARCH_PATHS.

            Returns:
                List of paths to discovered dbt project directories (parent directories
                of dbt_project.yml files).

            Example:
                >>> # Find projects in default locations
                >>> projects = find_dbt_projects()
                >>> print(projects)
                [PosixPath('workflows/transforms/dbt')]
                >>>
                >>> # Search custom locations
                >>> projects = find_dbt_projects(
                ...     root_dir="/custom/path",
                ...     search_paths=["analytics/dbt", "data/transforms"]
                ... )

            """
            if root_dir is None:
                root_dir = Path.cwd()
            else:
                root_dir = Path(root_dir)

            if search_paths is None:
                search_paths = DEFAULT_SEARCH_PATHS

            discovered = []

            for search_path in search_paths:
                candidate = root_dir / search_path / "dbt_project.yml"
                if candidate.exists():
                    discovered.append(candidate.parent)
                    logger.info("Discovered dbt project: %s", candidate.parent)

            return discovered
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;root_dir&#x22;" type="&#x22;str | Path | None&#x22;" value="&#x22;None&#x22;">
          Root directory to search from. Defaults to current working directory.
        </PyParameter>

        <PyParameter name="&#x22;search_paths&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
          List of relative paths to search. Defaults to DEFAULT\_SEARCH\_PATHS.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of paths to discovered dbt project directories (parent directories
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_dbt_project_dir&#x22;" type="&#x22;() -> Path&#x22;">
      Get the dbt project directory, auto-discovering if not explicitly set.

      Resolves the dbt project directory using a priority system:

      1. DBT\_PROJECT\_DIR environment variable
      2. Auto-discovered project in workspace
      3. Default: workflows/transforms/dbt

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > With environment variable set [#with-environment-variable-set]
        > > >
        > > > import os
        > > > os.environ\["DBT\_PROJECT\_DIR"] = "/custom/dbt"
        > > > project\_dir = get\_dbt\_project\_dir()
        > > > print(project\_dir)
        > > > PosixPath('/custom/dbt')
        > > >
        > > > With auto-discovery [#with-auto-discovery]
        > > >
        > > > project\_dir = get\_dbt\_project\_dir()
        > > >
        > > > Returns first discovered project or default path [#returns-first-discovered-project-or-default-path]
      </Callout>

      <PySourceCode>
        ```python
        def get_dbt_project_dir() -> Path:
            """Get the dbt project directory, auto-discovering if not explicitly set.

            Resolves the dbt project directory using a priority system:
            1. DBT_PROJECT_DIR environment variable
            2. Auto-discovered project in workspace
            3. Default: workflows/transforms/dbt

            Returns:
                Path to dbt project directory. May not exist if falling back to default
                and project hasn't been scaffolded yet.

            Example:
                >>> # With environment variable set
                >>> import os
                >>> os.environ["DBT_PROJECT_DIR"] = "/custom/dbt"
                >>> project_dir = get_dbt_project_dir()
                >>> print(project_dir)
                PosixPath('/custom/dbt')
                >>>
                >>> # With auto-discovery
                >>> project_dir = get_dbt_project_dir()
                >>> # Returns first discovered project or default path

            """
            # Check explicit environment variable
            env_path = os.environ.get("DBT_PROJECT_DIR")
            if env_path:
                return Path(env_path)

            # Auto-discover
            projects = find_dbt_projects()
            if projects:
                return projects[0]

            # Fall back to default
            return Path("workflows/transforms/dbt")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Path to dbt project directory. May not exist if falling back to default
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
