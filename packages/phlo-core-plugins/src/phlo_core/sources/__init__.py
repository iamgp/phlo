"""Source connector plugins bundled with Phlo.

This module provides source connector plugins that enable Phlo to ingest
data from various external systems and APIs. Source connectors handle the
complexity of connecting to external data sources, authentication, and
data extraction.

Available Plugins:
    - RestAPIPlugin: Generic REST API connector for fetching data from
        HTTP endpoints. Supports pagination, authentication headers,
        query parameters, and configurable timeouts.

Each plugin follows the SourceConnectorPlugin interface and provides methods
for fetching data and optionally retrieving schema information.

Example:
    Import and use source plugins::

        from phlo_core.sources import RestAPIPlugin

        # Create the plugin
        rest_plugin = RestAPIPlugin()

        # Configure and fetch data
        config = {
            "url": "https://api.example.com/users",
            "headers": {"Authorization": "Bearer token123"},
            "params": {"limit": 100},
            "timeout": 30,
            "records_path": "data.users"
        }

        for record in rest_plugin.fetch_data(config):
            process(record)

"""

from phlo_core.sources.rest_api import RestAPIPlugin

__all__ = ["RestAPIPlugin"]
