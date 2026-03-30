"""Base plugin classes and metadata.

This module defines the core Plugin base class and PluginMetadata that all
plugin types must inherit from and implement. These classes form the foundation
of Phlo's plugin architecture, providing lifecycle management and metadata
description for all extensions.

Key Classes:
    - :class:`PluginMetadata`: Plugin metadata container (name, version, etc.)
    - :class:`Plugin`: Abstract base class for all plugin types

Plugin Lifecycle:
    1. **Discovery**: Plugins are discovered via entry points
    2. **Loading**: Plugin classes are instantiated
    3. **Initialization**: :meth:`Plugin.initialize` is called with configuration
    4. **Runtime**: Plugin provides its functionality
    5. **Cleanup**: :meth:`Plugin.cleanup` is called when shutting down

Metadata Fields:
    The :class:`PluginMetadata` dataclass captures all essential plugin
    information including versioning, authorship, dependencies, and
    capability requirements.

Example:
    ```python
    from phlo.plugins.base import Plugin, PluginMetadata
    from phlo.capabilities.support import CapabilitySupport

    class MyConnector(Plugin):
        @property
        def metadata(self) -> PluginMetadata:
            return PluginMetadata(
                name="my-connector",
                version="1.0.0",
                description="Connects to My Data Source",
                author="Jane Developer",
                license="MIT",
                homepage="https://github.com/example/my-connector",
                tags=["connector", "source"],
                dependencies=["requests>=2.25.0"],
                requires_capabilities=["query_engine"],
                optional_capabilities=["catalog"],
                support=CapabilitySupport(
                    operational_guarantees=["best_effort"]
                )
            )

        def initialize(self, config: dict[str, Any]) -> None:
            # Connect to data source
            self.connection = create_connection(config)

        def cleanup(self) -> None:
            # Close connection
            self.connection.close()
    ```

Note:
    This module should not be imported directly. Use the public exports
    from :mod:`phlo.plugins.base` instead.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from phlo.capabilities.support import CapabilitySupport


@dataclass
class PluginMetadata:
    """Metadata about a plugin.

    This dataclass captures all essential information about a plugin including
    identity, authorship, dependencies, and capability requirements. It is used
    during plugin discovery, registration, and display.

    Attributes:
        name: Unique plugin name within its plugin type. Must be a valid
            Python identifier without spaces.
        version: Plugin version following semantic versioning (e.g., "1.0.0").
        description: Human-readable description of what the plugin does.
        author: Plugin author name, organization, or email.
        license: SPDX license identifier (e.g., "MIT", "Apache-2.0", "GPL-3.0").
        homepage: URL to the plugin repository or documentation.
        tags: Categorization tags for plugin discovery (e.g., ["source", "api"]).
        dependencies: Required Python packages with version constraints.
        requires_capabilities: Capability names that must be available for
            this plugin to function. Plugin loading will fail if unavailable.
        optional_capabilities: Capability names that enhance functionality
            when available, but are not required.
        support: :class:`~phlo.capabilities.support.CapabilitySupport` declaring
            operational guarantees (best_effort, self_healing, etc.).

    Example:
        ```python
        from phlo.plugins.base import PluginMetadata
        from phlo.capabilities.support import CapabilitySupport

        metadata = PluginMetadata(
            name="postgres-source",
            version="2.1.0",
            description="PostgreSQL data source connector",
            author="Phlo Team <team@phlo.dev>",
            license="Apache-2.0",
            homepage="https://github.com/phlohouse/phlo-postgres",
            tags=["source", "database", "postgres"],
            dependencies=["psycopg2-binary>=2.9.0", "sqlalchemy>=2.0.0"],
            requires_capabilities=["query_engine"],
            optional_capabilities=["iceberg"],
            support=CapabilitySupport(operational_guarantees=["best_effort"])
        )
        ```

    """

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
    """Base class for all Phlo plugins.

    This abstract base class defines the interface that all plugin types must
    implement. It provides lifecycle hooks for initialization and cleanup, and
    requires concrete implementations to provide metadata.

    The Phlo plugin system uses this base class to:
        - Discover and load plugins from entry points
        - Initialize plugins with configuration
        - Manage plugin lifecycle (load, run, cleanup)
        - Track plugin dependencies and requirements

    To create a plugin:
        1. Inherit from this class (or a more specific subclass)
        2. Implement the :meth:`metadata` property
        3. Override :meth:`initialize` for setup logic
        4. Override :meth:`cleanup` for teardown logic

    Attributes:
        None at the base class level. Subclasses may add attributes
        for their specific functionality.

    Abstract Methods:
        - :meth:`metadata`: Return :class:`PluginMetadata` for this plugin

    Lifecycle Methods:
        - :meth:`initialize`: Called once when plugin is loaded
        - :meth:`cleanup`: Called when plugin is being unloaded

    Example:
        ```python
        from phlo.plugins.base import Plugin, PluginMetadata

        class CustomPlugin(Plugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="my-plugin",
                    version="1.0.0",
                    description="Does something useful"
                )

            def initialize(self, config: dict[str, Any]) -> None:
                # Setup code here
                self.api_key = config.get("api_key")

            def cleanup(self) -> None:
                # Teardown code here
                pass
        ```

    See Also:
        - :class:`SourceConnectorPlugin`: For data source connectors
        - :class:`ServicePlugin`: For infrastructure services
        - :class:`CatalogPlugin`: For metadata catalogs

    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata with name, version, description, etc.

        """

    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the plugin with configuration.

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
        """Clean up plugin resources.

        This method is called when the plugin is being unloaded.
        Override to perform cleanup tasks like:
        - Closing connections
        - Releasing resources
        - Saving state
        """
        return
