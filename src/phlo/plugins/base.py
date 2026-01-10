"""
Base classes for Phlo plugins.

These abstract base classes define the interfaces that plugins must implement.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from importlib.resources.abc import Traversable
from typing import Any, Callable, Iterable

import click
import pandas as pd

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec, ResourceSpec
from phlo.plugins.observatory import ObservatoryExtensionManifest


@dataclass
class PluginMetadata:
    """Metadata about a plugin."""

    name: str
    """Plugin name (must be unique within plugin type)."""

    version: str
    """Plugin version (semver format)."""

    description: str = ""
    """Human-readable description of the plugin."""

    author: str = ""
    """Plugin author name/organization."""

    license: str = ""
    """Plugin license (e.g., MIT, Apache-2.0)."""

    homepage: str = ""
    """Plugin homepage or repository URL."""

    tags: list[str] = field(default_factory=list)
    """Tags for categorizing/searching plugins."""

    dependencies: list[str] = field(default_factory=list)
    """Python package dependencies required by this plugin."""


class Plugin(ABC):
    """
    Base class for all Phlo plugins.

    All plugin types must inherit from this class and implement
    the required abstract properties and methods.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        Return plugin metadata.

        Returns:
            PluginMetadata with name, version, description, etc.
        """
        pass

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.

        This method is called once when the plugin is loaded.
        Override to perform initialization tasks like:
        - Validating configuration
        - Setting up connections
        - Loading resources

        Args:
            config: Configuration dictionary for the plugin
        """
        pass

    def cleanup(self) -> None:
        """
        Clean up plugin resources.

        This method is called when the plugin is being unloaded.
        Override to perform cleanup tasks like:
        - Closing connections
        - Releasing resources
        - Saving state
        """
        pass


class DagsterExtensionPlugin(Plugin, ABC):
    """
    Base class for Dagster extension plugins.

    These plugins contribute Dagster definitions (assets/resources/schedules/sensors/etc.)
    to the running Phlo instance.
    """

    def get_definitions(self) -> Any:
        """Return Dagster definitions to merge into the global Definitions."""
        try:
            import dagster as dg
        except Exception as exc:  # noqa: BLE001 - optional dependency
            raise RuntimeError("Dagster is required for DagsterExtensionPlugin") from exc
        return dg.Definitions()

    def get_exports(self) -> dict[str, Any]:
        """
        Return exported symbols to attach to the `phlo` public API.

        Example: {"ingestion": phlo_ingestion}
        """
        return {}

    def clear_registries(self) -> None:
        """
        Clear any global registries used by this plugin (primarily for module reload and tests).
        """
        return None


class ObservatoryExtensionPlugin(Plugin, ABC):
    """
    Base class for Observatory UI extension plugins.

    Extensions provide a manifest and a static asset root that the Observatory UI can load
    at runtime.
    """

    @property
    @abstractmethod
    def manifest(self) -> ObservatoryExtensionManifest | dict[str, Any]:
        """Return the extension manifest or a raw manifest dict."""
        raise NotImplementedError

    @property
    @abstractmethod
    def asset_root(self) -> Traversable:
        """Return the root directory that contains the extension assets."""
        raise NotImplementedError

    def get_manifest(self) -> ObservatoryExtensionManifest:
        """Return a validated manifest instance."""
        if isinstance(self.manifest, ObservatoryExtensionManifest):
            return self.manifest
        return ObservatoryExtensionManifest.model_validate(self.manifest)


class IngestionEnginePlugin(DagsterExtensionPlugin, ABC):
    """
    Base class for ingestion engine capability plugins.

    Deprecated in favor of capability specs + orchestrator adapters.
    """

    @abstractmethod
    def get_ingestion_assets(self) -> Iterable[Any]:
        """Return Dagster assets created by the ingestion engine."""
        raise NotImplementedError

    @abstractmethod
    def get_ingestion_decorator(self) -> Callable[..., Any]:
        """Return the decorator used to define ingestion assets."""
        raise NotImplementedError


class CliCommandPlugin(Plugin, ABC):
    """
    Base class for CLI command plugins.

    These plugins contribute Click commands/groups to the `phlo` CLI at runtime.

    Intended use:
    - Capability packages (e.g., `phlo-nessie`, `phlo-openmetadata`) provide their own CLI surface.
    - `phlo` core stays lightweight and only provides the CLI glue + shared utilities.
    """

    @abstractmethod
    def get_cli_commands(self) -> list[click.Command]:
        """Return Click commands/groups to register on the root CLI."""
        raise NotImplementedError


