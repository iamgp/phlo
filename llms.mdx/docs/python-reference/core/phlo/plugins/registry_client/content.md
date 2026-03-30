# registry_client (/docs/python-reference/core/phlo/plugins/registry_client)



Registry client for Phlo plugins.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;RegistryPlugin&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/registry_client/RegistryPlugin&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_is_cache_valid&#x22;" type="&#x22;(now, ttl_seconds) -> bool&#x22;">
      <PySourceCode>
        ```python
        def _is_cache_valid(now: float, ttl_seconds: int) -> bool:
            if not _REGISTRY_CACHE["data"]:
                return False
            return (now - _REGISTRY_CACHE["loaded_at"]) < ttl_seconds
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;now&#x22;" type="&#x22;float&#x22;" value="null" />

        <PyParameter name="&#x22;ttl_seconds&#x22;" type="&#x22;int&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_normalize_registry&#x22;" type="&#x22;(registry) -> list[RegistryPlugin]&#x22;">
      <PySourceCode>
        ```python
        def _normalize_registry(registry: dict[str, Any]) -> list[RegistryPlugin]:
            return [
                RegistryPlugin(
                    name=name,
                    type=info.get("type", ""),
                    package=info.get("package", ""),
                    version=info.get("version", ""),
                    description=info.get("description", ""),
                    author=info.get("author", ""),
                    homepage=info.get("homepage"),
                    tags=list(info.get("tags", [])),
                    verified=bool(info.get("verified", False)),
                    core=bool(info.get("core", False)),
                )
                for name, info in registry.get("plugins", {}).items()
            ]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;registry&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[phlo.plugins.registry_client.RegistryPlugin]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_registry_from_package&#x22;" type="&#x22;() -> dict[str, Any]&#x22;">
      <PySourceCode>
        ```python
        def _load_registry_from_package() -> dict[str, Any]:
            registry_path = resources.files("phlo.plugins").joinpath("registry_data.json")
            return json.loads(registry_path.read_text(encoding="utf-8"))
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_registry_from_repo&#x22;" type="&#x22;() -> dict[str, Any] | None&#x22;">
      <PySourceCode>
        ```python
        def _load_registry_from_repo() -> dict[str, Any] | None:
            current = Path(__file__).resolve()
            for parent in current.parents:
                candidate = parent / "registry" / "plugins.json"
                if candidate.exists():
                    return json.loads(candidate.read_text(encoding="utf-8"))
            return None
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any] | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_load_registry_from_local&#x22;" type="&#x22;() -> dict[str, Any]&#x22;">
      <PySourceCode>
        ```python
        def _load_registry_from_local() -> dict[str, Any]:
            try:
                return _load_registry_from_package()
            except Exception as exc:
                logger.debug("Failed to load registry from package: %s", exc)

            repo_registry = _load_registry_from_repo()
            if repo_registry:
                return repo_registry

            raise FileNotFoundError("No bundled registry data found.")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_validate_registry&#x22;" type="&#x22;(registry) -> None&#x22;">
      <PySourceCode>
        ```python
        def _validate_registry(registry: dict[str, Any]) -> None:
            if not isinstance(registry, dict) or "plugins" not in registry:
                raise ValueError("Registry payload missing plugins section.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;registry&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;clear_registry_cache&#x22;" type="&#x22;() -> None&#x22;">
      Clear registry cache (useful for tests).

      <PySourceCode>
        ```python
        def clear_registry_cache() -> None:
            """Clear registry cache (useful for tests)."""
            _REGISTRY_CACHE["loaded_at"] = 0.0
            _REGISTRY_CACHE["data"] = None
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;fetch_registry&#x22;" type="&#x22;(force_refresh=False) -> dict[str, Any]&#x22;">
      Fetch the plugin registry with caching.

      Falls back to bundled registry data if network fetch fails.

      <PySourceCode>
        ```python
        def fetch_registry(force_refresh: bool = False) -> dict[str, Any]:
            """
            Fetch the plugin registry with caching.

            Falls back to bundled registry data if network fetch fails.
            """
            settings = get_settings()
            ttl_seconds = settings.plugin_registry_cache_ttl_seconds
            now = time.time()
            started = time.perf_counter()
            registry_url = settings.plugin_registry_url

            logger.debug(
                "plugin_registry_fetch_started",
                force_refresh=force_refresh,
                has_registry_url=bool(registry_url),
            )

            if not force_refresh and _is_cache_valid(now, ttl_seconds):
                logger.debug(
                    "plugin_registry_fetch_completed",
                    source="cache",
                    force_refresh=force_refresh,
                    plugin_count=len(_REGISTRY_CACHE["data"].get("plugins", {})),
                    elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
                )
                return _REGISTRY_CACHE["data"]

            registry = None
            source = "local"
            if registry_url:
                try:
                    response = requests.get(registry_url, timeout=settings.plugin_registry_timeout_seconds)
                    response.raise_for_status()
                    registry = response.json()
                    _validate_registry(registry)
                    source = "remote"
                except Exception as exc:
                    logger.warning(
                        "plugin_registry_fetch_fallback",
                        registry_url=registry_url,
                        error=str(exc),
                    )

            if registry is None:
                registry = _load_registry_from_local()
                _validate_registry(registry)

            _REGISTRY_CACHE["loaded_at"] = now
            _REGISTRY_CACHE["data"] = registry
            logger.debug(
                "plugin_registry_fetch_completed",
                source=source,
                force_refresh=force_refresh,
                plugin_count=len(registry.get("plugins", {})),
                elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
                cache_ttl_seconds=ttl_seconds,
            )
            return registry
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;force_refresh&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;list_registry_plugins&#x22;" type="&#x22;() -> list[RegistryPlugin]&#x22;">
      Return all registry plugins as normalized entries.

      <PySourceCode>
        ```python
        def list_registry_plugins() -> list[RegistryPlugin]:
            """Return all registry plugins as normalized entries."""
            registry = fetch_registry()
            return _normalize_registry(registry)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[phlo.plugins.registry_client.RegistryPlugin]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_registry_data&#x22;" type="&#x22;() -> dict[str, Any]&#x22;">
      Return raw registry data payload.

      <PySourceCode>
        ```python
        def get_registry_data() -> dict[str, Any]:
            """Return raw registry data payload."""
            return fetch_registry()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_plugin&#x22;" type="&#x22;(name) -> RegistryPlugin | None&#x22;">
      Return a single plugin entry by name.

      <PySourceCode>
        ```python
        def get_plugin(name: str) -> RegistryPlugin | None:
            """Return a single plugin entry by name."""
            registry = fetch_registry()
            info = registry.get("plugins", {}).get(name)
            if not info:
                return None
            return _normalize_registry({"plugins": {name: info}})[0]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.plugins.registry_client.RegistryPlugin | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;search_plugins&#x22;" type="&#x22;(query=None, plugin_type=None, tags=None) -> list[RegistryPlugin]&#x22;">
      Search registry plugins by name, description, type, or tags.

      <PySourceCode>
        ```python
        def search_plugins(
            query: str | None = None,
            plugin_type: str | None = None,
            tags: list[str] | None = None,
        ) -> list[RegistryPlugin]:
            """Search registry plugins by name, description, type, or tags."""
            plugins = list_registry_plugins()

            if plugin_type:
                plugins = [plugin for plugin in plugins if plugin.type == plugin_type]

            if tags:
                tag_set = {tag.lower() for tag in tags}
                plugins = [
                    plugin for plugin in plugins if tag_set.issubset({tag.lower() for tag in plugin.tags})
                ]

            if query:
                query_lower = query.lower()
                plugins = [
                    p
                    for p in plugins
                    if any(
                        query_lower in text.lower() for text in (p.name, p.description, p.package, *p.tags)
                    )
                ]

            return plugins
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;tags&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;list[phlo.plugins.registry_client.RegistryPlugin]&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
