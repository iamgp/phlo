"""Sling service and ingestion plugins.

This module provides plugin implementations that integrate Sling replication
capabilities into the Phlo plugin system. It exposes both an AssetProviderPlugin
for discovering Sling-backed assets and an IngestionProviderPlugin for handling
Sling-based data ingestion.

Classes:
    SlingAssetProvider: Provides Sling replication assets to the Phlo runtime.
    SlingIngestionProvider: Provides Sling-based ingestion capabilities.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from phlo.capabilities import (
    WorkflowContributionMode,
    WorkflowWizardContribution,
    WorkflowWizardField,
)
from phlo.capabilities.specs import AssetCheckSpec, AssetSpec
from phlo.plugins.base import AssetProviderPlugin, IngestionProviderPlugin, PluginMetadata

from phlo_sling.decorator import clear_sling_assets, get_sling_assets


def get_workflow_wizard_contributions() -> list[WorkflowWizardContribution]:
    """Return provider-neutral workflow wizard contributions for Sling."""

    return [
        WorkflowWizardContribution(
            id="sling.replication-source",
            package="phlo-sling",
            stage="source",
            label="Sling replication",
            description="Replicate database or file streams into a managed Phlo table.",
            required_capabilities=["table_store"],
            fields=[
                WorkflowWizardField(
                    name="domain",
                    label="Domain",
                    required=True,
                    description="Workflow domain, such as customers or billing.",
                ),
                WorkflowWizardField(
                    name="source_name",
                    label="Source name",
                    required=True,
                    description="Sling source connection name.",
                ),
                WorkflowWizardField(
                    name="source_stream",
                    label="Source stream",
                    required=True,
                    description="Stream, table, or file path to replicate.",
                ),
                WorkflowWizardField(
                    name="target_table",
                    label="Target table",
                    required=True,
                    description="Destination table and generated asset name.",
                ),
                WorkflowWizardField(
                    name="primary_key",
                    label="Primary key",
                    required=True,
                    default="id",
                    description="Column used for incremental replication and deduplication.",
                ),
                WorkflowWizardField(
                    name="replication_mode",
                    label="Replication mode",
                    field_type="select",
                    required=True,
                    default="incremental",
                    options=["incremental", "full-refresh", "snapshot"],
                    description="How Sling should keep the target table in sync.",
                ),
                WorkflowWizardField(
                    name="update_key",
                    label="Update key",
                    required=False,
                    description="Optional cursor column for incremental streams.",
                ),
                WorkflowWizardField(
                    name="schedule",
                    label="Schedule",
                    default="0 2 * * *",
                    description="Cron schedule for the generated replication asset.",
                ),
            ],
            modes={WorkflowContributionMode.PROPOSAL, WorkflowContributionMode.APPLY},
            metadata={"generator": "phlo-api workflow wizard Sling scaffold"},
        )
    ]


class SlingAssetProvider(AssetProviderPlugin):
    """Provide Sling-defined replication assets and checks to Phlo.

    This plugin class discovers and exposes Sling replication assets registered
    via decorators to the Phlo orchestration runtime. It manages the lifecycle
    of Sling asset registrations.

    Attributes:
        metadata (PluginMetadata): Information about this plugin including
            name, version, and description.

    Example:
        The plugin is automatically discovered by the Phlo plugin system::

            # No manual registration needed - discovered via entry points
            assets = SlingAssetProvider().get_assets()

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for discovery and registration.

        Returns:
            PluginMetadata containing name, version, and description of
            this Sling asset provider plugin.

        """
        return PluginMetadata(
            name="sling",
            version="0.1.0",
            description="Sling-based replication engine for Phlo",
        )

    def get_assets(self) -> Iterable[AssetSpec]:
        """Return registered Sling replication assets.

        Retrieves all Sling replication assets that have been registered
        via the @phlo_sling_replication or @phlo_sling_assets decorators.

        Returns:
            Iterable of AssetSpec objects representing registered
            Sling replication pipelines.

        """
        return get_sling_assets()

    def get_checks(self) -> Iterable[AssetCheckSpec]:
        """Return asset checks exposed by this provider.

        Currently, Sling replication assets do not expose any built-in
        asset checks through this provider.

        Returns:
            Empty iterable as no checks are defined.

        """
        return []

    def clear_registries(self) -> None:
        """Clear in-memory Sling replication asset registrations.

        Removes all registered Sling assets from the internal registry.
        This is typically called during testing or plugin reload scenarios.

        Returns:
            None

        """
        clear_sling_assets()


class SlingIngestionProvider(IngestionProviderPlugin):
    """Sling-based ingestion provider for Phlo.

    This plugin class exposes Sling replication as an ingestion mechanism
    within the Phlo platform. It provides the decorator and asset retrieval
    functions needed to define and execute Sling-based data replication.

    Attributes:
        metadata (PluginMetadata): Information about this plugin including
            name, version, and description.

    Example:
        The provider exposes the replication decorator::

            decorator = SlingIngestionProvider().get_decorator()
            @decorator(stream_name="source", table_name="target", ...)
            def my_replication():
                pass

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata containing name, version, and description of
            this Sling ingestion provider plugin.

        """
        return PluginMetadata(
            name="sling",
            version="0.1.0",
            description="Sling-based replication provider with database replication",
        )

    def get_decorator(self) -> Callable:
        """Return the @phlo_sling_replication decorator.

        Returns the decorator function that can be used to register
        Sling-backed replication assets.

        Returns:
            Callable decorator function for registering Sling replication
            definitions.

        """
        from phlo_sling import phlo_sling_replication

        return phlo_sling_replication

    def get_asset_retriever(self) -> Callable[[], list[Any]]:
        """Return function to get registered replication assets.

        Returns a callable that, when invoked, returns the list of all
        registered Sling replication assets.

        Returns:
            Callable that returns a list of registered Sling asset
            specifications.

        """
        return get_sling_assets
