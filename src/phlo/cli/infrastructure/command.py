from __future__ import annotations

import subprocess
from dataclasses import dataclass
from subprocess import CompletedProcess
from typing import Mapping, Sequence

from phlo.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class CommandError(RuntimeError):
    """Error raised when a subprocess command exits with a non-zero status."""

    cmd: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def __post_init__(self) -> None:
        """Populate RuntimeError args tuple for consistent exception rendering."""

        object.__setattr__(self, "args", (self.cmd, self.returncode, self.stdout, self.stderr))

    def __str__(self) -> str:
        """Render a readable command failure message."""

        cmd = " ".join(self.cmd)
        stderr = self.stderr.strip()
        if stderr:
            return f"Command failed ({self.returncode}): {cmd}\n{stderr}"
        return f"Command failed ({self.returncode}): {cmd}"


def run_command(
    cmd: Sequence[str],
    *,
    timeout_seconds: int | None = None,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    capture_output: bool = True,
    check: bool = True,
) -> CompletedProcess[str]:
    """Run a subprocess command with optional timeout and environment overrides.

    Args:
        cmd: Command and arguments to execute.
        timeout_seconds: Optional timeout in seconds.
        cwd: Optional working directory.
        env: Optional environment overrides.
        capture_output: Whether to capture stdout/stderr.
        check: Whether to raise on non-zero exit codes.

    Returns:
        CompletedProcess containing stdout, stderr, returncode, and args.

    Raises:
        CommandError: When check is True and the command exits non-zero.
        subprocess.TimeoutExpired: When the command exceeds timeout_seconds.
    """
    command_name = cmd[0] if cmd else "<empty>"
    logger.debug(
        "subprocess_command_started",
        command_name=command_name,
        arg_count=max(len(cmd) - 1, 0),
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        capture_output=capture_output,
    )

    result = subprocess.run(
        list(cmd),
        capture_output=capture_output,
        text=capture_output,
        timeout=timeout_seconds,
        cwd=cwd,
        env=None if env is None else dict(env),
        check=False,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if check and result.returncode != 0:
        logger.error(
            "subprocess_command_failed",
            command_name=command_name,
            returncode=result.returncode,
            stdout_length=len(stdout),
            stderr_length=len(stderr),
        )
        raise CommandError(
            cmd=tuple(cmd),
            returncode=result.returncode,
            stdout=stdout,
            stderr=stderr,
        )
    logger.debug(
        "subprocess_command_completed",
        command_name=command_name,
        returncode=result.returncode,
    )
    return result
