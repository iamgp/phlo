# rest_api (/docs/python-reference/packages/phlo-core-plugins/phlo_core/sources/rest_api)



REST API source connector plugin.

This module provides the RestAPIPlugin, a generic source connector for fetching
data from REST API endpoints. It supports configurable HTTP requests with
custom headers, query parameters, timeouts, and flexible response parsing.

Features:

* HTTP GET requests with configurable headers and query parameters
* Customizable timeout settings
* Flexible response parsing with dot-notation path support
* Automatic error handling with HTTP status code checking
* Support for both list and object response payloads
* Optional static schema retrieval

Example:
Using the REST API plugin::

from phlo\_core.sources.rest\_api import RestAPIPlugin

Create the plugin [#create-the-plugin]

plugin = RestAPIPlugin()

Configure a data fetch [#configure-a-data-fetch]

config = \{
"url": "[https://api.example.com/v1/users](https://api.example.com/v1/users)",
"headers": \{
"Authorization": "Bearer your-api-token",
"Accept": "application/json"
},
"params": \{"page": 1, "per\_page": 100},
"timeout": 30,
"records\_path": "data.users",  # Dot-notation path to records
"schema": \{
"id": "int",
"name": "str",
"email": "str"
}
}

Fetch and process records [#fetch-and-process-records]

for record in plugin.fetch\_data(config):
print(f"User: \{record\['name']}")

Get schema if available [#get-schema-if-available]

schema = plugin.get\_schema(config)

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;RestAPIPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/sources/rest_api/RestAPIPlugin&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_extract_records&#x22;" type="&#x22;(payload, records_path) -> list[dict[str, Any]]&#x22;">
      Extract record objects from a JSON response payload.

      Parses the JSON response and extracts records based on an optional
      dot-notation path. Supports both list responses (multiple records)
      and object responses (single record).

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Extract from list response::

        payload = \[\{"id": 1}, \{"id": 2}]
        records = \_extract\_records(payload, None)

        Returns: [{"id": 1}, {"id": 2}] [#returns-id-1-id-2]

        Extract from nested response::

        payload = \{"data": \{"users": \[\{"id": 1}, \{"id": 2}]}}
        records = \_extract\_records(payload, "data.users")

        Returns: [{"id": 1}, {"id": 2}] [#returns-id-1-id-2-1]

        Extract single object::

        payload = \{"id": 1, "name": "test"}
        records = \_extract\_records(payload, None)

        Returns: [{"id": 1, "name": "test"}] [#returns-id-1-name-test]

        Path not found::

        payload = \{"data": \{}}
        records = \_extract\_records(payload, "data.missing")

        Raises: ValueError [#raises-valueerror]
      </Callout>

      <PySourceCode>
        ```python
        def _extract_records(payload: Any, records_path: str | None) -> list[dict[str, Any]]:
            """Extract record objects from a JSON response payload.

            Parses the JSON response and extracts records based on an optional
            dot-notation path. Supports both list responses (multiple records)
            and object responses (single record).

            Args:
                payload: Parsed JSON response payload from the API. This should be
                    the result of calling ``response.json()`` on a requests response.
                records_path: Dot-separated path to the list or object records in
                    the payload (e.g., "data.users" or "response.items"). If None,
                    the payload itself is expected to be either a list of records
                    or a single record object.

            Returns:
                list[dict[str, Any]]: Normalized list of record dictionaries.
                If the payload contained a single object, it is wrapped in a list.
                If the payload contained a list, it is returned as-is.

            Raises:
                ValueError: If records_path is specified but the path cannot be
                    traversed in the payload, or if the final payload shape is
                    neither a list nor a dictionary.

            Example:
                Extract from list response::

                    payload = [{"id": 1}, {"id": 2}]
                    records = _extract_records(payload, None)
                    # Returns: [{"id": 1}, {"id": 2}]

                Extract from nested response::

                    payload = {"data": {"users": [{"id": 1}, {"id": 2}]}}
                    records = _extract_records(payload, "data.users")
                    # Returns: [{"id": 1}, {"id": 2}]

                Extract single object::

                    payload = {"id": 1, "name": "test"}
                    records = _extract_records(payload, None)
                    # Returns: [{"id": 1, "name": "test"}]

                Path not found::

                    payload = {"data": {}}
                    records = _extract_records(payload, "data.missing")
                    # Raises: ValueError

            """
            if records_path:
                current = payload
                for key in records_path.split("."):
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        raise ValueError(f"records_path '{records_path}' not found in payload")
                payload = current

            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return [payload]

            raise ValueError("Unsupported payload shape for REST API response")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;payload&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Parsed JSON response payload from the API. This should be
          the result of calling `response.json()` on a requests response.
        </PyParameter>

        <PyParameter name="&#x22;records_path&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Dot-separated path to the list or object records in
          the payload (e.g., "data.users" or "response.items"). If None,
          the payload itself is expected to be either a list of records
          or a single record object.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        list\[dict\[str, Any]]: Normalized list of record dictionaries.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
