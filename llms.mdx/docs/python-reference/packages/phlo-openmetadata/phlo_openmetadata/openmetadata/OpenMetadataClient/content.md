# OpenMetadataClient (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/openmetadata/OpenMetadataClient)



Client for OpenMetadata REST API.

Provides methods for interacting with OpenMetadata entities and
publishing metadata, lineage, and quality results.

The client handles authentication automatically and supports connection
pooling via requests.Session.

Attributes [#attributes]

<PyAttribute name="&#x22;base_url&#x22;" type="null" value="&#x22;base_url.rstrip('/')&#x22;">
  Base URL of OpenMetadata API.
</PyAttribute>

<PyAttribute name="&#x22;username&#x22;" type="null" value="&#x22;username&#x22;">
  Authentication username.
</PyAttribute>

<PyAttribute name="&#x22;password&#x22;" type="null" value="&#x22;password&#x22;">
  Authentication password.
</PyAttribute>

<PyAttribute name="&#x22;verify_ssl&#x22;" type="null" value="&#x22;verify_ssl&#x22;">
  Whether to verify SSL certificates.
</PyAttribute>

<PyAttribute name="&#x22;timeout&#x22;" type="null" value="&#x22;timeout&#x22;">
  Request timeout in seconds.
</PyAttribute>

<PyAttribute name="&#x22;service_name&#x22;" type="null" value="&#x22;service_name&#x22;">
  Default service name for operations.
</PyAttribute>

<PyAttribute name="&#x22;service_type&#x22;" type="null" value="&#x22;service_type&#x22;">
  Default service type (e.g., 'Trino').
</PyAttribute>

<PyAttribute name="&#x22;database_name&#x22;" type="null" value="&#x22;database_name&#x22;">
  Default database name.
</PyAttribute>

<PyAttribute name="&#x22;_ensured_services&#x22;" type="&#x22;set[str]&#x22;" value="&#x22;set()&#x22;" />

<PyAttribute name="&#x22;_ensured_databases&#x22;" type="&#x22;set[str]&#x22;" value="&#x22;set()&#x22;" />

<PyAttribute name="&#x22;_ensured_schemas&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;{}&#x22;" />

<PyAttribute name="&#x22;_jwt_token&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;session&#x22;" type="null" value="&#x22;requests.Session()&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, base_url, username, password, verify_ssl=True, timeout=30, service_name=None, service_type=None, database_name=None)&#x22;">
  Initialize OpenMetadata client.

  <PySourceCode>
    ```python
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30,
        service_name: str | None = None,
        service_type: str | None = None,
        database_name: str | None = None,
    ):
        """Initialize OpenMetadata client.

        Args:
            base_url: Base URL of OpenMetadata API (e.g., http://openmetadata:8585/api).
            username: OpenMetadata username.
            password: OpenMetadata password.
            verify_ssl: Whether to verify SSL certificates.
            timeout: Request timeout in seconds.
            service_name: Default service name for operations.
            service_type: Default service type.
            database_name: Default database name.

        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.service_name = service_name
        self.service_type = service_type
        self.database_name = database_name
        self._ensured_services: set[str] = set()
        self._ensured_databases: set[str] = set()
        self._ensured_schemas: dict[str, str] = {}
        self._jwt_token: str | None = None

        # Create session for connection pooling
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.verify = verify_ssl
        self.session.headers.update({"Content-Type": "application/json"})
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;base_url&#x22;" type="&#x22;str&#x22;" value="undefined">
      Base URL of OpenMetadata API (e.g., [http://openmetadata:8585/api](http://openmetadata:8585/api)).
    </PyParameter>

    <PyParameter name="&#x22;username&#x22;" type="&#x22;str&#x22;" value="undefined">
      OpenMetadata username.
    </PyParameter>

    <PyParameter name="&#x22;password&#x22;" type="&#x22;str&#x22;" value="undefined">
      OpenMetadata password.
    </PyParameter>

    <PyParameter name="&#x22;verify_ssl&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether to verify SSL certificates.
    </PyParameter>

    <PyParameter name="&#x22;timeout&#x22;" type="&#x22;int&#x22;" value="&#x22;30&#x22;">
      Request timeout in seconds.
    </PyParameter>

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Default service name for operations.
    </PyParameter>

    <PyParameter name="&#x22;service_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Default service type.
    </PyParameter>

    <PyParameter name="&#x22;database_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Default database name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_request&#x22;" type="&#x22;(self, method, endpoint, data=None, params=None, *, log_errors=True) -> dict[str, Any]&#x22;">
  Make authenticated request to OpenMetadata API.

  <PySourceCode>
    ```python
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        *,
        log_errors: bool = True,
    ) -> dict[str, Any]:
        """Make authenticated request to OpenMetadata API.

        Args:
            method: HTTP method.
            endpoint: API endpoint path.
            data: JSON payload for request body.
            params: Query parameters.
            log_errors: Whether to log request errors.

        Returns:
            Response JSON as dictionary.

        Raises:
            requests_exceptions.RequestException: On request failure.

        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
            )
            if response.status_code == 401:
                if self._jwt_token:
                    self._jwt_token = None
                    self.session.headers.pop("Authorization", None)
                    self.session.auth = HTTPBasicAuth(self.username, self.password)
                if self._authenticate():
                    response = self.session.request(
                        method=method,
                        url=url,
                        json=data,
                        params=params,
                        timeout=self.timeout,
                    )
            response.raise_for_status()
            return response.json() if response.text else {}

        except requests_exceptions.RequestException as exc:
            if log_errors:
                logger.error(
                    "openmetadata_request_failed",
                    method=method,
                    endpoint=endpoint,
                    error=str(exc),
                )
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;method&#x22;" type="&#x22;str&#x22;" value="undefined">
      HTTP method.
    </PyParameter>

    <PyParameter name="&#x22;endpoint&#x22;" type="&#x22;str&#x22;" value="undefined">
      API endpoint path.
    </PyParameter>

    <PyParameter name="&#x22;data&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      JSON payload for request body.
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Query parameters.
    </PyParameter>

    <PyParameter name="&#x22;log_errors&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether to log request errors.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Response JSON as dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_extract_token&#x22;" type="&#x22;(payload) -> Optional[str]&#x22;">
  Extract a bearer token from common OpenMetadata auth responses.

  <PySourceCode>
    ```python
    @staticmethod
    def _extract_token(payload: Any) -> Optional[str]:
        """Extract a bearer token from common OpenMetadata auth responses.

        Args:
            payload: Response payload to search for token.

        Returns:
            JWT token string or None if not found.

        """
        if isinstance(payload, dict):
            for key in ("accessToken", "token", "jwtToken", "idToken"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
            for key in ("data", "result", "response", "auth"):
                if key in payload:
                    token = OpenMetadataClient._extract_token(payload[key])
                    if token:
                        return token
        elif isinstance(payload, list):
            for item in payload:
                token = OpenMetadataClient._extract_token(item)
                if token:
                    return token
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;payload&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Response payload to search for token.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    JWT token string or None if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_authenticate&#x22;" type="&#x22;(self) -> bool&#x22;">
  Attempt to authenticate and store a bearer token for future requests.

  <PySourceCode>
    ```python
    def _authenticate(self) -> bool:
        """Attempt to authenticate and store a bearer token for future requests.

        Returns:
            True if authentication succeeded, False otherwise.

        """
        if self._jwt_token:
            return False

        if not self.username or not self.password:
            return False

        endpoints = ["/v1/users/login", "/v1/auth/login"]
        encoded_password = base64.b64encode(self.password.encode("utf-8")).decode("ascii")
        payloads = [{"email": self.username, "password": encoded_password}]
        if "@" not in self.username:
            payloads.append(
                {"email": f"{self.username}@open-metadata.org", "password": encoded_password}
            )

        for endpoint in endpoints:
            url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
            for payload in payloads:
                try:
                    response = self.session.request(
                        method="POST",
                        url=url,
                        json=payload,
                        timeout=self.timeout,
                        auth=None,
                    )
                except requests_exceptions.RequestException as exc:
                    logger.debug("OpenMetadata auth request failed: %s", exc)
                    continue

                if not (200 <= response.status_code < 300):
                    continue

                data = {}
                if response.text:
                    try:
                        data = response.json()
                    except ValueError:
                        data = {}

                token = self._extract_token(data)
                if token:
                    self._jwt_token = token
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    self.session.auth = None
                    return True

        return False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if authentication succeeded, False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_optional&#x22;" type="&#x22;(self, endpoint) -> Optional[dict[str, Any]]&#x22;">
  GET an endpoint and return None if not found.

  <PySourceCode>
    ```python
    def _get_optional(self, endpoint: str) -> Optional[dict[str, Any]]:
        """GET an endpoint and return None if not found.

        Args:
            endpoint: API endpoint path.

        Returns:
            Response dict or None if 404.

        Raises:
            requests_exceptions.HTTPError: For non-404 errors.

        """
        try:
            return self._request("GET", endpoint)
        except requests_exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;endpoint&#x22;" type="&#x22;str&#x22;" value="undefined">
      API endpoint path.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Response dict or None if 404.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_optional_any&#x22;" type="&#x22;(self, endpoints) -> Optional[dict[str, Any]]&#x22;">
  GET the first available endpoint, return None if all are missing.

  <PySourceCode>
    ```python
    def _get_optional_any(self, endpoints: list[str]) -> Optional[dict[str, Any]]:
        """GET the first available endpoint, return None if all are missing.

        Args:
            endpoints: List of endpoint paths to try.

        Returns:
            Response dict from first available endpoint, or None.

        """
        for endpoint in endpoints:
            try:
                return self._request("GET", endpoint)
            except requests_exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    continue
                raise
        return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;endpoints&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      List of endpoint paths to try.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Response dict from first available endpoint, or None.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_request_fallback&#x22;" type="&#x22;(self, attempts, *, data=None, params=None, retry_statuses=(404, 405), log_errors=True) -> dict[str, Any]&#x22;">
  Try multiple request targets, falling back on specific statuses.

  <PySourceCode>
    ```python
    def _request_fallback(
        self,
        attempts: list[tuple[str, str]],
        *,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        retry_statuses: tuple[int, ...] = (404, 405),
        log_errors: bool = True,
    ) -> dict[str, Any]:
        """Try multiple request targets, falling back on specific statuses.

        Args:
            attempts: List of (method, endpoint) tuples to try.
            data: JSON payload for request body.
            params: Query parameters.
            retry_statuses: Status codes that trigger fallback.
            log_errors: Whether to log errors.

        Returns:
            Response dict from first successful request.

        Raises:
            requests_exceptions.HTTPError: If all attempts fail.

        """
        last_exc: requests_exceptions.HTTPError | None = None
        for method, endpoint in attempts:
            try:
                return self._request(
                    method, endpoint, data=data, params=params, log_errors=log_errors
                )
            except requests_exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status in retry_statuses:
                    last_exc = exc
                    continue
                raise
        if last_exc:
            raise last_exc
        return {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;attempts&#x22;" type="&#x22;list[tuple[str, str]]&#x22;" value="undefined">
      List of (method, endpoint) tuples to try.
    </PyParameter>

    <PyParameter name="&#x22;data&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      JSON payload for request body.
    </PyParameter>

    <PyParameter name="&#x22;params&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Query parameters.
    </PyParameter>

    <PyParameter name="&#x22;retry_statuses&#x22;" type="&#x22;tuple[int, ...]&#x22;" value="&#x22;(404, 405)&#x22;">
      Status codes that trigger fallback.
    </PyParameter>

    <PyParameter name="&#x22;log_errors&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether to log errors.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Response dict from first successful request.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_sanitize_name&#x22;" type="&#x22;(value) -> str&#x22;">
  Sanitize entity names for OpenMetadata compatibility.

  <PySourceCode>
    ```python
    @staticmethod
    def _sanitize_name(value: str) -> str:
        """Sanitize entity names for OpenMetadata compatibility.

        Args:
            value: Raw entity name.

        Returns:
            Sanitized name with only alphanumeric and underscore characters.

        """
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value).strip("_")
        return cleaned or "phlo"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="undefined">
      Raw entity name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Sanitized name with only alphanumeric and underscore characters.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_entity_link&#x22;" type="&#x22;(table_fqn, column=None) -> str&#x22;">
  Build an OpenMetadata entityLink string.

  <PySourceCode>
    ```python
    @staticmethod
    def _build_entity_link(table_fqn: str, column: str | None = None) -> str:
        """Build an OpenMetadata entityLink string.

        Args:
            table_fqn: Fully qualified table name.
            column: Optional column name.

        Returns:
            Entity link string for OpenMetadata.

        """
        if column:
            return f"<#E::table::{table_fqn}::columns::{column}>"
        return f"<#E::table::{table_fqn}>"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name.
    </PyParameter>

    <PyParameter name="&#x22;column&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional column name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Entity link string for OpenMetadata.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;health_check&#x22;" type="&#x22;(self) -> bool&#x22;">
  Check if OpenMetadata is reachable and healthy.

  <PySourceCode>
    ```python
    def health_check(self) -> bool:
        """Check if OpenMetadata is reachable and healthy.

        Returns:
            True if OpenMetadata is healthy, False otherwise.

        """
        endpoints = ["/v1/system/version", "/health"]
        for endpoint in endpoints:
            try:
                response = self.session.request(
                    "GET", urljoin(self.base_url + "/", endpoint.lstrip("/"))
                )
                if response.status_code == 200:
                    return True
            except Exception as exc:
                logger.warning(
                    "openmetadata_health_check_failed",
                    endpoint=endpoint,
                    error=str(exc),
                )
                continue
        return False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if OpenMetadata is healthy, False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_table&#x22;" type="&#x22;(self, table_fqn) -> Optional[dict[str, Any]]&#x22;">
  Get table entity by fully qualified name.

  <PySourceCode>
    ```python
    def get_table(self, table_fqn: str) -> Optional[dict[str, Any]]:
        """Get table entity by fully qualified name.

        Args:
            table_fqn: Fully qualified table name (service.database.schema.table or schema.table).

        Returns:
            Table entity dict or None if not found.

        """
        return self._get_optional(f"/v1/tables/name/{table_fqn}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (service.database.schema.table or schema.table).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Table entity dict or None if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_database_service&#x22;" type="&#x22;(self, name) -> Optional[dict[str, Any]]&#x22;">
  Get database service by name.

  <PySourceCode>
    ```python
    def get_database_service(self, name: str) -> Optional[dict[str, Any]]:
        """Get database service by name.

        Args:
            name: Service name.

        Returns:
            Service entity dict or None if not found.

        """
        return self._get_optional(f"/v1/services/databaseServices/name/{name}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Service name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Service entity dict or None if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_database_service&#x22;" type="&#x22;(self, name, service_type, connection=None) -> dict[str, Any]&#x22;">
  Create a database service.

  <PySourceCode>
    ```python
    def create_database_service(
        self,
        name: str,
        service_type: str,
        connection: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Create a database service.

        Args:
            name: Service name.
            service_type: Service type (e.g., 'Trino', 'Snowflake').
            connection: Optional connection configuration.

        Returns:
            Created service entity dict.

        """
        payload: dict[str, Any] = {"name": name, "serviceType": service_type}
        if connection is not None:
            payload["connection"] = connection
        return self._request("POST", "/v1/services/databaseServices", data=payload)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Service name.
    </PyParameter>

    <PyParameter name="&#x22;service_type&#x22;" type="&#x22;str&#x22;" value="undefined">
      Service type (e.g., 'Trino', 'Snowflake').
    </PyParameter>

    <PyParameter name="&#x22;connection&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Optional connection configuration.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Created service entity dict.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;ensure_database_service&#x22;" type="&#x22;(self, name, service_type=None, connection=None) -> dict[str, Any]&#x22;">
  Ensure database service exists, creating it if needed.

  <PySourceCode>
    ```python
    def ensure_database_service(
        self,
        name: str,
        service_type: Optional[str] = None,
        connection: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Ensure database service exists, creating it if needed.

        Args:
            name: Service name.
            service_type: Service type (uses instance default if not provided).
            connection: Optional connection configuration.

        Returns:
            Existing or created service entity dict.

        Raises:
            ValueError: If service_type is required but not provided.

        """
        if name in self._ensured_services:
            return {"name": name}
        existing = self.get_database_service(name)
        if existing:
            self._ensured_services.add(name)
            return existing
        resolved_type = service_type or self.service_type
        if not resolved_type:
            raise ValueError("service_type is required to create database service")
        created = self.create_database_service(name, resolved_type, connection=connection)
        self._ensured_services.add(name)
        return created
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Service name.
    </PyParameter>

    <PyParameter name="&#x22;service_type&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Service type (uses instance default if not provided).
    </PyParameter>

    <PyParameter name="&#x22;connection&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Optional connection configuration.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Existing or created service entity dict.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_database&#x22;" type="&#x22;(self, database_fqn) -> Optional[dict[str, Any]]&#x22;">
  Get database by fully qualified name.

  <PySourceCode>
    ```python
    def get_database(self, database_fqn: str) -> Optional[dict[str, Any]]:
        """Get database by fully qualified name.

        Args:
            database_fqn: Fully qualified database name.

        Returns:
            Database entity dict or None if not found.

        """
        return self._get_optional(f"/v1/databases/name/{database_fqn}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;database_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified database name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Database entity dict or None if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_database&#x22;" type="&#x22;(self, name, service_fqn) -> dict[str, Any]&#x22;">
  Create a database within a service.

  <PySourceCode>
    ```python
    def create_database(self, name: str, service_fqn: str) -> dict[str, Any]:
        """Create a database within a service.

        Args:
            name: Database name.
            service_fqn: Parent service FQN.

        Returns:
            Created database entity dict.

        """
        payload = {"name": name, "service": service_fqn}
        return self._request("POST", "/v1/databases", data=payload)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Database name.
    </PyParameter>

    <PyParameter name="&#x22;service_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Parent service FQN.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Created database entity dict.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;ensure_database&#x22;" type="&#x22;(self, service_name, database_name) -> dict[str, Any]&#x22;">
  Ensure database exists within a service.

  <PySourceCode>
    ```python
    def ensure_database(self, service_name: str, database_name: str) -> dict[str, Any]:
        """Ensure database exists within a service.

        Args:
            service_name: Parent service name.
            database_name: Database name to ensure.

        Returns:
            Existing or created database entity dict.

        """
        database_fqn = f"{service_name}.{database_name}"
        if database_fqn in self._ensured_databases:
            return {"name": database_name}
        existing = self.get_database(database_fqn)
        if existing:
            self._ensured_databases.add(database_fqn)
            return existing
        created = self.create_database(database_name, service_name)
        self._ensured_databases.add(database_fqn)
        return created
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Parent service name.
    </PyParameter>

    <PyParameter name="&#x22;database_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Database name to ensure.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Existing or created database entity dict.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_database_schema&#x22;" type="&#x22;(self, schema_fqn) -> Optional[dict[str, Any]]&#x22;">
  Get database schema by fully qualified name.

  <PySourceCode>
    ```python
    def get_database_schema(self, schema_fqn: str) -> Optional[dict[str, Any]]:
        """Get database schema by fully qualified name.

        Args:
            schema_fqn: Fully qualified schema name.

        Returns:
            Schema entity dict or None if not found.

        """
        return self._get_optional(f"/v1/databaseSchemas/name/{schema_fqn}")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified schema name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Schema entity dict or None if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_database_schema&#x22;" type="&#x22;(self, name, database_fqn) -> dict[str, Any]&#x22;">
  Create a schema within a database.

  <PySourceCode>
    ```python
    def create_database_schema(self, name: str, database_fqn: str) -> dict[str, Any]:
        """Create a schema within a database.

        Args:
            name: Schema name.
            database_fqn: Parent database FQN.

        Returns:
            Created schema entity dict.

        """
        payload = {"name": name, "database": database_fqn}
        return self._request("POST", "/v1/databaseSchemas", data=payload)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name.
    </PyParameter>

    <PyParameter name="&#x22;database_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Parent database FQN.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Created schema entity dict.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;ensure_database_schema&#x22;" type="&#x22;(self, service_name, database_name, schema_name, *, service_type=None, connection=None) -> dict[str, Any]&#x22;">
  Ensure database schema exists, creating service/database if needed.

  <PySourceCode>
    ```python
    def ensure_database_schema(
        self,
        service_name: str,
        database_name: str,
        schema_name: str,
        *,
        service_type: Optional[str] = None,
        connection: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Ensure database schema exists, creating service/database if needed.

        Args:
            service_name: Service name.
            database_name: Database name.
            schema_name: Schema name to ensure.
            service_type: Optional service type override.
            connection: Optional connection configuration.

        Returns:
            Existing or created schema entity dict.

        """
        schema_fqn = f"{service_name}.{database_name}.{schema_name}"
        cached_id = self._ensured_schemas.get(schema_fqn)
        if cached_id:
            return {"id": cached_id, "name": schema_name}
        self.ensure_database_service(service_name, service_type=service_type, connection=connection)
        self.ensure_database(service_name, database_name)
        existing = self.get_database_schema(schema_fqn)
        if existing:
            schema_id = existing.get("id")
            if isinstance(schema_id, str) and schema_id:
                self._ensured_schemas[schema_fqn] = schema_id
            return existing
        created = self.create_database_schema(schema_name, f"{service_name}.{database_name}")
        created_id = created.get("id") if isinstance(created, dict) else None
        if isinstance(created_id, str) and created_id:
            self._ensured_schemas[schema_fqn] = created_id
        return created
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Service name.
    </PyParameter>

    <PyParameter name="&#x22;database_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Database name.
    </PyParameter>

    <PyParameter name="&#x22;schema_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name to ensure.
    </PyParameter>

    <PyParameter name="&#x22;service_type&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional service type override.
    </PyParameter>

    <PyParameter name="&#x22;connection&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Optional connection configuration.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Existing or created schema entity dict.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_schema_fqn&#x22;" type="&#x22;(self, schema_name, service_name, database_name) -> str&#x22;">
  Build fully qualified schema name.

  <PySourceCode>
    ```python
    def _schema_fqn(
        self,
        schema_name: str,
        service_name: Optional[str],
        database_name: Optional[str],
    ) -> str:
        """Build fully qualified schema name.

        Args:
            schema_name: Schema name.
            service_name: Service name (optional).
            database_name: Database name (optional).

        Returns:
            Fully qualified schema name.

        """
        if service_name and database_name:
            return f"{service_name}.{database_name}.{schema_name}"
        return schema_name
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema name.
    </PyParameter>

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;Optional[str]&#x22;" value="undefined">
      Service name (optional).
    </PyParameter>

    <PyParameter name="&#x22;database_name&#x22;" type="&#x22;Optional[str]&#x22;" value="undefined">
      Database name (optional).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Fully qualified schema name.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;search_tables&#x22;" type="&#x22;(self, query, limit=100) -> list[dict[str, Any]]&#x22;">
  Search for tables matching a query.

  <PySourceCode>
    ```python
    def search_tables(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        """Search for tables matching a query.

        Args:
            query: Search query string.
            limit: Maximum results.

        Returns:
            List of matching table entities.

        """
        result = self._request(
            "GET",
            "/v1/search/query",
            params={"q": query, "index": "table_search_index", "size": limit},
        )
        hits = result.get("hits", {}).get("hits", [])
        return [hit.get("_source", {}) for hit in hits]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      Search query string.
    </PyParameter>

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;100&#x22;">
      Maximum results.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of matching table entities.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_or_update_table&#x22;" type="&#x22;(self, schema_name, table, *, service_name=None, database_name=None, service_type=None) -> dict[str, Any]&#x22;">
  Create or update a table entity in OpenMetadata.

  <PySourceCode>
    ```python
    def create_or_update_table(
        self,
        schema_name: str,
        table: OpenMetadataTable,
        *,
        service_name: Optional[str] = None,
        database_name: Optional[str] = None,
        service_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create or update a table entity in OpenMetadata.

        Args:
            schema_name: Database schema name.
            table: OpenMetadataTable object.
            service_name: Optional service name override.
            database_name: Optional database name override.
            service_type: Optional service type override.

        Returns:
            Created/updated table entity from OpenMetadata.

        """
        resolved_service = service_name or self.service_name
        resolved_database = database_name or self.database_name
        resolved_service_type = service_type or self.service_type

        if resolved_service and resolved_database:
            self.ensure_database_schema(
                resolved_service,
                resolved_database,
                schema_name,
                service_type=resolved_service_type,
            )

        schema_fqn = self._schema_fqn(schema_name, resolved_service, resolved_database)
        payload = table.to_dict()
        payload["databaseSchema"] = schema_fqn

        # OpenMetadata expects CreateTable schema (no id) for upserts via PUT.
        return self._request("PUT", "/v1/tables", data=payload)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Database schema name.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;OpenMetadataTable&#x22;" value="undefined">
      OpenMetadataTable object.
    </PyParameter>

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional service name override.
    </PyParameter>

    <PyParameter name="&#x22;database_name&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional database name override.
    </PyParameter>

    <PyParameter name="&#x22;service_type&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional service type override.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Created/updated table entity from OpenMetadata.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_lineage&#x22;" type="&#x22;(self, from_fqn, to_fqn, description=None) -> dict[str, Any]&#x22;">
  Create lineage edge between two entities.

  <PySourceCode>
    ```python
    def create_lineage(
        self, from_fqn: str, to_fqn: str, description: Optional[str] = None
    ) -> dict[str, Any]:
        """Create lineage edge between two entities.

        Args:
            from_fqn: Source entity FQN.
            to_fqn: Target entity FQN.
            description: Optional edge description.

        Returns:
            Lineage creation result.

        """
        from_entity = self.get_table(from_fqn) or {}
        to_entity = self.get_table(to_fqn) or {}
        from_ref: dict[str, Any] = {"type": "table"}
        to_ref: dict[str, Any] = {"type": "table"}
        if isinstance(from_entity.get("id"), str):
            from_ref["id"] = from_entity["id"]
        else:
            from_ref["fullyQualifiedName"] = from_fqn
        if isinstance(to_entity.get("id"), str):
            to_ref["id"] = to_entity["id"]
        else:
            to_ref["fullyQualifiedName"] = to_fqn

        edge: dict[str, Any] = {"fromEntity": from_ref, "toEntity": to_ref}
        if description:
            edge["description"] = description

        payload = {
            "edge": {
                **edge,
            }
        }
        return self._request("PUT", "/v1/lineage", data=payload)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;from_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Source entity FQN.
    </PyParameter>

    <PyParameter name="&#x22;to_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Target entity FQN.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional edge description.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Lineage creation result.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_databases&#x22;" type="&#x22;(self) -> list[dict[str, Any]]&#x22;">
  List databases from OpenMetadata.

  <PySourceCode>
    ```python
    def list_databases(self) -> list[dict[str, Any]]:
        """List databases from OpenMetadata.

        Returns:
            List of database entities.

        """
        try:
            result = self._request("GET", "/v1/databases")
            data = result.get("data", [])
            return data if isinstance(data, list) else []
        except Exception as exc:
            logger.warning("openmetadata_list_databases_failed", error=str(exc))
            return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of database entities.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;add_owner&#x22;" type="&#x22;(self, table_fqn, owner_name) -> dict[str, Any]&#x22;">
  Set the owner for a table entity.

  <PySourceCode>
    ```python
    def add_owner(self, table_fqn: str, owner_name: str) -> dict[str, Any]:
        """Set the owner for a table entity.

        Args:
            table_fqn: Fully qualified table name.
            owner_name: Name of the owner.

        Returns:
            Updated table entity.

        Raises:
            ValueError: If table not found.

        """
        entity = self.get_table(table_fqn)
        if not entity:
            raise ValueError(f"Table not found: {table_fqn}")

        payload = dict(entity)
        payload["owner"] = {"name": owner_name, "type": "user"}

        return self._request("PUT", "/v1/tables", data=payload)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name.
    </PyParameter>

    <PyParameter name="&#x22;owner_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the owner.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Updated table entity.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_test_definition&#x22;" type="&#x22;(self, test_name, test_type=None, description=None, *, entity_type=None, parameter_definition=None, test_platforms=None) -> dict[str, Any]&#x22;">
  Create a test definition in OpenMetadata.

  <PySourceCode>
    ```python
    def create_test_definition(
        self,
        test_name: str,
        test_type: str | None = None,
        description: Optional[str] = None,
        *,
        entity_type: str | None = None,
        parameter_definition: Optional[list[dict[str, Any]]] = None,
        test_platforms: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Create a test definition in OpenMetadata.

        Args:
            test_name: Name of the test definition.
            test_type: Type of test (e.g., nullCheck, rangeCheck).
            description: Optional description.
            entity_type: Entity type (TABLE or COLUMN).
            parameter_definition: Parameter definitions for the test.
            test_platforms: List of test platforms.

        Returns:
            Created or existing test definition entity.

        """
        resolved_description = description or f"Phlo test definition: {test_name}"
        sanitized_name = self._sanitize_name(test_name)
        data_new: dict[str, Any] = {
            "name": sanitized_name,
            "displayName": test_name,
            "entityType": entity_type or "TABLE",
            "description": resolved_description,
            "testPlatforms": test_platforms or ["OpenMetadata"],
        }
        if parameter_definition is not None:
            data_new["parameterDefinition"] = parameter_definition
        data_new = compact_dict(data_new)

        data_legacy: dict[str, Any] = {
            "name": sanitized_name,
            "displayName": test_name,
            "testType": test_type,
            "description": resolved_description,
        }
        if parameter_definition is not None:
            data_legacy["parameterDefinition"] = parameter_definition
        data_legacy = compact_dict(data_legacy)

        try:
            return self._request_fallback(
                [("POST", "/v1/dataQuality/testDefinitions"), ("POST", "/v1/testDefinitions")],
                data=data_new,
            )
        except requests_exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 409:
                existing = self.get_test_definition(sanitized_name)
                return existing or {}
            if status in (400, 404):
                return self._request("POST", "/v1/testDefinitions", data=data_legacy)
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;test_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name of the test definition.
    </PyParameter>

    <PyParameter name="&#x22;test_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Type of test (e.g., nullCheck, rangeCheck).
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional description.
    </PyParameter>

    <PyParameter name="&#x22;entity_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Entity type (TABLE or COLUMN).
    </PyParameter>

    <PyParameter name="&#x22;parameter_definition&#x22;" type="&#x22;Optional[list[dict[str, Any]]]&#x22;" value="&#x22;None&#x22;">
      Parameter definitions for the test.
    </PyParameter>

    <PyParameter name="&#x22;test_platforms&#x22;" type="&#x22;Optional[list[str]]&#x22;" value="&#x22;None&#x22;">
      List of test platforms.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Created or existing test definition entity.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_test_definition&#x22;" type="&#x22;(self, name) -> Optional[dict[str, Any]]&#x22;">
  Get a test definition by name.

  <PySourceCode>
    ```python
    def get_test_definition(self, name: str) -> Optional[dict[str, Any]]:
        """Get a test definition by name.

        Args:
            name: Test definition name.

        Returns:
            Test definition entity or None if not found.

        """
        sanitized_name = self._sanitize_name(name)
        return self._get_optional_any(
            [
                f"/v1/dataQuality/testDefinitions/name/{sanitized_name}",
                f"/v1/testDefinitions/name/{sanitized_name}",
            ]
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Test definition name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Test definition entity or None if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_test_suite&#x22;" type="&#x22;(self, name) -> Optional[dict[str, Any]]&#x22;">
  Get a test suite by name.

  <PySourceCode>
    ```python
    def get_test_suite(self, name: str) -> Optional[dict[str, Any]]:
        """Get a test suite by name.

        Args:
            name: Test suite name.

        Returns:
            Test suite entity or None if not found.

        """
        return self._get_optional_any([f"/v1/dataQuality/testSuites/name/{name}"])
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Test suite name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Optional&#x22;">
    Test suite entity or None if not found.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_test_suite&#x22;" type="&#x22;(self, name, table_fqn, description=None) -> dict[str, Any]&#x22;">
  Create a test suite for a table.

  <PySourceCode>
    ```python
    def create_test_suite(
        self,
        name: str,
        table_fqn: str,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a test suite for a table.

        Args:
            name: Suite name.
            table_fqn: Table FQN to associate with suite.
            description: Optional description.

        Returns:
            Created test suite entity.

        """
        suite_name = name or f"{table_fqn}.testSuite"
        data: dict[str, Any] = {
            "name": suite_name,
            "basicEntityReference": table_fqn,
            "description": description,
        }
        data = compact_dict(data)
        return self._request("POST", "/v1/dataQuality/testSuites", data=data)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Suite name.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table FQN to associate with suite.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional description.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Created test suite entity.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;ensure_test_suite&#x22;" type="&#x22;(self, name, table_fqn, description=None) -> dict[str, Any]&#x22;">
  Ensure a test suite exists for a table.

  <PySourceCode>
    ```python
    def ensure_test_suite(
        self,
        name: str,
        table_fqn: str,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """Ensure a test suite exists for a table.

        Args:
            name: Suite name.
            table_fqn: Table FQN.
            description: Optional description.

        Returns:
            Existing or created test suite entity.

        """
        suite_name = name or f"{table_fqn}.testSuite"
        existing = self.get_test_suite(suite_name)
        if existing:
            return existing
        try:
            return self.create_test_suite(suite_name, table_fqn, description=description)
        except requests_exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 409:
                existing = self.get_test_suite(suite_name)
                return existing or {"name": suite_name}
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Suite name.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table FQN.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional description.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Existing or created test suite entity.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;create_test_case&#x22;" type="&#x22;(self, test_case_name, table_fqn, test_definition_name, parameters=None, description=None, *, entity_link=None, test_suite_name=None) -> dict[str, Any]&#x22;">
  Create a test case for a table.

  <PySourceCode>
    ```python
    def create_test_case(
        self,
        test_case_name: str,
        table_fqn: str,
        test_definition_name: str,
        parameters: Optional[dict[str, Any]] = None,
        description: Optional[str] = None,
        *,
        entity_link: str | None = None,
        test_suite_name: str | None = None,
    ) -> dict[str, Any]:
        """Create a test case for a table.

        Args:
            test_case_name: Name for the test case.
            table_fqn: Table FQN to test.
            test_definition_name: Associated test definition name.
            parameters: Test parameters as dict.
            description: Optional description.
            entity_link: Optional entity link override.
            test_suite_name: Optional test suite name.

        Returns:
            Created test case entity.

        """
        sanitized_case_name = self._sanitize_name(test_case_name)
        payload: dict[str, Any] = {
            "name": sanitized_case_name,
            "displayName": sanitized_case_name,
            "entityLink": entity_link or self._build_entity_link(table_fqn),
            "testDefinition": self._sanitize_name(test_definition_name),
            "description": description,
        }
        if parameters:
            payload["parameterValues"] = [
                {"name": k, "value": str(v)} for k, v in parameters.items()
            ]

        try:
            return self._request_fallback(
                [("POST", "/v1/dataQuality/testCases"), ("POST", "/v1/testCases")],
                data=payload,
            )
        except requests_exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in (400, 404, 409):
                test_def = self.get_test_definition(test_definition_name)
                if isinstance(test_def, dict):
                    test_def_fqn = test_def.get("fullyQualifiedName") or test_def.get("name")
                    if isinstance(test_def_fqn, str):
                        payload["testDefinition"] = test_def_fqn
                return self._request_fallback(
                    [("POST", "/v1/dataQuality/testCases"), ("POST", "/v1/testCases")],
                    data=payload,
                )
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;test_case_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Name for the test case.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Table FQN to test.
    </PyParameter>

    <PyParameter name="&#x22;test_definition_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Associated test definition name.
    </PyParameter>

    <PyParameter name="&#x22;parameters&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
      Test parameters as dict.
    </PyParameter>

    <PyParameter name="&#x22;description&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional description.
    </PyParameter>

    <PyParameter name="&#x22;entity_link&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional entity link override.
    </PyParameter>

    <PyParameter name="&#x22;test_suite_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional test suite name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Created test case entity.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;publish_test_result&#x22;" type="&#x22;(self, test_case_fqn, result, test_execution_date, result_value=None) -> dict[str, Any]&#x22;">
  Publish a test execution result.

  <PySourceCode>
    ```python
    def publish_test_result(
        self,
        test_case_fqn: str,
        result: str,
        test_execution_date: datetime,
        result_value: Optional[str] = None,
    ) -> dict[str, Any]:
        """Publish a test execution result.

        Args:
            test_case_fqn: Test case FQN.
            result: Test result ('Success' or 'Failed').
            test_execution_date: Execution timestamp.
            result_value: Optional result value/metric.

        Returns:
            Published result response or empty dict if skipped.

        """
        data = {
            "result": result,
            "testCaseStatus": result,
            "timestamp": int(test_execution_date.timestamp() * 1000),
            "result_value": result_value,
        }
        attempts = [
            ("PUT", f"/v1/dataQuality/testCases/{test_case_fqn}/testCaseResult"),
            ("POST", f"/v1/testCases/{test_case_fqn}/testCaseResult"),
            ("PUT", f"/v1/testCases/{test_case_fqn}/testCaseResult"),
        ]
        try:
            return self._request_fallback(attempts, data=data, log_errors=False)
        except requests_exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            body = exc.response.text if exc.response is not None else ""
            if status in (404, 405) or (status == 500 and "Not Found" in body):
                logger.info("OpenMetadata test result endpoint unavailable, skipping.")
                return {}
            raise
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;test_case_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Test case FQN.
    </PyParameter>

    <PyParameter name="&#x22;result&#x22;" type="&#x22;str&#x22;" value="undefined">
      Test result ('Success' or 'Failed').
    </PyParameter>

    <PyParameter name="&#x22;test_execution_date&#x22;" type="&#x22;datetime&#x22;" value="undefined">
      Execution timestamp.
    </PyParameter>

    <PyParameter name="&#x22;result_value&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional result value/metric.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Published result response or empty dict if skipped.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;close&#x22;" type="&#x22;(self) -> None&#x22;">
  Close underlying HTTP session.

  Should be called when done using the client to release connections.

  <PySourceCode>
    ```python
    def close(self) -> None:
        """Close underlying HTTP session.

        Should be called when done using the client to release connections.
        """
        self.session.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;format_timestamp&#x22;" type="&#x22;(dt) -> str&#x22;">
  Format timestamp for OpenMetadata.

  <PySourceCode>
    ```python
    @staticmethod
    def format_timestamp(dt: datetime) -> str:
        """Format timestamp for OpenMetadata.

        Args:
            dt: Datetime to format.

        Returns:
            ISO 8601 formatted string with Z suffix.

        """
        return dt.isoformat() + "Z"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;dt&#x22;" type="&#x22;datetime&#x22;" value="undefined">
      Datetime to format.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    ISO 8601 formatted string with Z suffix.
  </PyFunctionReturn>
</PyFunction>
