"""Hasura GraphQL API automation and management.

This module provides tools for managing Hasura metadata:
- Table tracking and relationships
- Permission configuration and sync
- Metadata export/import
- Schema management

Example:
    >>> from phlo_hasura import HasuraClient
    >>> client = HasuraClient()
    >>> client.track_table("api", "orders")

Classes:
    HasuraClient: Client for Hasura Metadata API operations.
    HasuraPermissionManager: Manages permissions from YAML/JSON config files.
    HasuraTableTracker: Automatically discovers and tracks PostgreSQL tables.

Functions:
    track_tables: Auto-track tables in specified schema(s).
    auto_track: Convenience function to auto-track all tables in a schema.
    auto_track_all: Auto-discover and track all tables in all user schemas.
    export_metadata: Export current Hasura metadata.
    apply_metadata: Apply Hasura metadata from file.
    sync_permissions: Sync permissions from config file.

"""

from phlo_hasura.client import HasuraClient
from phlo_hasura.permissions import HasuraPermissionManager
from phlo_hasura.track import HasuraTableTracker

__all__ = [
    "HasuraClient",
    "HasuraPermissionManager",
    "HasuraTableTracker",
]
