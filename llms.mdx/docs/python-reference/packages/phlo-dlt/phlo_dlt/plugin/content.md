# plugin (/docs/python-reference/packages/phlo-dlt/phlo_dlt/plugin)



Plugin interface for Phlo DLT integration.

This module provides the plugin classes that integrate phlo-dlt with the
Phlo plugin system. It exposes DLT-based ingestion capabilities through
standardized plugin interfaces.

Plugin Classes:

* :class:`DltAssetProvider`: Provides DLT-defined assets to Phlo
* :class:`DLTIngestionProvider`: Provides ingestion decorator interface

Plugin Registration:
These plugins are discovered via entry points defined in pyproject.toml:

* `phlo.asset_providers`: DltAssetProvider
* `phlo.ingestion_providers`: DLTIngestionProvider

Capabilities Exposed:

* Ingestion asset definitions from @phlo\_ingestion decorators
* Asset check specifications for Pandera validation
* The phlo\_ingestion decorator for users

See Also:

* :mod:`phlo.plugins.base`: Base plugin interfaces
* :mod:`phlo.plugins.discovery`: Plugin discovery system
* :mod:`phlo_dlt.decorator`: Asset registration source

Example:
The plugins are auto-discovered by Phlo. Users interact with them
via the public API:

```python
import phlo

# Uses DLTIngestionProvider internally
@phlo.ingestion.phlo_ingestion(table_name="users", ...)
def load_users(): ...

# Uses DltAssetProvider internally
assets = phlo.ingestion.get_ingestion_assets()
```

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DltAssetProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/plugin/DltAssetProvider&#x22;" />

      <Card title="&#x22;DLTIngestionProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/plugin/DLTIngestionProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
