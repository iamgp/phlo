"""Unit tests for golden-path runner utility functions.

Tests pure functions from scripts/run_golden_path.py without requiring
Docker or running infrastructure.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, cast

import pytest

# Import the script as a module
_spec = importlib.util.spec_from_file_location(
    "run_golden_path",
    Path(__file__).resolve().parent.parent / "scripts" / "run_golden_path.py",
)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["run_golden_path"] = _mod
_spec.loader.exec_module(_mod)
_mod_any = cast(Any, _mod)

force_remove_directory = _mod_any.force_remove_directory
find_available_port = _mod_any.find_available_port
extract_openmetadata_token = _mod_any.extract_openmetadata_token
read_env_file = _mod_any.read_env_file
upsert_env_file = _mod_any.upsert_env_file
write_file = _mod_any.write_file


class TestForceRemoveDirectory:
    """Tests for `force_remove_directory`."""

    def test_returns_true_for_nonexistent(self, tmp_path: Path) -> None:
        """Verify missing directories are treated as successfully removed.

        Args:
            tmp_path: Temporary path fixture.
        """
        assert force_remove_directory(tmp_path / "nope") is True

    def test_removes_existing_directory(self, tmp_path: Path) -> None:
        """Verify existing directories are deleted.

        Args:
            tmp_path: Temporary path fixture.
        """
        target = tmp_path / "subdir"
        target.mkdir()
        (target / "file.txt").write_text("data")
        assert force_remove_directory(target) is True
        assert not target.exists()


class TestFindAvailablePort:
    """Tests for `find_available_port`."""

    def test_returns_port_when_available(self) -> None:
        """Verify an available port is returned within the search window."""
        port = find_available_port(49200, max_tries=5)
        assert port is not None
        assert 49200 <= port < 49205

    def test_returns_none_when_exhausted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify `None` is returned when all probed ports are unavailable.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        monkeypatch.setattr(_mod, "check_port_in_use", lambda _port: True)
        assert find_available_port(9000, max_tries=3) is None


class TestExtractOpenmetadataToken:
    """Tests for `extract_openmetadata_token`."""

    def test_extracts_access_token(self) -> None:
        """Verify direct `accessToken` values are extracted."""
        assert extract_openmetadata_token({"accessToken": "abc123"}) == "abc123"

    def test_extracts_jwt_token(self) -> None:
        """Verify direct `jwtToken` values are extracted."""
        assert extract_openmetadata_token({"jwtToken": "jwt-val"}) == "jwt-val"

    def test_extracts_nested_token(self) -> None:
        """Verify tokens nested inside dictionaries are extracted."""
        payload = {"data": {"accessToken": "nested-tok"}}
        assert extract_openmetadata_token(payload) == "nested-tok"

    def test_returns_none_for_empty(self) -> None:
        """Verify empty payloads return `None`."""
        assert extract_openmetadata_token({}) is None
        assert extract_openmetadata_token([]) is None

    def test_extracts_from_list(self) -> None:
        """Verify token extraction works for list payloads."""
        assert extract_openmetadata_token([{"token": "list-tok"}]) == "list-tok"


class TestReadEnvFile:
    """Tests for `read_env_file`."""

    def test_parses_key_value_pairs(self, tmp_path: Path) -> None:
        """Verify key-value pairs are parsed from env files.

        Args:
            tmp_path: Temporary path fixture.
        """
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")
        result = read_env_file(env_file)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_comments_and_blanks(self, tmp_path: Path) -> None:
        """Verify comments and blank lines are ignored.

        Args:
            tmp_path: Temporary path fixture.
        """
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\n\nKEY=val\n")
        result = read_env_file(env_file)
        assert result == {"KEY": "val"}

    def test_handles_equals_in_value(self, tmp_path: Path) -> None:
        """Verify values can include `=` characters.

        Args:
            tmp_path: Temporary path fixture.
        """
        env_file = tmp_path / ".env"
        env_file.write_text("DSN=postgres://u:p@host/db?opt=1\n")
        result = read_env_file(env_file)
        assert result["DSN"] == "postgres://u:p@host/db?opt=1"


class TestUpsertEnvFile:
    """Tests for `upsert_env_file`."""

    def test_creates_new_file(self, tmp_path: Path) -> None:
        """Verify upsert creates files when absent.

        Args:
            tmp_path: Temporary path fixture.
        """
        env_file = tmp_path / ".env"
        upsert_env_file(env_file, {"A": "1", "B": "2"})
        result = read_env_file(env_file)
        assert result == {"A": "1", "B": "2"}

    def test_updates_existing_key(self, tmp_path: Path) -> None:
        """Verify existing keys are updated in-place.

        Args:
            tmp_path: Temporary path fixture.
        """
        env_file = tmp_path / ".env"
        env_file.write_text("X=old\nY=keep\n")
        upsert_env_file(env_file, {"X": "new"})
        result = read_env_file(env_file)
        assert result == {"X": "new", "Y": "keep"}

    def test_appends_new_key(self, tmp_path: Path) -> None:
        """Verify new keys are appended when missing.

        Args:
            tmp_path: Temporary path fixture.
        """
        env_file = tmp_path / ".env"
        env_file.write_text("X=1\n")
        upsert_env_file(env_file, {"Z": "3"})
        result = read_env_file(env_file)
        assert result == {"X": "1", "Z": "3"}

    def test_preserves_comments(self, tmp_path: Path) -> None:
        """Verify existing comments remain after updates.

        Args:
            tmp_path: Temporary path fixture.
        """
        env_file = tmp_path / ".env"
        env_file.write_text("# header\nA=1\n")
        upsert_env_file(env_file, {"A": "2"})
        content = env_file.read_text()
        assert "# header" in content


class TestWriteFile:
    """Tests for `write_file`."""

    def test_creates_file_and_parents(self, tmp_path: Path) -> None:
        """Verify file writes create parent directories as needed.

        Args:
            tmp_path: Temporary path fixture.
        """
        target = tmp_path / "deep" / "nested" / "file.txt"
        write_file(target, "hello")
        assert target.read_text() == "hello"
