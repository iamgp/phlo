"""Unit tests for golden-path runner utility functions.

Tests pure functions from scripts/run_golden_path.py without requiring
Docker or running infrastructure.
"""

import importlib.util
import sys
from pathlib import Path

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

force_remove_directory = _mod.force_remove_directory
find_available_port = _mod.find_available_port
extract_openmetadata_token = _mod.extract_openmetadata_token
read_env_file = _mod.read_env_file
upsert_env_file = _mod.upsert_env_file
write_file = _mod.write_file


class TestForceRemoveDirectory:
    def test_returns_true_for_nonexistent(self, tmp_path: Path) -> None:
        assert force_remove_directory(tmp_path / "nope") is True

    def test_removes_existing_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "subdir"
        target.mkdir()
        (target / "file.txt").write_text("data")
        assert force_remove_directory(target) is True
        assert not target.exists()


class TestFindAvailablePort:
    def test_returns_port_when_available(self) -> None:
        port = find_available_port(49200, max_tries=5)
        assert port is not None
        assert 49200 <= port < 49205

    def test_returns_none_when_exhausted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(_mod, "check_port_in_use", lambda _port: True)
        assert find_available_port(9000, max_tries=3) is None


class TestExtractOpenmetadataToken:
    def test_extracts_access_token(self) -> None:
        assert extract_openmetadata_token({"accessToken": "abc123"}) == "abc123"

    def test_extracts_jwt_token(self) -> None:
        assert extract_openmetadata_token({"jwtToken": "jwt-val"}) == "jwt-val"

    def test_extracts_nested_token(self) -> None:
        payload = {"data": {"accessToken": "nested-tok"}}
        assert extract_openmetadata_token(payload) == "nested-tok"

    def test_returns_none_for_empty(self) -> None:
        assert extract_openmetadata_token({}) is None
        assert extract_openmetadata_token([]) is None

    def test_extracts_from_list(self) -> None:
        assert extract_openmetadata_token([{"token": "list-tok"}]) == "list-tok"


class TestReadEnvFile:
    def test_parses_key_value_pairs(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")
        result = read_env_file(env_file)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_comments_and_blanks(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\n\nKEY=val\n")
        result = read_env_file(env_file)
        assert result == {"KEY": "val"}

    def test_handles_equals_in_value(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("DSN=postgres://u:p@host/db?opt=1\n")
        result = read_env_file(env_file)
        assert result["DSN"] == "postgres://u:p@host/db?opt=1"


class TestUpsertEnvFile:
    def test_creates_new_file(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        upsert_env_file(env_file, {"A": "1", "B": "2"})
        result = read_env_file(env_file)
        assert result == {"A": "1", "B": "2"}

    def test_updates_existing_key(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("X=old\nY=keep\n")
        upsert_env_file(env_file, {"X": "new"})
        result = read_env_file(env_file)
        assert result == {"X": "new", "Y": "keep"}

    def test_appends_new_key(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("X=1\n")
        upsert_env_file(env_file, {"Z": "3"})
        result = read_env_file(env_file)
        assert result == {"X": "1", "Z": "3"}

    def test_preserves_comments(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("# header\nA=1\n")
        upsert_env_file(env_file, {"A": "2"})
        content = env_file.read_text()
        assert "# header" in content


class TestWriteFile:
    def test_creates_file_and_parents(self, tmp_path: Path) -> None:
        target = tmp_path / "deep" / "nested" / "file.txt"
        write_file(target, "hello")
        assert target.read_text() == "hello"
