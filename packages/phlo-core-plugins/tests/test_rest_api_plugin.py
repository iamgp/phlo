"""Tests for REST API plugin."""

from phlo_core.sources.rest_api import RestAPIPlugin


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_rest_api_plugin_fetches_records(monkeypatch):
    plugin = RestAPIPlugin()
    payload = [{"id": 1}, {"id": 2}]

    def dummy_get(url, headers=None, params=None, timeout=30):
        return DummyResponse(payload)

    monkeypatch.setattr("phlo_core.sources.rest_api.requests.get", dummy_get)
    records = list(plugin.fetch_data({"url": "https://example.com"}))

    assert records == payload


def test_rest_api_plugin_records_path(monkeypatch):
    plugin = RestAPIPlugin()
    payload = {"data": {"items": [{"id": 3}]}}

    def dummy_get(url, headers=None, params=None, timeout=30):
        return DummyResponse(payload)

    monkeypatch.setattr("phlo_core.sources.rest_api.requests.get", dummy_get)
    records = list(
        plugin.fetch_data({"url": "https://example.com", "records_path": "data.items"})
    )

    assert records == [{"id": 3}]
