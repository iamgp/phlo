"""Trino service plugin package."""

from phlo_trino.governance import TrinoGovernanceBackend
from phlo_trino.plugin import TrinoResourceProvider, TrinoServicePlugin
from phlo_trino.resource import TrinoResource
from phlo_trino.settings import TrinoSettings, get_settings

__all__ = [
    "TrinoGovernanceBackend",
    "TrinoResourceProvider",
    "TrinoServicePlugin",
    "TrinoResource",
    "TrinoSettings",
    "get_settings",
]
__version__ = "0.1.0"
