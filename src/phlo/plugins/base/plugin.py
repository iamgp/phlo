"""
Base plugin classes and metadata.

This module defines the core Plugin base class and PluginMetadata that all
plugin types must inherit from and implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from phlo.capabilities.support import CapabilitySupport


@dataclass
class PluginMetadata:
    """Metadata about a plugin."""

    name: str
    """Plugin name (must be unique within plugin type)."""

    version: str
    """Plugin version (semver format)."""

    description: str = ""
    """Human-readable description of the plugin."""

    author: str = ""
    """Plugin author name/organization."""

    license: str = ""
    """Plugin license (e.g., MIT, Apache-2.0)."""

    homepage: str = ""
    """Plugin homepage or repository URL."""

    tags: list[str] = field(default_factory=list)
    """Tags for categorizing/searching plugins."""

    dependencies: list[str] = field(default_factory=list)
    """Python package dependencies required by this plugin."""

    requires_capabilities: list[str] = field(default_factory=list)
    """Capabilities this plugin needs to function."""

    optional_capabilities: list[str] = field(default_factory=list)
    """Capabilities this plugin can use when available."""

    support: CapabilitySupport = field(default_factory=CapabilitySupport)
    """Concrete guarantees the plugin or provider supports."""


class Plugin(ABC):
    """
    Base class for all Phlo plugins.

    All plugin types must inherit from this class and implement
    the required abstract properties and methods.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        Return plugin metadata.

        Returns:
            PluginMetadata with name, version, description, etc.
        """

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.

        This method is called once when the plugin is loaded.
        Override to perform initialization tasks like:
        - Validating configuration
        - Setting up connections
        - Loading resources

        Args:
            config: Configuration dictionary for the plugin
        """
        return

    def cleanup(self) -> None:
        """
        Clean up plugin resources.

        This method is called when the plugin is being unloaded.
        Override to perform cleanup tasks like:
        - Closing connections
        - Releasing resources
        - Saving state
        """
        return
