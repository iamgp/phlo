from __future__ import annotations

from click.testing import CliRunner

from phlo.cli.commands.services.exec import exec_cmd
from phlo.cli.commands.services.logs import logs_cmd
from phlo.cli.commands.services.restart import restart_cmd
from phlo.cli.commands.services.start import start_cmd
from phlo.cli.commands.services.stop import stop_cmd


def test_docker_lifecycle_help_is_user_facing() -> None:
    commands = [start_cmd, stop_cmd, restart_cmd, logs_cmd, exec_cmd]

    for command in commands:
        result = CliRunner().invoke(command, ["--help"])

        assert result.exit_code == 0, result.output
        assert "Examples:" not in result.output
        assert "Args:" not in result.output
        assert "Returns:" not in result.output
