"""
Local test mode for running tests without Docker.

Enables `phlo test --local` by automatically swapping production resources
with mock implementations backed by DuckDB.

Example:
    >>> os.environ["PHLO_TEST_LOCAL"] = "1"
    >>> # Assets automatically use mocks
"""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from phlo_testing.mock_dlt import MockDLTResource, mock_dlt_source
from phlo_testing.mock_iceberg import MockIcebergCatalog
from phlo_testing.mock_trino import MockTrinoResource


class LocalTestMode:
    """
    Context manager to enable local test mode.

    Replaces production resources with mocks for fast local testing.

    Example:
        >>> with LocalTestMode() as mode:
        ...     # All resources are mocked
        ...     iceberg = mode.iceberg
        ...     trino = mode.trino
    """

    def __init__(
        self,
        fixture_dir: Optional[Path] = None,
        use_recorded_fixtures: bool = False,
    ) -> None:
        """
        Initialize local test mode.

        Args:
            fixture_dir: Directory for fixture recording/playback
            use_recorded_fixtures: Whether to use pre-recorded fixtures
        """
        self.fixture_dir = fixture_dir or Path(tempfile.gettempdir()) / "phlo_test_fixtures"
        self.fixture_dir.mkdir(exist_ok=True)

        self.use_recorded_fixtures = use_recorded_fixtures
        self._original_env: dict[str, Any] = {}
        self._fixtures: dict[str, Any] = {}

        # Initialize mock resources
        self.iceberg = MockIcebergCatalog()
        self.trino = MockTrinoResource()

    def __enter__(self) -> LocalTestMode:
        """Enter local test mode."""
        # Save original environment
        self._original_env = os.environ.copy()

        # Set local test mode flag
        os.environ["PHLO_TEST_LOCAL"] = "1"
        os.environ["PHLO_LOG_LEVEL"] = "DEBUG"

        # Load recorded fixtures if available
        if self.use_recorded_fixtures:
            self._load_fixtures()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit local test mode."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self._original_env)

        # Clean up resources
        self.iceberg.close()
        self.trino.close()

    def record_fixture(self, name: str, data: Any) -> None:
        """
        Record a fixture for later playback.

        Args:
            name: Fixture name
            data: Data to record
        """
        fixture_file = self.fixture_dir / f"{name}.json"

        # Convert to JSON-serializable format
        if hasattr(data, "to_dict"):
            data = data.to_dict()
        elif hasattr(data, "to_json"):
            data = data.to_json()

        with open(fixture_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_fixture(self, name: str) -> Any:
        """
        Load a recorded fixture.

        Args:
            name: Fixture name

        Returns:
            Fixture data

        Raises:
            FileNotFoundError: If fixture doesn't exist
        """
        fixture_file = self.fixture_dir / f"{name}.json"

        if not fixture_file.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_file}")

        with open(fixture_file) as f:
            return json.load(f)

    def _load_fixtures(self) -> None:
        """Load all recorded fixtures."""
        if not self.fixture_dir.exists():
            return

        for fixture_file in self.fixture_dir.glob("*.json"):
            name = fixture_file.stem
            with open(fixture_file) as f:
                self._fixtures[name] = json.load(f)

    def get_resource(self, name: str) -> Any:
        """
        Get a mock resource.

        Args:
            name: Resource name (iceberg, trino)

        Returns:
            Mock resource

        Raises:
            ValueError: If resource doesn't exist
        """
        resources = {
            "iceberg": self.iceberg,
            "trino": self.trino,
        }

        if name not in resources:
            raise ValueError(f"Unknown resource: {name}")

        return resources[name]


@contextmanager
def local_test_mode(
    fixture_dir: Optional[Path] = None,
) -> Iterator[LocalTestMode]:
    """
    Context manager for local test mode.

    Args:
        fixture_dir: Directory for fixtures

    Yields:
        LocalTestMode instance

    Example:
        >>> with local_test_mode() as mode:
        ...     # Test with mocked resources
        ...     table = mode.iceberg.create_table(...)
    """
    mode = LocalTestMode(fixture_dir=fixture_dir)

    with mode:
        yield mode


