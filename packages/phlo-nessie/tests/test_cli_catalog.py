from unittest.mock import MagicMock

import pytest

from phlo_nessie import cli_catalog
from phlo_nessie import catalog_backend


def test_get_iceberg_catalog_loads_catalog_backend(monkeypatch) -> None:
    mock_catalog = MagicMock()
    mock_loader = MagicMock(return_value=mock_catalog)

    monkeypatch.setattr(catalog_backend, "load_pyiceberg_catalog", mock_loader)

    result = cli_catalog._get_iceberg_catalog(ref="dev")

    mock_loader.assert_called_once_with(ref="dev")
    assert result is mock_catalog


def test_get_iceberg_catalog_raises_clear_error_when_backend_missing(monkeypatch) -> None:
    original_import = __import__

    def raising_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "phlo_nessie.catalog_backend":
            raise ImportError("missing backend")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", raising_import)

    with pytest.raises(RuntimeError, match="Iceberg catalog support is not installed"):
        cli_catalog._get_iceberg_catalog()
