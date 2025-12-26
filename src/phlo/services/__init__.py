"""
Phlo Services Module

Discovers and manages service definitions from installed service plugins.
Used by the CLI to compose infrastructure for lakehouses.
"""

from phlo.discovery import ServiceDefinition, ServiceDiscovery
from phlo.services.composer import ComposeGenerator

__all__ = ["ServiceDiscovery", "ServiceDefinition", "ComposeGenerator"]
