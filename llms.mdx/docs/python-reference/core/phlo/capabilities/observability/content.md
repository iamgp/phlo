# observability (/docs/python-reference/core/phlo/capabilities/observability)



Default observability capability provider.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DefaultObservabilityBackend&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/observability/DefaultObservabilityBackend&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;register_default_capability_providers&#x22;" type="&#x22;() -> None&#x22;">
      Register core-owned default maintenance and observability providers.

      <PySourceCode>
        ```python
        def register_default_capability_providers() -> None:
            """Register core-owned default maintenance and observability providers."""
            register_maintenance_read_model(
                MaintenanceReadModelSpec(
                    name="default",
                    provider=DefaultMaintenanceReadModel(),
                )
            )
            register_observability_backend(
                ObservabilityBackendSpec(
                    name="default",
                    provider=DefaultObservabilityBackend(),
                    metadata={
                        "default_stack": ["phlo-otel", "phlo-clickstack"],
                        "service_dependencies": ["clickstack"],
                    },
                    support=CapabilitySupport(
                        supports_metrics=True,
                        supports_logs=True,
                        supports_dashboards=True,
                        supports_alerts=True,
                    ),
                )
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_service_base_url&#x22;" type="&#x22;(service_name, *, public_url_env, port_env_key) -> str | None&#x22;">
      <PySourceCode>
        ```python
        def _resolve_service_base_url(
            service_name: str,
            *,
            public_url_env: str,
            port_env_key: str,
        ) -> str | None:
            public_url = _service_env_value(service_name, public_url_env)
            if public_url:
                return public_url.rstrip("/")

            port = _service_env_value(service_name, port_env_key)
            if port is None:
                return None

            host = os.environ.get(_PUBLIC_HOST_ENV, "localhost")
            scheme = os.environ.get(_PUBLIC_SCHEME_ENV, "http")
            return f"{scheme}://{host}:{port}"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;public_url_env&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;port_env_key&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_service_env_value&#x22;" type="&#x22;(service_name, key) -> str | None&#x22;">
      <PySourceCode>
        ```python
        def _service_env_value(service_name: str, key: str) -> str | None:
            env_value = os.environ.get(key)
            if env_value:
                return env_value

            service = _discover_service(service_name)
            if service is None:
                return None

            payload = service.env_vars.get(key, {})
            default = payload.get("default")
            if default in (None, ""):
                return None
            return str(default)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_discover_service&#x22;" type="&#x22;(service_name)&#x22;">
      <PySourceCode>
        ```python
        def _discover_service(service_name: str):
            try:
                from phlo.plugins.discovery import ServiceDiscovery

                return ServiceDiscovery().get_service(service_name)
            except Exception:
                return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;_discover_grafana_dashboards&#x22;" type="&#x22;() -> list[dict[str, str]]&#x22;">
      <PySourceCode>
        ```python
        def _discover_grafana_dashboards() -> list[dict[str, str]]:
            service = _discover_service("grafana")
            if service is None or service.source_path is None:
                return []

            dashboards_dir = service.source_path / "dashboards"
            if not dashboards_dir.exists():
                return []

            dashboards: list[dict[str, str]] = []
            for dashboard_path in sorted(dashboards_dir.glob("*.json")):
                payload = _load_dashboard_payload(dashboard_path)
                if payload is None:
                    continue
                uid = payload.get("uid")
                title = payload.get("title")
                if isinstance(uid, str) and isinstance(title, str):
                    dashboards.append({"uid": uid, "title": title})
            return dashboards
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[dict[str, str]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_dashboard_payload&#x22;" type="&#x22;(path) -> dict[str, object] | None&#x22;">
      <PySourceCode>
        ```python
        def _load_dashboard_payload(path: Path) -> dict[str, object] | None:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None
            if not isinstance(payload, dict):
                return None
            return payload
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, object] | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_dashboard_category&#x22;" type="&#x22;(title) -> str&#x22;">
      <PySourceCode>
        ```python
        def _dashboard_category(title: str) -> str:
            lowered = title.lower()
            if "overview" in lowered:
                return "overview"
            if "infrastructure" in lowered:
                return "infrastructure"
            return "dashboard"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;title&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_join_url&#x22;" type="&#x22;(base_url, path) -> str&#x22;">
      <PySourceCode>
        ```python
        def _join_url(base_url: str, path: str) -> str:
            normalized_path = path if path.startswith("/") else f"/{path}"
            if normalized_path == "/":
                return base_url.rstrip("/")
            return f"{base_url.rstrip('/')}{normalized_path}"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;base_url&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;path&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_append_query_params&#x22;" type="&#x22;(url, **params) -> str&#x22;">
      <PySourceCode>
        ```python
        def _append_query_params(url: str, **params: str | None) -> str:
            split_result = urlsplit(url)
            query_params = dict(parse_qsl(split_result.query, keep_blank_values=True))
            query_params.update({key: value for key, value in params.items() if value is not None})
            return urlunsplit(
                (
                    split_result.scheme,
                    split_result.netloc,
                    split_result.path,
                    urlencode(query_params),
                    split_result.fragment,
                )
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;url&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;params&#x22;" type="&#x22;str | None&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
