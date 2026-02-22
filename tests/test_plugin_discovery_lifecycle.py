"""Regression tests for plugin lifecycle hooks during discovery registration."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from phlo.plugins import PluginMetadata, SourceConnectorPlugin, discover_plugins
from phlo.plugins.discovery import get_global_registry


class _SettingsStub:
    """Test settings stub for plugin discovery."""

    plugins_enabled = True
    plugins_whitelist: list[str] = []
    plugins_blacklist: list[str] = []


class _EntryPointStub:
    """Simple entry point stub for discovery tests."""

    def __init__(self, name: str, plugin: SourceConnectorPlugin) -> None:
        self.name = name
        self.value = f"tests:{name}"
        self._plugin = plugin

    def load(self) -> SourceConnectorPlugin:
        """Return plugin instance for entry point loading."""
        return self._plugin


class _LifecycleSourcePlugin(SourceConnectorPlugin):
    """Source plugin with observable initialize/cleanup lifecycle events."""

    def __init__(
        self,
        marker: str,
        events: list[str],
        *,
        fail_initialize: bool = False,
        fail_cleanup: bool = False,
    ) -> None:
        self.marker = marker
        self._events = events
        self._fail_initialize = fail_initialize
        self._fail_cleanup = fail_cleanup

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata with a stable plugin name for replacement tests."""
        return PluginMetadata(name="lifecycle_source", version=f"1.0.0-{self.marker}")

    def initialize(self, config: dict[str, object]) -> None:
        """Track plugin initialization and optionally fail."""
        self._events.append(f"initialize:{self.marker}")
        if self._fail_initialize:
            raise RuntimeError(f"initialize failed for {self.marker}")

    def cleanup(self) -> None:
        """Track plugin cleanup and optionally fail."""
        self._events.append(f"cleanup:{self.marker}")
        if self._fail_cleanup:
            raise RuntimeError(f"cleanup failed for {self.marker}")

    def fetch_data(self, config: dict[str, object]) -> Iterator[dict[str, int]]:
        """Yield one row to satisfy source plugin interface."""
        yield {"id": 1}


@pytest.fixture
def clean_registry() -> Iterator:
    """Reset global plugin registry around each lifecycle regression test."""
    registry = get_global_registry()
    registry.clear()
    yield registry
    registry.clear()


def _patch_source_entry_points(
    monkeypatch: pytest.MonkeyPatch, entry_points: list[_EntryPointStub]
) -> None:
    """Patch settings and entry point discovery for source connector tests."""

    monkeypatch.setattr("phlo.plugins.discovery.plugins.get_settings", lambda: _SettingsStub())

    def _fake_entry_points(*_args, **kwargs):
        group = kwargs.get("group")
        if group == "phlo.plugins.sources":
            return entry_points
        return []

    monkeypatch.setattr(
        "phlo.plugins.discovery.plugins.importlib.metadata.entry_points",
        _fake_entry_points,
    )


