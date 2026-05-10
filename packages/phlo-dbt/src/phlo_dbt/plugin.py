"""Phlo plugin implementations for dbt integration.

This module provides the Phlo plugin classes that register dbt capabilities
with the Phlo platform. It includes both an AssetProviderPlugin (for exposing
dbt models as Phlo assets) and a TransformationProviderPlugin (for dbt-based
data transformations).

Example:
    >>> from phlo_dbt.plugin import DbtAssetProvider, DbtTransformationProvider
    >>>
    >>> # Get dbt assets
    >>> asset_provider = DbtAssetProvider()
    >>> assets = asset_provider.get_assets()
    >>>
    >>> # Get transformation provider
    >>> transform_provider = DbtTransformationProvider()
    >>> cli_plugin = transform_provider.get_cli_plugin()

"""

from __future__ import annotations

from collections.abc import Iterable

from phlo.capabilities import (
    WorkflowContributionMode,
    WorkflowWizardContribution,
    WorkflowWizardField,
)
from phlo.capabilities.specs import AssetSpec
from phlo.plugins.base import (
    AssetProviderPlugin,
    PluginMetadata,
    TransformationProviderPlugin,
)

from phlo_dbt.assets import build_dbt_asset_specs


def get_workflow_wizard_contributions() -> list[WorkflowWizardContribution]:
    """Return provider-neutral workflow wizard contributions for dbt."""

    return [
        WorkflowWizardContribution(
            id="dbt.initialize-project",
            package="phlo-dbt",
            stage="transform",
            label="Initialize dbt project",
            description="Create a Phlo-compatible dbt project scaffold if one is missing.",
            required_capabilities=["query_engine"],
            fields=[
                WorkflowWizardField(
                    name="project_name",
                    label="Project name",
                    required=True,
                    description="dbt project name to write into dbt_project.yml.",
                )
            ],
            modes={WorkflowContributionMode.PROPOSAL, WorkflowContributionMode.APPLY},
            metadata={"generator": "phlo_dbt.scaffold.write_dbt_scaffold"},
        ),
        WorkflowWizardContribution(
            id="dbt.basic-model",
            package="phlo-dbt",
            stage="transform",
            label="Create staging model",
            description="Create a basic dbt staging model from the selected source table.",
            required_capabilities=["query_engine"],
            fields=[
                WorkflowWizardField(
                    name="model_name",
                    label="Model name",
                    required=True,
                    description="Name for the generated dbt model.",
                ),
                WorkflowWizardField(
                    name="source_relation",
                    label="Source relation",
                    required=False,
                    description="Optional source relation used in the SQL skeleton.",
                ),
            ],
            modes={WorkflowContributionMode.PROPOSAL, WorkflowContributionMode.APPLY},
            metadata={"generator": "phlo-api workflow wizard dbt model scaffold"},
        ),
        WorkflowWizardContribution(
            id="dbt.source-yml",
            package="phlo-dbt",
            stage="transform",
            label="Create dbt source metadata",
            description="Create source.yml metadata for the selected raw relation.",
            required_capabilities=["query_engine"],
            fields=[
                WorkflowWizardField(
                    name="source_name",
                    label="Source name",
                    required=True,
                    description="dbt source name, usually raw.",
                    default="raw",
                ),
                WorkflowWizardField(
                    name="table_name",
                    label="Table name",
                    required=True,
                    description="Source table exposed to dbt.",
                ),
            ],
            modes={WorkflowContributionMode.PROPOSAL, WorkflowContributionMode.APPLY},
            metadata={"generator": "phlo-api workflow wizard dbt source scaffold"},
        ),
        WorkflowWizardContribution(
            id="dbt.schema-tests",
            package="phlo-dbt",
            stage="transform",
            label="Add model tests",
            description="Create schema.yml tests and model docs for the staging model.",
            required_capabilities=["query_engine"],
            fields=[
                WorkflowWizardField(
                    name="model_name",
                    label="Model name",
                    required=True,
                    description="dbt model to document and test.",
                ),
                WorkflowWizardField(
                    name="unique_key",
                    label="Unique key",
                    required=True,
                    description="Column that should be unique and not null.",
                    default="id",
                ),
            ],
            modes={WorkflowContributionMode.PROPOSAL, WorkflowContributionMode.APPLY},
            metadata={"generator": "phlo-api workflow wizard dbt tests scaffold"},
        ),
    ]


class DbtAssetProvider(AssetProviderPlugin):
    """Asset provider plugin exposing dbt models as Phlo assets.

    This plugin discovers dbt models from the project's manifest and exposes
    them as Phlo AssetSpec objects. This enables dbt models to participate in
    Phlo's orchestration, lineage tracking, and monitoring systems.

    The plugin uses the build_dbt_asset_specs() function to parse the dbt
    manifest and create corresponding asset specifications with proper
    dependencies, metadata, and execution configuration.

    Example:
        >>> from phlo_dbt.plugin import DbtAssetProvider
        >>> provider = DbtAssetProvider()
        >>>
        >>> # Get plugin metadata
        >>> metadata = provider.metadata
        >>> print(f"Plugin: {metadata.name} v{metadata.version}")
        >>>
        >>> # Get dbt assets
        >>> assets = provider.get_assets()
        >>> for asset in assets:
        ...     print(f"Asset: {asset.key}, Group: {asset.group}")

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            Metadata describing the dbt asset provider plugin.

        """
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt models as asset specs",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        """Return dbt-derived asset specifications.

        Returns:
            Iterable of dbt asset specifications.

        """
        return build_dbt_asset_specs()


class DbtTransformationProvider(TransformationProviderPlugin):
    """Transformation provider plugin for dbt.

    This plugin registers dbt as a transformation provider in Phlo, enabling
    dbt models to be executed as part of Phlo's data pipeline transformations.

    The provider supplies both the asset retriever (for discovering transformable
    assets) and the CLI plugin (for dbt-related CLI commands). This allows Phlo
    to integrate dbt runs into its orchestration and provide unified CLI access
    to dbt operations.

    Example:
        >>> from phlo_dbt.plugin import DbtTransformationProvider
        >>> provider = DbtTransformationProvider()
        >>>
        >>> # Get metadata
        >>> metadata = provider.metadata
        >>> print(f"Transform Provider: {metadata.name}")
        >>>
        >>> # Get asset retriever function
        >>> retriever = provider.get_asset_retriever()
        >>> assets = retriever()
        >>>
        >>> # Get CLI plugin for dbt commands
        >>> cli = provider.get_cli_plugin()
        >>> commands = cli.get_cli_commands()

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            Metadata describing the dbt transformation provider plugin.

        """
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt-based transformation provider",
        )

    def get_asset_retriever(self):
        """Return a function to retrieve transformation asset specs.

        Returns:
            Callable that returns dbt asset specifications.

        """
        return build_dbt_asset_specs

    def get_cli_plugin(self):
        """Return the CLI plugin for dbt commands.

        Returns:
            DbtCliPlugin instance for dbt CLI command integration.

        """
        from phlo_dbt.cli_plugin import DbtCliPlugin

        return DbtCliPlugin
