"""Hasura GraphQL API automation and management.

This module provides tools for managing Hasura metadata:
- Table tracking and relationships
- Permission configuration and sync
- Metadata export/import
- Schema management

Example:
    >>> from phlo_hasura import HasuraClient
    >>> client = HasuraClient()
    >>> client.track_table("api", "glucose_readings")
"""

from phlo_hasura.client import HasuraClient
from phlo_hasura.permissions import HasuraPermissionManager
from phlo_hasura.track import HasuraTableTracker

__all__ = [
    "HasuraClient",
    "HasuraPermissionManager",
    "HasuraTableTracker",
]
