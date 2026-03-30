# observatory_ext (/docs/python-reference/packages/phlo-observatory/phlo_observatory/observatory_ext)



Observatory extension plugin base class (backward-compatible re-export).

This module provides backward-compatible access to the ObservatoryExtensionPlugin
base class, which is the foundation for all Observatory UI extensions.

Extension authors subclass ObservatoryExtensionPlugin to:

* Define extension metadata (name, version, description)
* Register UI routes and navigation items
* Provide settings panels and configuration options
* Inject content into Observatory UI slots

Backward Compatibility:
This re-export is maintained for existing extensions. New extensions should
import directly from phlo.plugins.observatory.

Example:

> > > from phlo\_observatory.observatory\_ext import ObservatoryExtensionPlugin
> > > class MyExtension(ObservatoryExtensionPlugin):
> > > ...     @property
> > > ...     def manifest(self):
> > > ...         return ObservatoryExtensionManifest(name="my-extension", ...)

See Also:
phlo.plugins.observatory.ObservatoryExtensionPlugin: Source definition.
phlo\_observatory.manifest: Related manifest data models.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['ObservatoryExtensionPlugin']&#x22;" />
