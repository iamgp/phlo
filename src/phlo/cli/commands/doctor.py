from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import click


class DiagnosticStatus(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass(frozen=True)
class DiagnosticResult:
    id: str
    group: str
    status: DiagnosticStatus
    message: str
    fix: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "group": self.group,
            "status": self.status.value,
            "message": self.message,
        }
        if self.fix:
            payload["fix"] = self.fix
        if self.details:
            payload["details"] = self.details
        return payload


def summarize(results: list[DiagnosticResult]) -> dict[str, int]:
    return {
        status.value: sum(1 for result in results if result.status == status)
        for status in DiagnosticStatus
    }


def render_json(results: list[DiagnosticResult]) -> str:
    return json.dumps(
        {
            "summary": summarize(results),
            "checks": [result.to_payload() for result in results],
        },
        indent=2,
        sort_keys=True,
    )


def render_terminal(results: list[DiagnosticResult]) -> str:
    lines = ["Phlo Doctor", ""]
    groups = list(dict.fromkeys(result.group for result in results))
    for group in groups:
        lines.append(group)
        for result in [item for item in results if item.group == group]:
            lines.append(f"  {result.status.value:<5} {result.message}")
            if result.fix:
                lines.append(f"        Fix: {result.fix}")
        lines.append("")
    summary = summarize(results)
    lines.append(
        "Summary: "
        f"{summary['ok']} ok, {summary['warn']} warnings, "
        f"{summary['fail']} failures, {summary['skip']} skipped"
    )
    return "\n".join(lines)


def run_diagnostics(*, verbose: bool = False) -> list[DiagnosticResult]:
    return [
        DiagnosticResult(
            "doctor.bootstrap", "Environment", DiagnosticStatus.OK, "Doctor command loaded"
        )
    ]


@click.command("doctor")
@click.option("--json", "output_json", is_flag=True, help="Output diagnostics as JSON.")
@click.option("--verbose", is_flag=True, help="Include exception details where available.")
def doctor_cmd(output_json: bool, verbose: bool) -> None:
    """Diagnose local Phlo setup and service health."""
    results = run_diagnostics(verbose=verbose)
    click.echo(render_json(results) if output_json else render_terminal(results))
    if any(result.status == DiagnosticStatus.FAIL for result in results):
        raise click.exceptions.Exit(1)
