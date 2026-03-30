# SourceConnectorPlugin (/docs/python-reference/core/phlo/plugins/base/source/SourceConnectorPlugin)



Base class for source connector plugins.

Source connectors enable ingesting data from external sources
like APIs, databases, file systems, etc.

Example:

```python
class GitHubConnector(SourceConnectorPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="github",
            version="1.0.0",
            description="Fetch data from GitHub API",
            author="Phlo Team",
        )

    def fetch_data(self, config: dict) -> Iterator[dict]:
        api_token = config["api_token"]
        repo = config["repo"]

        # Fetch data from GitHub API
        for event in fetch_github_events(api_token, repo):
            yield event

    def get_schema(self, config: dict) -> dict:
        return \{
            "id": "string",
            "type": "string",
            "created_at": "timestamp",
            "actor": "object",
        \}
```

Functions [#functions]

<PyFunction name="&#x22;fetch_data&#x22;" type="&#x22;(self, config) -> Iterator[dict[str, Any]]&#x22;">
  Fetch data from the source.

  This method should yield dictionaries representing individual records.
  It will be called by Phlo's ingestion framework to load data.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def fetch_data(self, config: dict) -> Iterator[dict]:
        api_url = config["api_url"]
        api_key = config["api_key"]

        response = requests.get(api_url, headers=\{"Authorization": f"Bearer \{api_key\}"\})
        for item in response.json()["items"]:
            yield \{
                "id": item["id"],
                "value": item["value"],
                "timestamp": item["created_at"],
            \}
    ```
  </Callout>

  <PySourceCode>
    ````python
    @abstractmethod
    def fetch_data(self, config: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """Fetch data from the source.

        This method should yield dictionaries representing individual records.
        It will be called by Phlo's ingestion framework to load data.

        Args:
            config: Configuration for this fetch operation, including:
                - Connection parameters
                - Query/filter parameters
                - Pagination settings
                - Authentication credentials

        Yields:
            Dict representing a single record

        Example:
            \```python
            def fetch_data(self, config: dict) -> Iterator[dict]:
                api_url = config["api_url"]
                api_key = config["api_key"]

                response = requests.get(api_url, headers={"Authorization": f"Bearer {api_key}"})
                for item in response.json()["items"]:
                    yield {
                        "id": item["id"],
                        "value": item["value"],
                        "timestamp": item["created_at"],
                    }
            \```

        """
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Configuration for this fetch operation, including:

      * Connection parameters
      * Query/filter parameters
      * Pagination settings
      * Authentication credentials
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterator[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_schema&#x22;" type="&#x22;(self, config) -> dict[str, str] | None&#x22;">
  Get the schema of data returned by this connector.

  This method is optional but recommended. It helps with:

  * Type inference
  * Data validation
  * Documentation

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def get_schema(self, config: dict) -> dict:
        return \{
            "id": "string",
            "temperature": "float",
            "timestamp": "timestamp",
            "location": "string",
        \}
    ```
  </Callout>

  <PySourceCode>
    ````python
    def get_schema(self, config: dict[str, Any]) -> dict[str, str] | None:
        """Get the schema of data returned by this connector.

        This method is optional but recommended. It helps with:
        - Type inference
        - Data validation
        - Documentation

        Args:
            config: Configuration for the source

        Returns:
            Dictionary mapping column names to types (e.g., {"id": "string", "count": "int"})
            or None if schema is dynamic/unknown

        Example:
            \```python
            def get_schema(self, config: dict) -> dict:
                return {
                    "id": "string",
                    "temperature": "float",
                    "timestamp": "timestamp",
                    "location": "string",
                }
            \```

        """
        return None
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Configuration for the source
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[str, str] | None&#x22;">
    Dictionary mapping column names to types (e.g., \{"id": "string", "count": "int"})
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;test_connection&#x22;" type="&#x22;(self, config) -> bool&#x22;">
  Test if the source is reachable with given configuration.

  This method is optional but recommended for debugging.

  <PySourceCode>
    ```python
    def test_connection(self, config: dict[str, Any]) -> bool:
        """Test if the source is reachable with given configuration.

        This method is optional but recommended for debugging.

        Args:
            config: Configuration to test

        Returns:
            True if connection successful, False otherwise

        """
        try:
            iterator = iter(self.fetch_data(config))
            next(iterator)
            return True
        except StopIteration:
            return True
        except Exception:
            logger.debug("source_connectivity_check_failed")
            return False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Configuration to test
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if connection successful, False otherwise
  </PyFunctionReturn>
</PyFunction>
