# services (/docs/python-reference/core/phlo/cli/commands/services)



Service management commands.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['services_group', '_register_commands']&#x22;" />

<Tabs items="[&#x22;Functions&#x22;,&#x22;Modules&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_register_commands&#x22;" type="&#x22;() -> None&#x22;">
      Import and register service subcommands lazily.

      This keeps `phlo.cli.commands.services` lightweight when utility modules are imported
      from service-specific plugins during CLI plugin discovery.

      <PySourceCode>
        ```python
        def _register_commands() -> None:
            """Import and register service subcommands lazily.

            This keeps `phlo.cli.commands.services` lightweight when utility modules are imported
            from service-specific plugins during CLI plugin discovery.
            """
            global _COMMANDS_REGISTERED
            if _COMMANDS_REGISTERED:
                return

            from phlo.cli.commands.services.add import add_cmd
            from phlo.cli.commands.services.exec import exec_cmd
            from phlo.cli.commands.services.init import init_cmd
            from phlo.cli.commands.services.list import list_cmd
            from phlo.cli.commands.services.logs import logs_cmd
            from phlo.cli.commands.services.ports import ports_cmd
            from phlo.cli.commands.services.remove import remove_cmd
            from phlo.cli.commands.services.reset import reset_cmd
            from phlo.cli.commands.services.restart import restart_cmd
            from phlo.cli.commands.services.start import start_cmd
            from phlo.cli.commands.services.status import status_cmd
            from phlo.cli.commands.services.stop import stop_cmd

            services_group.add_command(init_cmd)
            services_group.add_command(list_cmd)
            services_group.add_command(ports_cmd)
            services_group.add_command(start_cmd)
            services_group.add_command(stop_cmd)
            services_group.add_command(reset_cmd)
            services_group.add_command(restart_cmd)
            services_group.add_command(status_cmd)
            services_group.add_command(add_cmd)
            services_group.add_command(remove_cmd)
            services_group.add_command(logs_cmd)
            services_group.add_command(exec_cmd)
            _COMMANDS_REGISTERED = True
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;services_group&#x22;" type="&#x22;(ctx) -> None&#x22;">
      Manage Phlo infrastructure services (Docker).

      <PySourceCode>
        ```python
        @click.group(name="services", invoke_without_command=True)
        @click.pass_context
        def services_group(ctx: click.Context) -> None:
            """Manage Phlo infrastructure services (Docker)."""
            _register_commands()
            if ctx.invoked_subcommand is None:
                click.echo(ctx.get_help())
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ctx&#x22;" type="&#x22;click.Context&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>

  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/utils&#x22;" title="&#x22;utils&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/exec&#x22;" title="&#x22;exec&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/init&#x22;" title="&#x22;init&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/remove&#x22;" title="&#x22;remove&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/logs&#x22;" title="&#x22;logs&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/add&#x22;" title="&#x22;add&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/status&#x22;" title="&#x22;status&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/reset&#x22;" title="&#x22;reset&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/start&#x22;" title="&#x22;start&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/stop&#x22;" title="&#x22;stop&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/list&#x22;" title="&#x22;list&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/ports&#x22;" title="&#x22;ports&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli/commands/services/restart&#x22;" title="&#x22;restart&#x22;" />
    </Cards>
  </Tab>
</Tabs>