class SourceConnectorPlugin(Plugin, ABC):
    """
    Base class for source connector plugins.

    Source connectors enable ingesting data from external sources
    like APIs, databases, file systems, etc.

    Example:
        ```python
        class GitHubConnector(SourceConnectorPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="github",
                    version="1.0.0",
                    description="Fetch data from GitHub API",
                    author="Phlo Team",
                )

            def fetch_data(self, config: dict) -> Iterator[dict]:
                api_token = config["api_token"]
                repo = config["repo"]

                # Fetch data from GitHub API
                for event in fetch_github_events(api_token, repo):
                    yield event

            def get_schema(self, config: dict) -> dict:
                return {
                    "id": "string",
                    "type": "string",
                    "created_at": "timestamp",
                    "actor": "object",
                }
        ```
    """

    @abstractmethod
    def fetch_data(self, config: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """
        Fetch data from the source.

        This method should yield dictionaries representing individual records.
        It will be called by Phlo's ingestion framework to load data.

        Args:
            config: Configuration for this fetch operation, including:
                - Connection parameters
                - Query/filter parameters
                - Pagination settings
                - Authentication credentials

        Yields:
            Dict representing a single record

        Example:
            ```python
            def fetch_data(self, config: dict) -> Iterator[dict]:
                api_url = config["api_url"]
                api_key = config["api_key"]

                response = requests.get(api_url, headers={"Authorization": f"Bearer {api_key}"})
                for item in response.json()["items"]:
                    yield {
                        "id": item["id"],
                        "value": item["value"],
                        "timestamp": item["created_at"],
                    }
            ```
        """
        pass

    def get_schema(self, config: dict[str, Any]) -> dict[str, str] | None:
        """
        Get the schema of data returned by this connector.

        This method is optional but recommended. It helps with:
        - Type inference
        - Data validation
        - Documentation

        Args:
            config: Configuration for the source

        Returns:
            Dictionary mapping column names to types (e.g., {"id": "string", "count": "int"})
            or None if schema is dynamic/unknown

        Example:
            ```python
            def get_schema(self, config: dict) -> dict:
                return {
                    "id": "string",
                    "temperature": "float",
                    "timestamp": "timestamp",
                    "location": "string",
                }
            ```
        """
        return None

    def test_connection(self, config: dict[str, Any]) -> bool:
        """
        Test if the source is reachable with given configuration.

        This method is optional but recommended for debugging.

        Args:
            config: Configuration to test

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to fetch at least one record
            next(iter(self.fetch_data(config)))
            return True
        except Exception:
            return False


class ServicePlugin(Plugin, ABC):
    """
    Base class for service plugins.

    Service plugins provide Docker-based infrastructure components
    that can be composed into a Phlo stack.
    """

    @property
    @abstractmethod
    def service_definition(self) -> dict[str, Any]:
        """
        Return the service definition.

        This is equivalent to the content of a service.yaml file.
        """
        pass

    @property
    def category(self) -> str:
        """Service category (core, api, bi, observability, etc.)."""
        return self.service_definition.get("category", "custom")

    @property
    def is_default(self) -> bool:
        """Whether this service should be installed by default."""
        return self.service_definition.get("default", False)

    @property
    def profile(self) -> str | None:
        """Optional profile this service belongs to."""
        return self.service_definition.get("profile")

    def get_compose_fragment(self) -> dict[str, Any]:
        """Return Docker Compose service configuration."""
        return self.service_definition.get("compose", {})

    def get_files(self) -> list[dict[str, str]]:
        """Return files to copy during initialization."""
        return self.service_definition.get("files", [])

    def get_dependencies(self) -> list[str]:
        """Return list of service names this depends on."""
        return self.service_definition.get("depends_on", [])


class QualityCheckPlugin(Plugin, ABC):
    """
    Base class for quality check plugins.

    Quality check plugins enable custom data validation logic
    beyond the built-in checks.

    Example:
        ```python
        from phlo_quality.checks import QualityCheck, QualityCheckResult

        class BusinessRuleCheck(QualityCheckPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="business_rule",
                    version="1.0.0",
                    description="Validate business rules",
                )

            def create_check(self, **kwargs) -> QualityCheck:
                rule = kwargs.get("rule")
                return BusinessRuleQualityCheck(rule=rule)


        class BusinessRuleQualityCheck(QualityCheck):
            def __init__(self, rule: str):
                self.rule = rule

            def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
                # Implement rule validation
                violations = df.query(f"not ({self.rule})")

                return QualityCheckResult(
                    passed=len(violations) == 0,
                    metric_name="business_rule",
                    metric_value={"violations": len(violations)},
                )

            @property
            def name(self) -> str:
                return f"business_rule_{self.rule}"
        ```
    """

    @abstractmethod
    def create_check(self, **kwargs) -> Any:
        """
        Create a quality check instance.

        This factory method creates instances of quality checks
        that can be used with @phlo_quality decorator.

        Args:
            **kwargs: Parameters for configuring the check

        Returns:
            QualityCheck instance

        Example:
            ```python
            def create_check(self, column: str, threshold: float) -> QualityCheck:
                return CustomQualityCheck(column=column, threshold=threshold)
            ```
        """
        pass


class TransformationPlugin(Plugin, ABC):
    """
    Base class for transformation plugins.

    Transformation plugins enable custom data processing steps
    that can be composed in data pipelines.

    Example:
        ```python
        class PivotTransform(TransformationPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="pivot",
                    version="1.0.0",
                    description="Pivot table transformation",
                )

            def transform(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
                index = config["index"]
                columns = config["columns"]
                values = config["values"]

                return df.pivot_table(
                    index=index,
                    columns=columns,
                    values=values,
                    aggfunc=config.get("aggfunc", "mean")
                )

            def get_output_schema(self, input_schema: dict, config: dict) -> dict:
                # Return schema of transformed data
                return {...}
        ```
    """

    @abstractmethod
    def transform(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        """
        Transform a DataFrame.

        Args:
            df: Input DataFrame
            config: Configuration for the transformation

        Returns:
            Transformed DataFrame

        Example:
            ```python
            def transform(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
                column = config["column"]
                multiplier = config.get("multiplier", 1.0)

                df = df.copy()
                df[column] = df[column] * multiplier
                return df
            ```
        """
        pass

    def get_output_schema(
        self, input_schema: dict[str, str], config: dict[str, Any]
    ) -> dict[str, str] | None:
        """
        Get the schema of transformed data.

        This method is optional but recommended for type inference.

        Args:
            input_schema: Schema of input DataFrame
            config: Configuration for the transformation

        Returns:
            Schema of output DataFrame or None if unknown
        """
        return None

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate transformation configuration.

        This method is optional but recommended for catching errors early.

        Args:
            config: Configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        return True


class CatalogPlugin(Plugin, ABC):
    """
    Base class for engine-agnostic catalog plugins.

    Catalog plugins define logical catalog configuration that engine adapters
    serialize into their native formats (files or programmatic config).

    Example:
        ```python
        class IcebergCatalogPlugin(CatalogPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="iceberg",
                    version="1.0.0",
                    description="Iceberg catalog with Nessie backend",
                )

            @property
            def targets(self) -> list[str]:
                return ["trino", "spark"]

            @property
            def catalog_name(self) -> str:
                return "iceberg"

            def get_properties(self) -> dict[str, str]:
                return {
                    "connector.name": "iceberg",
                    "iceberg.catalog.type": "rest",
                    "iceberg.rest-catalog.uri": "http://nessie:19120/iceberg",
                }
        ```
    """

    @property
    @abstractmethod
    def targets(self) -> list[str]:
        """
        Return engine identifiers that can consume this catalog.

        Examples: ["trino"], ["spark"], ["trino", "spark"].
        """
        pass

    @property
    @abstractmethod
    def catalog_name(self) -> str:
        """
        Return the catalog name.

        This becomes the catalog identifier in the engine.
        """
        pass

    @abstractmethod
    def get_properties(self) -> dict[str, Any]:
        """
        Return catalog configuration as key-value pairs.

        Returns:
            Dictionary of config key -> value
        """
        pass

    def supports_target(self, target: str) -> bool:
        """Return True if the catalog supports the requested engine target."""
        return target in self.targets


class TrinoCatalogPlugin(CatalogPlugin, ABC):
    """
    Deprecated: use CatalogPlugin with targets=["trino"] instead.
    """

    def __init__(self) -> None:
        warnings.warn(
            "TrinoCatalogPlugin is deprecated; use CatalogPlugin with targets=['trino'].",
            DeprecationWarning,
            stacklevel=2,
        )

    @property
    def targets(self) -> list[str]:
        return ["trino"]


class AssetProviderPlugin(Plugin, ABC):
    """Base class for capability plugins that provide asset specs."""

    @abstractmethod
    def get_assets(self) -> Iterable[AssetSpec]:
        raise NotImplementedError

    def get_checks(self) -> Iterable[AssetCheckSpec]:
        return []


class ResourceProviderPlugin(Plugin, ABC):
    """Base class for plugins that provide resource specs."""

    @abstractmethod
    def get_resources(self) -> Iterable[ResourceSpec]:
        raise NotImplementedError


class OrchestratorAdapterPlugin(Plugin, ABC):
    """Base class for orchestrator adapters."""

    @abstractmethod
    def build_definitions(
        self,
        *,
        assets: Iterable[AssetSpec],
        checks: Iterable[AssetCheckSpec],
        resources: Iterable[ResourceSpec],
    ) -> Any:
        raise NotImplementedError
