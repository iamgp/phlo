"""Phlo API modules.

This package provides tools for managing API layers (PostgREST and Hasura).

Quick Start:
    # Generate PostgREST views from dbt models
    >>> from phlo.api.postgrest.views import generate_views
    >>> generate_views(apply=True)

    # Auto-track tables in Hasura
    >>> from phlo.api.hasura import auto_track
    >>> auto_track(schema="api")

    # Manage permissions
    >>> from phlo.api.hasura import HasuraPermissionManager
    >>> manager = HasuraPermissionManager()
    >>> manager.sync_permissions(config, verbose=True)
"""

from phlo.api.hasura import (
    HasuraClient,
    HasuraPermissionManager,
    HasuraTableTracker,
)
from phlo.api.postgrest.views import generate_views

__all__ = [
    "generate_views",
    "HasuraClient",
    "HasuraPermissionManager",
    "HasuraTableTracker",
]