class LocalTestDecorator:
    """
    Decorator to mark tests that should use local mode.

    Example:
        >>> @local_test
        ... def test_my_asset():
        ...     # Runs with mocked resources
        ...     pass
    """

    def __call__(self, func: Any) -> Any:
        """Apply decorator."""

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with local_test_mode():
                return func(*args, **kwargs)

        return wrapper


# Singleton decorator instance
local_test = LocalTestDecorator()


def is_local_test_mode() -> bool:
    """
    Check if running in local test mode.

    Returns:
        True if PHLO_TEST_LOCAL environment variable is set
    """
    return os.environ.get("PHLO_TEST_LOCAL", "").lower() in ("1", "true")


class FixtureRecorder:
    """
    Helper to record fixtures from real services.

    Captures responses from production services and saves them for
    replay in local mode.

    Example:
        >>> recorder = FixtureRecorder(fixture_dir)
        >>> data = recorder.record_dlt_fetch("users", fetch_users_api)
    """

    def __init__(self, fixture_dir: Optional[Path] = None) -> None:
        """
        Initialize recorder.

        Args:
            fixture_dir: Directory to store fixtures
        """
        self.fixture_dir = fixture_dir or Path(tempfile.gettempdir()) / "phlo_fixtures"
        self.fixture_dir.mkdir(exist_ok=True)

    def record_dlt_source(
        self,
        name: str,
        source_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Record data from a DLT source.

        Args:
            name: Fixture name
            source_func: Function that returns DLT source
            *args: Args to pass to source_func
            **kwargs: Kwargs to pass to source_func

        Returns:
            List of records from source
        """
        # Call source function to get data
        source = source_func(*args, **kwargs)
        data = list(source)

        # Save to fixture
        fixture_file = self.fixture_dir / f"{name}_dlt.json"

        with open(fixture_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return data

    def record_sql_query(
        self,
        name: str,
        query_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Record results from a SQL query.

        Args:
            name: Fixture name
            query_func: Function that executes query
            *args: Args to pass to query_func
            **kwargs: Kwargs to pass to query_func

        Returns:
            Query results
        """
        # Execute query
        results = query_func(*args, **kwargs)

        # Convert to list of dicts if needed
        if hasattr(results, "to_dict"):
            data = results.to_dict("records")
        else:
            data = list(results)

        # Save to fixture
        fixture_file = self.fixture_dir / f"{name}_sql.json"

        with open(fixture_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return data

    def load_dlt_fixture(self, name: str) -> MockDLTResource:
        """
        Load a recorded DLT fixture.

        Args:
            name: Fixture name

        Returns:
            MockDLTResource with recorded data
        """
        fixture_file = self.fixture_dir / f"{name}_dlt.json"

        if not fixture_file.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_file}")

        with open(fixture_file) as f:
            data = json.load(f)

        return mock_dlt_source(data, resource_name=name)

    def get_fixture_dir(self) -> Path:
        """Get fixture directory path."""
        return self.fixture_dir

    def list_fixtures(self) -> list[str]:
        """List all recorded fixtures."""
        if not self.fixture_dir.exists():
            return []

        return sorted(f.stem for f in self.fixture_dir.glob("*.*"))


# Environment variable helpers


def enable_local_test_mode() -> None:
    """Enable local test mode for current process."""
    os.environ["PHLO_TEST_LOCAL"] = "1"


def disable_local_test_mode() -> None:
    """Disable local test mode for current process."""
    os.environ.pop("PHLO_TEST_LOCAL", None)


def set_fixture_dir(path: Path) -> None:
    """Set fixture directory path."""
    os.environ["PHLO_FIXTURE_DIR"] = str(path)


def get_fixture_dir() -> Path:
    """Get fixture directory path."""
    env_path = os.environ.get("PHLO_FIXTURE_DIR")

    if env_path:
        return Path(env_path)

    return Path(tempfile.gettempdir()) / "phlo_fixtures"
