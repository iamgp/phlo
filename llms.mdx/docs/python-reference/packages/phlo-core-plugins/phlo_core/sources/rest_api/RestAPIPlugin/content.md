# RestAPIPlugin (/docs/python-reference/packages/phlo-core-plugins/phlo_core/sources/rest_api/RestAPIPlugin)



Generic REST API source connector for fetching data from HTTP endpoints.

This plugin provides a flexible interface for connecting to REST APIs and
extracting data. It handles HTTP request configuration, response parsing,
and error handling automatically.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata containing name, version, description,
  author, and tags for this plugin.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;fetch_data&#x22;" type="&#x22;(self, config)&#x22;">
  Fetch records from a REST API endpoint.

  Makes an HTTP GET request to the configured URL and yields records
  extracted from the response. Handles request configuration, error
  checking, and response parsing automatically.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Fetch data with authentication::

    config = \{
    "url": "[https://api.example.com/users](https://api.example.com/users)",
    "headers": \{"Authorization": "Bearer token123"},
    "timeout": 30
    }

    for user in plugin.fetch\_data(config):
    process\_user(user)

    Fetch nested data from complex response::

    config = \{
    "url": "[https://api.example.com/complex](https://api.example.com/complex)",
    "records\_path": "response.data.records",
    "params": \{"limit": 100}
    }

    records = list(plugin.fetch\_data(config))
  </Callout>

  <PySourceCode>
    ```python
    def fetch_data(self, config: dict[str, Any]):
        """Fetch records from a REST API endpoint.

        Makes an HTTP GET request to the configured URL and yields records
        extracted from the response. Handles request configuration, error
        checking, and response parsing automatically.

        Args:
            config: Source configuration dictionary containing:
                - url (str, required): The API endpoint URL to fetch from.
                - headers (dict, optional): HTTP headers to include in the request.
                    Defaults to empty dict.
                - params (dict, optional): Query parameters to append to the URL.
                    Defaults to empty dict.
                - timeout (int, optional): Request timeout in seconds.
                    Defaults to 30.
                - records_path (str, optional): Dot-separated path to the records
                    within the JSON response. If not provided, assumes the response
                    is either a list of records or a single record object.

        Yields:
            dict[str, Any]: Individual record dictionaries extracted from
            the response payload. Each yielded item represents one record
            ready for processing.

        Raises:
            requests.RequestException: If the HTTP request fails or returns
                a non-2xx status code.
            ValueError: If the records_path is specified but not found in
                the response, or if the payload format is unsupported.

        Example:
            Fetch data with authentication::

                config = {
                    "url": "https://api.example.com/users",
                    "headers": {"Authorization": "Bearer token123"},
                    "timeout": 30
                }

                for user in plugin.fetch_data(config):
                    process_user(user)

            Fetch nested data from complex response::

                config = {
                    "url": "https://api.example.com/complex",
                    "records_path": "response.data.records",
                    "params": {"limit": 100}
                }

                records = list(plugin.fetch_data(config))

        """
        url = config["url"]
        headers = config.get("headers", {})
        params = config.get("params", {})
        timeout = config.get("timeout", 30)
        records_path = config.get("records_path")

        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()

        payload = response.json()
        records = _extract_records(payload, records_path)
        for record in records:
            yield record
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Source configuration dictionary containing:

      * url (str, required): The API endpoint URL to fetch from.
      * headers (dict, optional): HTTP headers to include in the request.
        Defaults to empty dict.
      * params (dict, optional): Query parameters to append to the URL.
        Defaults to empty dict.
      * timeout (int, optional): Request timeout in seconds.
        Defaults to 30.
      * records\_path (str, optional): Dot-separated path to the records
        within the JSON response. If not provided, assumes the response
        is either a list of records or a single record object.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;get_schema&#x22;" type="&#x22;(self, config) -> dict[str, str] | None&#x22;">
  Retrieve optional static schema from configuration.

  Extracts and returns a schema mapping if one was provided in the
  configuration. This allows users to optionally specify expected
  column names and types alongside the source configuration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Get schema from config::

    config = \{
    "url": "[https://api.example.com/data](https://api.example.com/data)",
    "schema": \{
    "id": "int",
    "name": "str",
    "created\_at": "datetime"
    }
    }

    schema = plugin.get\_schema(config)

    Returns: {"id": "int", "name": "str", "created_at": "datetime"} [#returns-id-int-name-str-created_at-datetime]

    Without schema in config::

    config = \{"url": "[https://api.example.com/data"\\}](https://api.example.com/data"\\})
    schema = plugin.get\_schema(config)  # Returns None
  </Callout>

  <PySourceCode>
    ```python
    def get_schema(self, config: dict[str, Any]) -> dict[str, str] | None:
        """Retrieve optional static schema from configuration.

        Extracts and returns a schema mapping if one was provided in the
        configuration. This allows users to optionally specify expected
        column names and types alongside the source configuration.

        Args:
            config: Source configuration dictionary that may include a
                "schema" key mapping column names to type strings.

        Returns:
            dict[str, str] | None: Schema mapping dictionary if present in
            config, where keys are column names and values are type strings.
            Returns None if no schema was configured.

        Example:
            Get schema from config::

                config = {
                    "url": "https://api.example.com/data",
                    "schema": {
                        "id": "int",
                        "name": "str",
                        "created_at": "datetime"
                    }
                }

                schema = plugin.get_schema(config)
                # Returns: {"id": "int", "name": "str", "created_at": "datetime"}

            Without schema in config::

                config = {"url": "https://api.example.com/data"}
                schema = plugin.get_schema(config)  # Returns None

        """
        return config.get("schema")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Source configuration dictionary that may include a
      "schema" key mapping column names to type strings.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, str] | None&#x22;">
    dict\[str, str] | None: Schema mapping dictionary if present in
  </PyFunctionReturn>
</PyFunction>
