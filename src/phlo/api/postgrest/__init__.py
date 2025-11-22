"""PostgREST authentication infrastructure setup.

This module provides the core authentication infrastructure for PostgREST,
including database roles, JWT functions, and user management.

Example:
    >>> from phlo.api.postgrest import setup_postgrest
    >>> setup_postgrest()  # Sets up auth infrastructure
"""

from phlo.api.postgrest.setup import setup_postgrest

__all__ = ["setup_postgrest"]
