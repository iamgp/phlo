# runtime_config (/docs/python-reference/packages/phlo-dbt/phlo_dbt/runtime_config)



Canonical dbt runtime configuration derived from Phlo settings.

This module manages dbt runtime configuration, profile generation, and target
resolution. It bridges Phlo's settings system with dbt's profile format,
enabling seamless integration between the two platforms.

Example:

> > > from phlo\_dbt.runtime\_config import DbtRuntimeConfig, write\_dbt\_profile
> > > config = DbtRuntimeConfig(
> > > ...     target\_name="prod",
> > > ...     catalog="analytics",
> > > ...     schema="marts"
> > > ... )
> > > profile\_path = write\_dbt\_profile(config, Path("/app/profiles"))
> > > print(f"Profile written to: \{profile\_path}")

<PyAttribute name="&#x22;DEFAULT_DBT_TARGET&#x22;" type="null" value="&#x22;'dev'&#x22;" />

<PyAttribute name="&#x22;DBT_QUERY_ENGINE_SUPPORT&#x22;" type="null" value="&#x22;CapabilitySupport(supports_refs=True)&#x22;" />

<PyAttribute name="&#x22;DEFAULT_DBT_PROFILE_NAME&#x22;" type="null" value="&#x22;'phlo'&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DbtRuntimeConfig&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/runtime_config/DbtRuntimeConfig&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_dbt_target_name&#x22;" type="&#x22;(runtime=None, *, target=None) -> str&#x22;">
      Resolve the effective dbt target name from canonical routing.

      Resolution order:

      1. Explicit target argument
      2. Canonical routing environment
      3. Legacy `dbt_target` tag
      4. Default `DEFAULT_DBT_TARGET`

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > target = resolve\_dbt\_target\_name(target="prod")
        > > > print(target)
        > > > prod
        > > >
        > > > With runtime context containing environment [#with-runtime-context-containing-environment]
        > > >
        > > > target = resolve\_dbt\_target\_name(runtime=ctx)
        > > >
        > > > Returns environment name from routing context [#returns-environment-name-from-routing-context]
      </Callout>

      <PySourceCode>
        ```python
        def resolve_dbt_target_name(
            runtime: RuntimeContext | None = None, *, target: str | None = None
        ) -> str:
            """Resolve the effective dbt target name from canonical routing.

            Resolution order:
            1. Explicit target argument
            2. Canonical routing environment
            3. Legacy `dbt_target` tag
            4. Default `DEFAULT_DBT_TARGET`

            Args:
                runtime: Optional runtime context for environment-based resolution.
                target: Optional explicit target name to use (highest priority).

            Returns:
                Resolved dbt target name string.

            Example:
                >>> target = resolve_dbt_target_name(target="prod")
                >>> print(target)
                prod
                >>>
                >>> # With runtime context containing environment
                >>> target = resolve_dbt_target_name(runtime=ctx)
                >>> # Returns environment name from routing context

            """
            if target:
                return target
            if runtime is not None:
                routing = routing_from_context(runtime)
                if routing.environment:
                    return routing.environment
                runtime_tags = getattr(runtime, "tags", {}) or {}
                legacy_target = runtime_tags.get("dbt_target") if isinstance(runtime_tags, dict) else None
                if isinstance(legacy_target, str) and legacy_target:
                    return legacy_target
            return DEFAULT_DBT_TARGET
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="&#x22;None&#x22;">
          Optional runtime context for environment-based resolution.
        </PyParameter>

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional explicit target name to use (highest priority).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Resolved dbt target name string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;resolve_dbt_runtime_config&#x22;" type="&#x22;(runtime=None, *, target=None) -> DbtRuntimeConfig&#x22;">
      Resolve canonical dbt runtime config from query-engine settings and routing.

      Combines Phlo settings with runtime context to produce a complete dbt runtime
      configuration. Handles catalog name resolution based on runtime references.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > config = resolve\_dbt\_runtime\_config(target="prod")
        > > > print(f"Catalog: \{config.catalog}, Target: \{config.target\_name}")
        > > >
        > > > With runtime that has a branch reference [#with-runtime-that-has-a-branch-reference]
        > > >
        > > > config = resolve\_dbt\_runtime\_config(runtime=ctx)
        > > >
        > > > Catalog will include branch suffix if not "main" [#catalog-will-include-branch-suffix-if-not-main]
      </Callout>

      <PySourceCode>
        ```python
        def resolve_dbt_runtime_config(
            runtime: RuntimeContext | None = None,
            *,
            target: str | None = None,
        ) -> DbtRuntimeConfig:
            """Resolve canonical dbt runtime config from query-engine settings and routing.

            Combines Phlo settings with runtime context to produce a complete dbt runtime
            configuration. Handles catalog name resolution based on runtime references.

            Args:
                runtime: Optional runtime context for environment-based configuration.
                target: Optional explicit target name to use.

            Returns:
                Fully configured DbtRuntimeConfig instance.

            Example:
                >>> config = resolve_dbt_runtime_config(target="prod")
                >>> print(f"Catalog: {config.catalog}, Target: {config.target_name}")
                >>> # With runtime that has a branch reference
                >>> config = resolve_dbt_runtime_config(runtime=ctx)
                >>> # Catalog will include branch suffix if not "main"

            """
            settings = get_dbt_settings()
            target_name = resolve_dbt_target_name(runtime, target=target)
            catalog = settings.dbt_query_catalog
            ref = resolve_runtime_ref(runtime, support=DBT_QUERY_ENGINE_SUPPORT, default_ref="main")
            if ref and ref != "main":
                catalog = f"{catalog}_{ref}"

            return DbtRuntimeConfig(
                profile_name=resolve_dbt_profile_name(settings.dbt_project_path),
                target_name=target_name,
                engine_type=settings.dbt_query_engine_type,
                user=settings.dbt_query_user,
                host=settings.dbt_query_host,
                port=settings.dbt_query_port,
                catalog=catalog,
                schema=settings.dbt_query_schema,
                threads=settings.dbt_query_threads,
                http_scheme=settings.dbt_query_http_scheme,
                method=settings.dbt_query_auth_method,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="&#x22;None&#x22;">
          Optional runtime context for environment-based configuration.
        </PyParameter>

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional explicit target name to use.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_dbt.runtime_config.DbtRuntimeConfig&#x22;">
        Fully configured DbtRuntimeConfig instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;resolve_dbt_profile_name&#x22;" type="&#x22;(project_dir) -> str&#x22;">
      Resolve the dbt profile name declared by the project, if any.

      Reads the dbt\_project.yml file to extract the profile name. Falls back
      to the default profile name if the file doesn't exist or doesn't specify
      a profile.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > profile = resolve\_dbt\_profile\_name(Path("/app/workflows/transforms/dbt"))
        > > > print(profile)
        > > > phlo  # or the profile name from dbt\_project.yml
      </Callout>

      <PySourceCode>
        ```python
        def resolve_dbt_profile_name(project_dir: Path) -> str:
            """Resolve the dbt profile name declared by the project, if any.

            Reads the dbt_project.yml file to extract the profile name. Falls back
            to the default profile name if the file doesn't exist or doesn't specify
            a profile.

            Args:
                project_dir: Path to the dbt project directory containing dbt_project.yml.

            Returns:
                Profile name string, either from the project file or the default.

            Example:
                >>> profile = resolve_dbt_profile_name(Path("/app/workflows/transforms/dbt"))
                >>> print(profile)
                phlo  # or the profile name from dbt_project.yml

            """
            project_file = project_dir / "dbt_project.yml"
            if not project_file.exists():
                return DEFAULT_DBT_PROFILE_NAME
            try:
                payload = yaml.safe_load(project_file.read_text(encoding="utf-8")) or {}
            except Exception:
                return DEFAULT_DBT_PROFILE_NAME
            profile_name = payload.get("profile")
            if isinstance(profile_name, str) and profile_name:
                return profile_name
            return DEFAULT_DBT_PROFILE_NAME
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to the dbt project directory containing dbt\_project.yml.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Profile name string, either from the project file or the default.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;render_dbt_profile_yaml&#x22;" type="&#x22;(config) -> str&#x22;">
      Render canonical dbt runtime config as `profiles.yml` text.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > config = DbtRuntimeConfig(target\_name="prod")
        > > > yaml\_text = render\_dbt\_profile\_yaml(config)
        > > > print(yaml\_text)
        > > > phlo:
        > > > target: prod
        > > > outputs:
        > > > prod:
        > > > type: trino
        > > > ...
      </Callout>

      <PySourceCode>
        ```python
        def render_dbt_profile_yaml(config: DbtRuntimeConfig) -> str:
            """Render canonical dbt runtime config as `profiles.yml` text.

            Args:
                config: DbtRuntimeConfig instance to serialize.

            Returns:
                YAML-formatted string suitable for writing to profiles.yml.

            Example:
                >>> config = DbtRuntimeConfig(target_name="prod")
                >>> yaml_text = render_dbt_profile_yaml(config)
                >>> print(yaml_text)
                phlo:
                  target: prod
                  outputs:
                    prod:
                      type: trino
                      ...

            """
            return yaml.safe_dump(config.to_profile_payload(), sort_keys=False)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config&#x22;" type="&#x22;DbtRuntimeConfig&#x22;" value="undefined">
          DbtRuntimeConfig instance to serialize.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        YAML-formatted string suitable for writing to profiles.yml.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;write_dbt_profile&#x22;" type="&#x22;(config, profiles_dir, *, filename='profiles.yml') -> Path&#x22;">
      Write canonical `profiles.yml` to disk and return its path.

      Creates the profiles directory if it doesn't exist, then writes the
      rendered YAML configuration.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > config = DbtRuntimeConfig(target\_name="prod")
        > > > path = write\_dbt\_profile(config, Path("/app/profiles"))
        > > > print(f"Profile written to: \{path}")
      </Callout>

      <PySourceCode>
        ```python
        def write_dbt_profile(
            config: DbtRuntimeConfig,
            profiles_dir: Path,
            *,
            filename: str = "profiles.yml",
        ) -> Path:
            """Write canonical `profiles.yml` to disk and return its path.

            Creates the profiles directory if it doesn't exist, then writes the
            rendered YAML configuration.

            Args:
                config: DbtRuntimeConfig to serialize and write.
                profiles_dir: Directory path where profiles.yml should be written.
                filename: Name of the profile file (default: "profiles.yml").

            Returns:
                Path to the written profile file.

            Raises:
                OSError: If directory creation or file write fails.

            Example:
                >>> config = DbtRuntimeConfig(target_name="prod")
                >>> path = write_dbt_profile(config, Path("/app/profiles"))
                >>> print(f"Profile written to: {path}")

            """
            profiles_dir.mkdir(parents=True, exist_ok=True)
            profile_path = profiles_dir / filename
            profile_path.write_text(render_dbt_profile_yaml(config), encoding="utf-8")
            return profile_path
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config&#x22;" type="&#x22;DbtRuntimeConfig&#x22;" value="undefined">
          DbtRuntimeConfig to serialize and write.
        </PyParameter>

        <PyParameter name="&#x22;profiles_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Directory path where profiles.yml should be written.
        </PyParameter>

        <PyParameter name="&#x22;filename&#x22;" type="&#x22;str&#x22;" value="&#x22;'profiles.yml'&#x22;">
          Name of the profile file (default: "profiles.yml").
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Path to the written profile file.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;ensure_dbt_profile&#x22;" type="&#x22;(profiles_dir, *, runtime=None, target=None) -> Path&#x22;">
      Resolve and write canonical `profiles.yml` for the active dbt target.

      Combines configuration resolution and profile writing into a single
      convenience function. Ensures a valid profiles.yml exists for the
      specified runtime context and target.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from phlo\_dbt.runtime\_config import ensure\_dbt\_profile
        > > > path = ensure\_dbt\_profile(
        > > > ...     Path("/app/profiles"),
        > > > ...     target="prod"
        > > > ... )
        > > > print(f"Profile ready at: \{path}")
      </Callout>

      <PySourceCode>
        ```python
        def ensure_dbt_profile(
            profiles_dir: Path,
            *,
            runtime: RuntimeContext | None = None,
            target: str | None = None,
        ) -> Path:
            """Resolve and write canonical `profiles.yml` for the active dbt target.

            Combines configuration resolution and profile writing into a single
            convenience function. Ensures a valid profiles.yml exists for the
            specified runtime context and target.

            Args:
                profiles_dir: Directory path where profiles.yml should be written.
                runtime: Optional runtime context for configuration resolution.
                target: Optional explicit target name.

            Returns:
                Path to the written (or existing) profile file.

            Example:
                >>> from phlo_dbt.runtime_config import ensure_dbt_profile
                >>> path = ensure_dbt_profile(
                ...     Path("/app/profiles"),
                ...     target="prod"
                ... )
                >>> print(f"Profile ready at: {path}")

            """
            return write_dbt_profile(
                resolve_dbt_runtime_config(runtime, target=target),
                profiles_dir,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;profiles_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Directory path where profiles.yml should be written.
        </PyParameter>

        <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="&#x22;None&#x22;">
          Optional runtime context for configuration resolution.
        </PyParameter>

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional explicit target name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Path to the written (or existing) profile file.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
