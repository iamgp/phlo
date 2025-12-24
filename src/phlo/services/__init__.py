"""
Phlo Services Module

Discovers and manages service definitions from installed service plugins.
Used by the CLI to compose infrastructure for lakehouses.
"""

from phlo.services.composer import ComposeGenerator
from phlo.services.discovery import ServiceDefinition, ServiceDiscovery

__all__ = ["ServiceDiscovery", "ServiceDefinition", "ComposeGenerator"]
