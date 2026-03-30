# env (/docs/python-reference/core/phlo/cli/env)



Environment Configuration Commands

Commands for exporting generated environment configuration.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;env&#x22;" type="&#x22;() -> None&#x22;">
      Manage environment configuration.

      <PySourceCode>
        ```python
        @click.group()
        def env() -> None:
            """Manage environment configuration."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;export_env&#x22;" type="&#x22;(include_secrets, output, _format) -> None&#x22;">
      Export the generated environment configuration.

      <PySourceCode>
        ```python
        @env.command("export")
        @click.option(
            "--include-secrets",
            is_flag=True,
            help="Include secrets from .phlo/.env.local in the export output.",
        )
        @click.option(
            "--output",
            type=click.Path(dir_okay=False, path_type=Path),
            help="Write output to a file instead of stdout.",
        )
        @click.option(
            "--format",
            "_format",
            type=click.Choice(["dotenv"], case_sensitive=False),
            default="dotenv",
            help="Output format (dotenv only for now).",
        )
        def export_env(include_secrets: bool, output: Path | None, _format: str) -> None:
            """Export the generated environment configuration.

            Examples:
                phlo env export
                phlo env export --include-secrets
                phlo env export --output env.full
            """
            config = _load_project_config()
            env_overrides = _get_env_overrides(config)
            logger.info(
                "env_export_started",
                include_secrets=include_secrets,
                output_file=output is not None,
                output_format=_format,
            )

            discovery = ServiceDiscovery()
            all_services = discovery.discover()
            if not all_services:
                logger.warning("env_export_no_services_found")
                raise click.ClickException(
                    "No services found. Install service plugins or run from a Phlo project directory."
                )

            services_to_install = _select_services(discovery, all_services, config)
            composer = ComposeGenerator(discovery)

            env_content = composer.generate_env(services_to_install, env_overrides=env_overrides)

            if include_secrets:
                env_local_path = Path.cwd() / ".phlo" / ".env.local"
                existing_env_local = parse_env_file(env_local_path)
                env_local_content = composer.generate_env_local(
                    services_to_install,
                    env_overrides=env_overrides,
                    existing_values=existing_env_local,
                )
                content = f"{env_content.rstrip()}\n\n{env_local_content.lstrip()}"
            else:
                content = env_content

            if output:
                output.write_text(content)
                logger.info("env_export_succeeded", output_file=str(output))
                click.echo(f"Wrote: {output}")
            else:
                logger.info("env_export_succeeded", output_file=None)
                click.echo(content)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;include_secrets&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;output&#x22;" type="&#x22;Path | None&#x22;" value="null" />

        <PyParameter name="&#x22;_format&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_project_config&#x22;" type="&#x22;() -> dict[str, Any]&#x22;">
      <PySourceCode>
        ```python
        def _load_project_config() -> dict[str, Any]:
            config_path = Path.cwd() / "phlo.yaml"
            if not config_path.exists():
                return {}
            try:
                with config_path.open() as f:
                    return yaml.safe_load(f) or {}
            except (OSError, yaml.YAMLError):
                logger.warning("env_export_config_load_failed", path=str(config_path), exc_info=True)
                return {}
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_get_env_overrides&#x22;" type="&#x22;(config) -> dict[str, Any]&#x22;">
      <PySourceCode>
        ```python
        def _get_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
            env_overrides = config.get("env", {}) if isinstance(config, dict) else {}
            return env_overrides if isinstance(env_overrides, dict) else {}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_select_services&#x22;" type="&#x22;(discovery, all_services, config) -> list[ServiceDefinition]&#x22;">
      <PySourceCode>
        ```python
        def _select_services(
            discovery: ServiceDiscovery,
            all_services: dict[str, ServiceDefinition],
            config: dict[str, Any],
        ) -> list[ServiceDefinition]:
            user_overrides = config.get("services", {}) if isinstance(config, dict) else {}

            disabled_services = {
                name
                for name, cfg in user_overrides.items()
                if isinstance(cfg, dict) and cfg.get("enabled") is False
            }

            inline_services = [
                ServiceDefinition.from_inline(name, cfg)
                for name, cfg in user_overrides.items()
                if isinstance(cfg, dict) and cfg.get("type") == "inline"
            ]

            default_services = discovery.get_default_services(disabled_services=disabled_services)
            profile_services = [
                service
                for service in all_services.values()
                if service.profile and service.name not in disabled_services
            ]

            return default_services + profile_services + inline_services
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;discovery&#x22;" type="&#x22;ServiceDiscovery&#x22;" value="null" />

        <PyParameter name="&#x22;all_services&#x22;" type="&#x22;dict[str, ServiceDefinition]&#x22;" value="null" />

        <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[phlo.plugins.discovery.ServiceDefinition]&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
