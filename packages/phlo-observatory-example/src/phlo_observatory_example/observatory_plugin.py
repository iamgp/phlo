"""Example Observatory extension plugin implementation.

This module defines the ExampleObservatoryExtension class, which demonstrates
the full capabilities of the Observatory extension API including:

- Custom UI routes and navigation items
- Dashboard slot integrations
- Extension settings panels with JSON schema validation
- Static asset serving for bundled JavaScript components

Classes:
    ExampleObservatoryExtension: Main extension plugin implementation.

Example:
    The extension is loaded automatically by the plugin discovery system::

        from phlo.plugins import discover_plugins
        plugins = discover_plugins("phlo.observatory.extensions")

See Also:
    phlo.plugins.observatory: Base classes and interfaces for Observatory extensions.
    phlo_observatory_example.observatory_assets: Bundled static assets.

Loaded through the phlo plugin entry-point mechanism at startup rather than imported directly.
Reference implementation built on the phlo.plugins.observatory extension API.
"""

from __future__ import annotations

from importlib import resources
from importlib.abc import Traversable

from phlo.plugins import PluginMetadata
from phlo.plugins.observatory import (
    ObservatoryExtensionCompatibility,
    ObservatoryExtensionManifest,
    ObservatoryExtensionNavItem,
    ObservatoryExtensionPlugin,
    ObservatoryExtensionRoute,
    ObservatoryExtensionSettings,
    ObservatoryExtensionSettingsPanel,
    ObservatoryExtensionSlot,
    ObservatoryExtensionUI,
)


class ExampleObservatoryExtension(ObservatoryExtensionPlugin):
    """Example Observatory extension demonstrating plugin capabilities.

    This extension provides a complete example of how to extend the
    Phlo Observatory UI with custom routes, dashboard integrations,
    and user-configurable settings.

    The extension registers:
    - A dedicated route at ``/extensions/example``
    - Navigation link in the sidebar
    - Dashboard widget slots (after cards and hub stats)
    - Settings panel with toggle and message configuration

    Attributes:
        _metadata: Cached PluginMetadata instance.
        _manifest: Cached ObservatoryExtensionManifest instance.
        _asset_root: Cached Traversable path to static assets.

    Example:
        Extension is auto-discovered and loaded by Phlo::

            from phlo.plugins.observatory import load_extension
            ext = load_extension("phlo_observatory_example")

    See Also:
        ObservatoryExtensionPlugin: Base class defining the extension interface.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for extension discovery and registration.

        The metadata provides the extension's identity including name,
        version, and description. This information is used by the
        plugin system for dependency resolution and display purposes.

        Returns:
            PluginMetadata: Extension identity with the following fields:
                - name: Short identifier "example"
                - version: Semantic version "0.1.0"
                - description: Human-readable summary

        Example:
            Access metadata for debugging or display::

                ext = ExampleObservatoryExtension()
                print(ext.metadata.name)  # "example"

        """
        return PluginMetadata(
            name="example",
            version="0.1.0",
            description="Example Observatory UI extension",
        )

    @property
    def manifest(self) -> ObservatoryExtensionManifest:
        """Return Observatory extension manifest with full configuration.

        The manifest defines all UI integrations, settings schemas, and
        compatibility requirements. It controls how the extension appears
        and behaves within the Observatory interface.

        Returns:
            ObservatoryExtensionManifest: Complete extension configuration
                including:
                - name: Extension identifier
                - version: Extension version
                - compat: Minimum Observatory version requirements
                - settings: JSON schema and default values for configuration
                - ui: Routes, navigation, slots, and settings panels

        Raises:
            ValidationError: If manifest configuration is invalid.

        Example:
            Inspect manifest configuration::

                ext = ExampleObservatoryExtension()
                manifest = ext.manifest
                print(manifest.ui.routes)  # List of routes

        See Also:
            ObservatoryExtensionSettings: Configuration schema definition.
            ObservatoryExtensionUI: UI component registrations.

        """
        return ObservatoryExtensionManifest(
            name="example",
            version="0.1.0",
            compat=ObservatoryExtensionCompatibility(observatory_min="0.1.0"),
            settings=ObservatoryExtensionSettings(
                settings_schema={
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "message": {"type": "string"},
                    },
                },
                defaults={"enabled": True, "message": "Hello from extension settings."},
                scope="extension",
            ),
            ui=ObservatoryExtensionUI(
                routes=[
                    ObservatoryExtensionRoute(
                        path="/extensions/example",
                        module="/example.js",
                        export="registerRoutes",
                    )
                ],
                nav=[ObservatoryExtensionNavItem(title="Example", to="/extensions/example")],
                slots=[
                    ObservatoryExtensionSlot(
                        slot_id="dashboard.after-cards",
                        module="/example.js",
                        export="registerDashboardSlot",
                    ),
                    ObservatoryExtensionSlot(
                        slot_id="hub.after-stats",
                        module="/example.js",
                        export="registerHubSlot",
                    ),
                ],
                settings=[
                    ObservatoryExtensionSettingsPanel(
                        module="/example.js", export="registerSettings"
                    )
                ],
            ),
        )

    @property
    def asset_root(self) -> Traversable:
        """Return the static asset directory for the extension.

        Assets in this directory (JavaScript bundles, images, etc.) are
        served by the Observatory server and made available to the
        extension's frontend components.

        Returns:
            Traversable: Package path to the ``observatory_assets`` directory.
                Uses importlib.resources for reliable path resolution
                across package installation methods (editable, wheel, etc.).

        Raises:
            ModuleNotFoundError: If the package resources cannot be located.

        Example:
            Access bundled JavaScript file::

                ext = ExampleObservatoryExtension()
                js_path = ext.asset_root.joinpath("example.js")
                content = js_path.read_text()

        See Also:
            importlib.resources: Modern Python resource loading API.
            phlo_observatory_example.observatory_assets: Asset directory contents.

        """
        return resources.files("phlo_observatory_example").joinpath("observatory_assets")
