from __future__ import annotations

import subprocess
from dataclasses import dataclass
from subprocess import CompletedProcess
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class CommandError(RuntimeError):
    cmd: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def __str__(self) -> str:
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
        raise CommandError(
            cmd=tuple(cmd),
            returncode=result.returncode,
            stdout=stdout,
            stderr=stderr,
        )
    return result
