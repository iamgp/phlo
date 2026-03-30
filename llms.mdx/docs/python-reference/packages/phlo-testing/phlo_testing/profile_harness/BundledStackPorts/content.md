# BundledStackPorts (/docs/python-reference/packages/phlo-testing/phlo_testing/profile_harness/BundledStackPorts)



Resolved host ports for the bundled-stack contract harness.

Attributes [#attributes]

<PyAttribute name="&#x22;phlo_api&#x22;" type="&#x22;int&#x22;" value="null">
  Port for Phlo API service.
</PyAttribute>

<PyAttribute name="&#x22;dagster&#x22;" type="&#x22;int&#x22;" value="null">
  Port for Dagster webserver.
</PyAttribute>

<PyAttribute name="&#x22;observatory&#x22;" type="&#x22;int&#x22;" value="&#x22;3001&#x22;">
  Port for Observatory UI (default: 3001).
</PyAttribute>

<PyAttribute name="&#x22;hasura&#x22;" type="&#x22;int&#x22;" value="&#x22;8082&#x22;">
  Port for Hasura GraphQL (default: 8082).
</PyAttribute>

<PyAttribute name="&#x22;postgrest&#x22;" type="&#x22;int&#x22;" value="&#x22;3002&#x22;">
  Port for PostgREST API (default: 3002).
</PyAttribute>

<PyAttribute name="&#x22;pgweb&#x22;" type="&#x22;int&#x22;" value="&#x22;8081&#x22;">
  Port for pgweb UI (default: 8081).
</PyAttribute>

<PyAttribute name="&#x22;postgres&#x22;" type="&#x22;int&#x22;" value="&#x22;5432&#x22;">
  Port for PostgreSQL (default: 5432).
</PyAttribute>

<PyAttribute name="&#x22;trino&#x22;" type="&#x22;int&#x22;" value="&#x22;8080&#x22;">
  Port for Trino (default: 8080).
</PyAttribute>

<PyAttribute name="&#x22;minio_api&#x22;" type="&#x22;int&#x22;" value="&#x22;9000&#x22;">
  Port for MinIO API (default: 9000).
</PyAttribute>

<PyAttribute name="&#x22;minio_console&#x22;" type="&#x22;int&#x22;" value="&#x22;9001&#x22;">
  Port for MinIO Console (default: 9001).
</PyAttribute>

<PyAttribute name="&#x22;nessie&#x22;" type="&#x22;int&#x22;" value="&#x22;19120&#x22;">
  Port for Nessie catalog (default: 19120).
</PyAttribute>

<PyAttribute name="&#x22;prometheus&#x22;" type="&#x22;int&#x22;" value="&#x22;9090&#x22;">
  Port for Prometheus (default: 9090).
</PyAttribute>

<PyAttribute name="&#x22;loki&#x22;" type="&#x22;int&#x22;" value="&#x22;3100&#x22;">
  Port for Loki logging (default: 3100).
</PyAttribute>

<PyAttribute name="&#x22;grafana&#x22;" type="&#x22;int&#x22;" value="&#x22;3003&#x22;">
  Port for Grafana (default: 3003).
</PyAttribute>

<PyAttribute name="&#x22;alloy&#x22;" type="&#x22;int&#x22;" value="&#x22;12345&#x22;">
  Port for Alloy (default: 12345).
</PyAttribute>

<PyAttribute name="&#x22;superset&#x22;" type="&#x22;int&#x22;" value="&#x22;8088&#x22;">
  Port for Superset (default: 8088).
</PyAttribute>

<PyAttribute name="&#x22;openmetadata&#x22;" type="&#x22;int&#x22;" value="&#x22;8585&#x22;">
  Port for OpenMetadata (default: 8585).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;from_env&#x22;" type="&#x22;(cls, env_vars) -> BundledStackPorts&#x22;">
  Create BundledStackPorts from environment variables.

  <PySourceCode>
    ```python
    @classmethod
    def from_env(cls, env_vars: dict[str, str]) -> BundledStackPorts:
        """Create BundledStackPorts from environment variables.

        Args:
            env_vars: Dictionary of environment variables.

        Returns:
            BundledStackPorts instance with ports from environment.

        """
        return cls(
            phlo_api=int(env_vars.get("PHLO_API_PORT", "54000")),
            dagster=int(env_vars.get("DAGSTER_PORT", "3000")),
            observatory=int(env_vars.get("OBSERVATORY_PORT", "3001")),
            hasura=int(env_vars.get("HASURA_PORT", "8082")),
            postgrest=int(env_vars.get("POSTGREST_PORT", "3002")),
            pgweb=int(env_vars.get("PGWEB_PORT", "8081")),
            postgres=int(env_vars.get("POSTGRES_PORT", "5432")),
            trino=int(env_vars.get("TRINO_PORT", "8080")),
            minio_api=int(env_vars.get("MINIO_API_PORT", "9000")),
            minio_console=int(env_vars.get("MINIO_CONSOLE_PORT", "9001")),
            nessie=int(env_vars.get("NESSIE_PORT", "19120")),
            prometheus=int(env_vars.get("PROMETHEUS_PORT", "9090")),
            loki=int(env_vars.get("LOKI_PORT", "3100")),
            grafana=int(env_vars.get("GRAFANA_PORT", "3003")),
            alloy=int(env_vars.get("ALLOY_PORT", "12345")),
            superset=int(env_vars.get("SUPERSET_PORT", "8088")),
            openmetadata=int(env_vars.get("OPENMETADATA_PORT", "8585")),
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;env_vars&#x22;" type="&#x22;dict[str, str]&#x22;" value="undefined">
      Dictionary of environment variables.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.profile_harness.BundledStackPorts&#x22;">
    BundledStackPorts instance with ports from environment.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, phlo_api, dagster, observatory=3001, hasura=8082, postgrest=3002, pgweb=8081, postgres=5432, trino=8080, minio_api=9000, minio_console=9001, nessie=19120, prometheus=9090, loki=3100, grafana=3003, alloy=12345, superset=8088, openmetadata=8585) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;phlo_api&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;dagster&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;observatory&#x22;" type="&#x22;int&#x22;" value="&#x22;3001&#x22;" />

    <PyParameter name="&#x22;hasura&#x22;" type="&#x22;int&#x22;" value="&#x22;8082&#x22;" />

    <PyParameter name="&#x22;postgrest&#x22;" type="&#x22;int&#x22;" value="&#x22;3002&#x22;" />

    <PyParameter name="&#x22;pgweb&#x22;" type="&#x22;int&#x22;" value="&#x22;8081&#x22;" />

    <PyParameter name="&#x22;postgres&#x22;" type="&#x22;int&#x22;" value="&#x22;5432&#x22;" />

    <PyParameter name="&#x22;trino&#x22;" type="&#x22;int&#x22;" value="&#x22;8080&#x22;" />

    <PyParameter name="&#x22;minio_api&#x22;" type="&#x22;int&#x22;" value="&#x22;9000&#x22;" />

    <PyParameter name="&#x22;minio_console&#x22;" type="&#x22;int&#x22;" value="&#x22;9001&#x22;" />

    <PyParameter name="&#x22;nessie&#x22;" type="&#x22;int&#x22;" value="&#x22;19120&#x22;" />

    <PyParameter name="&#x22;prometheus&#x22;" type="&#x22;int&#x22;" value="&#x22;9090&#x22;" />

    <PyParameter name="&#x22;loki&#x22;" type="&#x22;int&#x22;" value="&#x22;3100&#x22;" />

    <PyParameter name="&#x22;grafana&#x22;" type="&#x22;int&#x22;" value="&#x22;3003&#x22;" />

    <PyParameter name="&#x22;alloy&#x22;" type="&#x22;int&#x22;" value="&#x22;12345&#x22;" />

    <PyParameter name="&#x22;superset&#x22;" type="&#x22;int&#x22;" value="&#x22;8088&#x22;" />

    <PyParameter name="&#x22;openmetadata&#x22;" type="&#x22;int&#x22;" value="&#x22;8585&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
