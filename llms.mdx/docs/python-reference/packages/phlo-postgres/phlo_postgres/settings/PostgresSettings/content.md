# PostgresSettings (/docs/python-reference/packages/phlo-postgres/phlo_postgres/settings/PostgresSettings)



PostgreSQL database connection and schema configuration.

Configuration class that manages PostgreSQL connection parameters using
Pydantic validation. Supports environment variable overrides and provides
utilities for building connection strings.

Attributes [#attributes]

<PyAttribute name="&#x22;postgres_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='postgres', description='PostgreSQL host')&#x22;">
  Database server hostname. Can be resolved via environment
  variables and supports special host resolution rules.
</PyAttribute>

<PyAttribute name="&#x22;postgres_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=5432, description='PostgreSQL port')&#x22;">
  Database server port number.
</PyAttribute>

<PyAttribute name="&#x22;postgres_user&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL username')&#x22;">
  Authentication username.
</PyAttribute>

<PyAttribute name="&#x22;postgres_password&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL password')&#x22;">
  Authentication password (URL-encoded in connection strings).
</PyAttribute>

<PyAttribute name="&#x22;postgres_db&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL database name')&#x22;">
  Default database name to connect to.
</PyAttribute>

<PyAttribute name="&#x22;postgres_mart_schema&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='marts', description='Schema for published mart tables')&#x22;">
  Schema name for published data mart tables.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;model_post_init&#x22;" type="&#x22;(self, __context) -> None&#x22;">
  Post-initialization hook for host and port resolution.

  Resolves the postgres\_host and postgres\_port values using phlo's
  network resolution system. This allows for dynamic host resolution
  based on environment variables (e.g., POSTGRES\_PORT for test overrides).

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Uses object.**setattr** to bypass Pydantic's frozen model behavior.
    This ensures the resolved values are stored after initial validation.
  </Callout>

  <PySourceCode>
    ```python
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook for host and port resolution.

        Resolves the postgres_host and postgres_port values using phlo's
        network resolution system. This allows for dynamic host resolution
        based on environment variables (e.g., POSTGRES_PORT for test overrides).

        Args:
            __context: Pydantic model context (unused but required by signature).

        Note:
            Uses object.__setattr__ to bypass Pydantic's frozen model behavior.
            This ensures the resolved values are stored after initial validation.

        """
        host, port = resolve_host(
            self.postgres_host, self.postgres_port, port_env_var="POSTGRES_PORT"
        )
        object.__setattr__(self, "postgres_host", host)
        object.__setattr__(self, "postgres_port", port)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;__context&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Pydantic model context (unused but required by signature).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_postgres_connection_string&#x22;" type="&#x22;(self, include_db=True) -> str&#x22;">
  Build a PostgreSQL connection URI from current settings.

  Constructs a properly URL-encoded PostgreSQL connection string suitable
  for use with SQLAlchemy, psycopg2, or other database libraries.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > settings = PostgresSettings()
    > > > settings.get\_postgres\_connection\_string()
    > > > 'postgresql://phlo:phlo\@postgres:5432/phlo'
    > > >
    > > > Without database (for server-level operations) [#without-database-for-server-level-operations]
    > > >
    > > > settings.get\_postgres\_connection\_string(include\_db=False)
    > > > 'postgresql://phlo:phlo\@postgres:5432'
    > > >
    > > > With special characters in password [#with-special-characters-in-password]
    > > >
    > > > settings = PostgresSettings(postgres\_password="p\@ssw/rd")
    > > > settings.get\_postgres\_connection\_string()
    > > > 'postgresql://phlo:p%40ssw%2Frd\@postgres:5432/phlo'
  </Callout>

  <PySourceCode>
    ```python
    def get_postgres_connection_string(self, include_db: bool = True) -> str:
        """Build a PostgreSQL connection URI from current settings.

        Constructs a properly URL-encoded PostgreSQL connection string suitable
        for use with SQLAlchemy, psycopg2, or other database libraries.

        Args:
            include_db: Whether to include the database name in the connection
                string. Set to False when connecting to the server to create
                the database, or when the database name is specified separately.

        Returns:
            str: URL-encoded PostgreSQL connection string.

        Example:
            >>> settings = PostgresSettings()
            >>> settings.get_postgres_connection_string()
            'postgresql://phlo:phlo@postgres:5432/phlo'
            >>>
            >>> # Without database (for server-level operations)
            >>> settings.get_postgres_connection_string(include_db=False)
            'postgresql://phlo:phlo@postgres:5432'
            >>>
            >>> # With special characters in password
            >>> settings = PostgresSettings(postgres_password="p@ssw/rd")
            >>> settings.get_postgres_connection_string()
            'postgresql://phlo:p%40ssw%2Frd@postgres:5432/phlo'

        """
        db_part = f"/{self.postgres_db}" if include_db else ""
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return f"postgresql://{user}:{password}@{self.postgres_host}:{self.postgres_port}{db_part}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;include_db&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
      Whether to include the database name in the connection
      string. Set to False when connecting to the server to create
      the database, or when the database name is specified separately.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    URL-encoded PostgreSQL connection string.
  </PyFunctionReturn>
</PyFunction>
