"""Workflow management commands."""

from __future__ import annotations

import click


@click.group(name="workflow")
def workflow_group():
    """Manage workflows."""
    pass


__all__ = ["workflow_group"]
