"""Audit log commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from phlo.cli.output import json_envelope


@click.group(name="audit")
def audit_group() -> None:
    """Inspect local Phlo audit records."""


def _audit_path() -> Path:
    return Path(".phlo") / "audit" / "operations.jsonl"


def _read_records(limit: int | None = None) -> list[dict[str, Any]]:
    path = _audit_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if limit is not None:
        lines = lines[-limit:]
    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append({"malformed": line})
    return records


@audit_group.command("tail")
@click.option("--limit", default=20, show_default=True)
@click.option("--since", help="Accepted for CLI compatibility; currently informational.")
@click.option("--json", "output_json", is_flag=True, help="Emit machine-readable JSON.")
def tail_cmd(limit: int, since: str | None, output_json: bool) -> None:
    """Tail recent audit records."""
    records = _read_records(limit=limit)
    if output_json:
        click.echo(json_envelope(data={"items": records, "since": since}))
        return
    for record in records:
        click.echo(json.dumps(record, sort_keys=True))


@audit_group.command("query")
@click.option("--operation")
@click.option("--json", "output_json", is_flag=True, help="Emit machine-readable JSON.")
def query_cmd(operation: str | None, output_json: bool) -> None:
    """Query audit records."""
    records = _read_records()
    if operation:
        records = [record for record in records if record.get("operation") == operation]
    if output_json:
        click.echo(json_envelope(data={"items": records}))
        return
    for record in records:
        click.echo(json.dumps(record, sort_keys=True))


__all__ = ["audit_group"]
