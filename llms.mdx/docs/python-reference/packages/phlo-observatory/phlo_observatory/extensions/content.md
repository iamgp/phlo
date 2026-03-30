# extensions (/docs/python-reference/packages/phlo-observatory/phlo_observatory/extensions)



Observatory extension discovery utilities (backward-compatible re-exports).

This module provides backward-compatible access to extension discovery and
retrieval functions for the Observatory UI plugin system.

Extension Discovery:
The Observatory uses Python entry points to discover UI extensions.
Extensions declare themselves in package metadata and are loaded
dynamically at runtime.

Key Functions:

* discover\_observatory\_extensions: Scan and load all available extensions
* get\_observatory\_extension: Retrieve a specific extension by name

Backward Compatibility:
These exports are maintained for existing extensions. New code should
import directly from phlo.plugins.observatory.

Example:

> > > from phlo\_observatory.extensions import discover\_observatory\_extensions
> > > extensions = discover\_observatory\_extensions()
> > > for ext in extensions:
> > > ...     print(f"Found extension: \{ext.manifest.name}")

See Also:
phlo.plugins.observatory: Source of truth for extension API.
phlo\_observatory.manifest: Extension manifest data models.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['ObservatoryExtensionPlugin', 'discover_observatory_extensions', 'get_observatory_extension']&#x22;" />
