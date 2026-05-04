"""Shared user-facing CLI output helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import click


def user_error(
    summary: str,
    *,
    missing: str | Path | None = None,
    run: str | None = None,
    details: Mapping[str, Any] | Iterable[str] | None = None,
) -> click.ClickException:
    """Build a concise, recoverable CLI error.

    The returned exception intentionally contains only user-facing text. Internal
    diagnostics should be logged separately with structured fields.
    """
    lines = [summary]

    if missing is not None:
        lines.extend(["", f"Missing: {missing}"])

    if details:
        lines.append("")
        if isinstance(details, Mapping):
            lines.extend(f"{key}: {value}" for key, value in details.items())
        else:
            lines.extend(str(item) for item in details)

    if run:
        lines.extend(["", f"Run: {run}"])

    return click.ClickException("\n".join(lines))


def missing_phlo_project_error() -> click.ClickException:
    """Return the standard error for commands that require `.phlo/`."""
    return user_error(
        "Phlo services have not been initialized",
        missing=".phlo/",
        run="phlo services init",
    )


def missing_compose_file_error(compose_file: str | Path) -> click.ClickException:
    """Return the standard error for commands that require generated Compose config."""
    return user_error(
        "services have not been initialized",
        missing=compose_file,
        run="phlo services init",
    )


def exclusive_options_error(left: str, right: str) -> click.ClickException:
    """Return the standard error for mutually-exclusive input options."""
    return user_error(
        "choose one input source",
        details=[f"Use either {left} or {right}, not both."],
    )


def missing_query_error(*, command_hint: str) -> click.ClickException:
    """Return the standard error for query commands with no SQL input."""
    return user_error(
        "no SQL query provided",
        details=["Provide an inline query argument or pass --file."],
        run=command_hint,
    )


def file_read_error(path: str | Path) -> click.ClickException:
    """Return the standard error for unreadable command input files."""
    return user_error("could not read file", details={"File": path})


def empty_file_error(path: str | Path) -> click.ClickException:
    """Return the standard error for empty command input files."""
    return user_error("file is empty", details={"File": path})


def command_failed_error(
    command_name: str,
    *,
    exit_code: int | None = None,
    run: str | None = None,
    details: Mapping[str, Any] | Iterable[str] | None = None,
) -> click.ClickException:
    """Return the standard error for external command failures."""
    failure_details: list[str] = []
    if exit_code is not None:
        failure_details.append(f"Exit code: {exit_code}")
    if details:
        if isinstance(details, Mapping):
            failure_details.extend(f"{key}: {value}" for key, value in details.items())
        else:
            failure_details.extend(str(item) for item in details)
    return user_error(f"{command_name} failed", details=failure_details, run=run)


def service_unavailable_error(
    service: str, *, run: str = "phlo services start"
) -> click.ClickException:
    """Return the standard error for commands that need a running service."""
    return user_error(
        f"{service} is not available",
        details=[f"Make sure the {service} service is running."],
        run=run,
    )