def _capture_plugin_load_errors(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """Capture plugin load errors to assert failure paths are not silent."""
    errors: list[dict[str, object]] = []

    def _capture(event: str, **kwargs: object) -> None:
        if event == "plugin_load_failed":
            errors.append(kwargs)

    monkeypatch.setattr("phlo.plugins.discovery.plugins.logger.error", _capture)
    return errors


def _assert_plugin_load_failed_error(errors: list[dict[str, object]]) -> None:
    """Assert one plugin_load_failed error was emitted for lifecycle regressions."""
    assert len(errors) == 1
    assert errors[0] == {
        "plugin_name": "lifecycle_source",
        "entry_point": "tests:lifecycle_source",
        "plugin_type": "source_connectors",
        "exc_info": True,
    }


def test_discover_plugins_calls_initialize_before_registration(
    clean_registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Initialize is called when discovered plugin registration succeeds."""
    events: list[str] = []
    plugin = _LifecycleSourcePlugin(marker="new", events=events)
    _patch_source_entry_points(
        monkeypatch, [_EntryPointStub(name="lifecycle_source", plugin=plugin)]
    )

    discover_plugins(plugin_type="source_connectors", auto_register=True)

    assert clean_registry.get_source_connector("lifecycle_source") is plugin
    assert events == ["initialize:new"]


def test_discover_plugins_cleans_existing_plugin_before_replacement_registration(
    clean_registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Replacement flow cleans existing plugin before new registration."""
    events: list[str] = []
    existing = _LifecycleSourcePlugin(marker="old", events=events)
    clean_registry.register_source_connector(existing)

    incoming = _LifecycleSourcePlugin(marker="new", events=events)
    _patch_source_entry_points(
        monkeypatch, [_EntryPointStub(name="lifecycle_source", plugin=incoming)]
    )

    register_source_connector = clean_registry.register_source_connector

    def _track_register(plugin: SourceConnectorPlugin, replace: bool = False) -> None:
        events.append(f"register:{plugin.marker}")
        register_source_connector(plugin, replace=replace)

    monkeypatch.setattr(clean_registry, "register_source_connector", _track_register)

    discover_plugins(plugin_type="source_connectors", auto_register=True)

    assert clean_registry.get_source_connector("lifecycle_source") is incoming
    assert events == ["initialize:new", "cleanup:old", "register:new"]


def test_discover_plugins_keeps_existing_plugin_when_cleanup_fails(
    clean_registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cleanup failure during replacement preserves prior registry plugin."""
    events: list[str] = []
    existing = _LifecycleSourcePlugin(marker="old", events=events, fail_cleanup=True)
    clean_registry.register_source_connector(existing)

    incoming = _LifecycleSourcePlugin(marker="new", events=events)
    _patch_source_entry_points(
        monkeypatch, [_EntryPointStub(name="lifecycle_source", plugin=incoming)]
    )
    plugin_load_errors = _capture_plugin_load_errors(monkeypatch)

    discovered = discover_plugins(plugin_type="source_connectors", auto_register=True)

    assert clean_registry.get_source_connector("lifecycle_source") is existing
    assert discovered["source_connectors"] == []
    assert events == ["initialize:new", "cleanup:old", "cleanup:new"]
    _assert_plugin_load_failed_error(plugin_load_errors)


def test_discover_plugins_keeps_existing_plugin_when_initialize_fails(
    clean_registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Initialize failure does not touch existing plugin registration."""
    events: list[str] = []
    existing = _LifecycleSourcePlugin(marker="old", events=events)
    clean_registry.register_source_connector(existing)

    incoming = _LifecycleSourcePlugin(marker="new", events=events, fail_initialize=True)
    _patch_source_entry_points(
        monkeypatch, [_EntryPointStub(name="lifecycle_source", plugin=incoming)]
    )
    plugin_load_errors = _capture_plugin_load_errors(monkeypatch)

    discovered = discover_plugins(plugin_type="source_connectors", auto_register=True)

    assert clean_registry.get_source_connector("lifecycle_source") is existing
    assert discovered["source_connectors"] == []
    assert events == ["initialize:new", "cleanup:new"]
    _assert_plugin_load_failed_error(plugin_load_errors)


def test_discover_plugins_recovers_existing_plugin_on_registration_failure(
    clean_registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Registration failure after cleanup re-initializes existing plugin."""
    events: list[str] = []
    existing = _LifecycleSourcePlugin(marker="old", events=events)
    clean_registry.register_source_connector(existing)

    incoming = _LifecycleSourcePlugin(marker="new", events=events)
    _patch_source_entry_points(
        monkeypatch, [_EntryPointStub(name="lifecycle_source", plugin=incoming)]
    )

    register_source_connector = clean_registry.register_source_connector

    def _failing_register(plugin: SourceConnectorPlugin, replace: bool = False) -> None:
        if plugin is incoming:
            raise RuntimeError("simulated registration failure")
        register_source_connector(plugin, replace=replace)

    monkeypatch.setattr(clean_registry, "register_source_connector", _failing_register)
    plugin_load_errors = _capture_plugin_load_errors(monkeypatch)

    discovered = discover_plugins(plugin_type="source_connectors", auto_register=True)

    assert clean_registry.get_source_connector("lifecycle_source") is existing
    assert discovered["source_connectors"] == []
    assert events == ["initialize:new", "cleanup:old", "initialize:old", "cleanup:new"]
    _assert_plugin_load_failed_error(plugin_load_errors)
