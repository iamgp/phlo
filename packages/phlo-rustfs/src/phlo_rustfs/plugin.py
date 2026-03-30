"""RustFS service plugin.

This module implements Phlo plugins for integrating RustFS into the service mesh.
It provides service definitions for running RustFS containers and initializing
buckets, plus resource providers that expose S3-compatible object storage
capabilities to other components.

Classes:
    RustfsServicePlugin: Main service plugin for the RustFS container.
    RustfsSetupServicePlugin: Service plugin for bucket initialization.
    RustfsObjectStoreProvider: Capability provider for S3 storage.
    RustfsResourceProvider: Resource provider exposing object store specs.

Functions:
    _load_service_definition: Loads YAML service definitions from package resources.
"""

from __future__ import annotations

from importlib import resources
from time import perf_counter
from typing import Any

import yaml

from phlo.capabilities import ObjectStoreSpec, ResourceSpec
from phlo.logging import get_logger
from phlo.plugins import PluginMetadata, ResourceProviderPlugin, ServicePlugin

logger = get_logger(__name__)


def _load_service_definition(resource_name: str, service_name: str) -> dict[str, Any]:
    """Load a YAML service definition from package resources.

    Reads a YAML file containing Docker Compose-style service definitions
    from the phlo_rustfs package resources. Includes structured logging
    for performance monitoring and error tracking.

    Args:
        resource_name: Name of the YAML resource file to load.
        service_name: Logical name of the service for logging purposes.

    Returns:
        Dictionary containing the parsed YAML service definition.

    Raises:
        Exception: If the YAML file cannot be read or parsed.

    Example:
        >>> definition = _load_service_definition("service.yaml", "rustfs")
        >>> print(definition["name"])
        "rustfs"

    """
    start = perf_counter()
    logger.info(
        "rustfs_service_definition_load_started",
        service_name=service_name,
        resource_name=resource_name,
    )
    service_path = resources.files("phlo_rustfs").joinpath(resource_name)
    try:
        data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
    except Exception:
        logger.error(
            "rustfs_service_definition_load_failed",
            service_name=service_name,
            resource_name=resource_name,
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
            exc_info=True,
        )
        raise

    service_count = len(data.get("services", {})) if isinstance(data, dict) else None
    logger.info(
        "rustfs_service_definition_load_completed",
        service_name=service_name,
        resource_name=resource_name,
        elapsed_ms=round((perf_counter() - start) * 1000, 2),
        service_count=service_count,
    )
    return data


class RustfsServicePlugin(ServicePlugin):
    """Service plugin for RustFS.

    Implements the ServicePlugin interface to provide Docker Compose service
    definitions for running RustFS S3-compatible object storage. This is the
    main service that runs the RustFS container.

    The service definition includes volume mounts, port mappings, and health
    checks for the RustFS S3 API and web console.
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the RustFS service plugin.

        Returns:
            PluginMetadata containing name, version, description, author,
            and tags for discovery and categorization.

        """
        return PluginMetadata(
            name="rustfs",
            version="0.1.0",
            description="S3-compatible object storage for data lake (RustFS)",
            author="Phlo Team",
            tags=["core", "storage", "s3"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the RustFS service definition.

        Returns the Docker Compose service definition for running the RustFS
        container, including API and console port mappings, volume mounts,
        and health check configuration.

        Returns:
            Dictionary containing the service definition parsed from
            the embedded service.yaml resource.

        """
        return _load_service_definition("service.yaml", "rustfs")


class RustfsSetupServicePlugin(ServicePlugin):
    """Service plugin for RustFS bucket initialization.

    Implements the ServicePlugin interface to provide a Docker Compose service
    definition for initializing RustFS buckets on startup. This service runs
    once after the main RustFS container is healthy to create the default
    buckets required by the data platform.

    Depends on the main rustfs service and uses the MinIO client to create
    buckets with appropriate access policies.
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the RustFS setup plugin.

        Returns:
            PluginMetadata containing name, version, description, author,
            and tags for discovery and categorization. Tagged with "bootstrap"
            to indicate this is a one-time initialization service.

        """
        return PluginMetadata(
            name="rustfs-setup",
            version="0.1.0",
            description="Initialize RustFS buckets for data lake",
            author="Phlo Team",
            tags=["core", "storage", "bootstrap"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the RustFS setup service definition.

        Returns the Docker Compose service definition for the bucket
        initialization container. This service depends on the main rustfs
        service being healthy and runs the MinIO client to create buckets.

        Returns:
            Dictionary containing the setup service definition parsed from
            the embedded rustfs-setup.yaml resource.

        """
        return _load_service_definition("rustfs-setup.yaml", "rustfs-setup")


class RustfsObjectStoreProvider:
    """Capability provider for RustFS-backed object storage.

    Provides S3-compatible connection details for RustFS storage. This class
    implements the object store capability interface, allowing other components
    to obtain S3 connection parameters for integrating with RustFS.

    The provider reads configuration from RustfsSettings and formats it
    into S3-compatible dictionaries suitable for Sling and other S3 clients.
    """

    def to_sling_connection(self) -> dict[str, Any]:
        """Return a Sling-compatible S3 connection definition.

        Constructs an S3 connection dictionary formatted for use with Sling.
        Includes endpoint URL, credentials, and region information read from
        the cached RustfsSettings.

        Returns:
            Dictionary with keys: type, endpoint, access_key_id,
            secret_access_key, and region.

        Example:
            >>> provider = RustfsObjectStoreProvider()
            >>> conn = provider.to_sling_connection()
            >>> print(conn["type"])
            "s3"

        """
        from phlo_rustfs.settings import get_settings

        settings = get_settings()
        return {
            "type": "s3",
            "endpoint": f"http://{settings.rustfs_endpoint()}",
            "access_key_id": settings.rustfs_access_key,
            "secret_access_key": settings.rustfs_secret_key,
            "region": settings.s3_region,
        }


class RustfsResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin for RustFS capabilities.

    Implements the ResourceProviderPlugin interface to expose RustFS object
    storage capabilities to the Phlo resource registry. This plugin allows
    other components to discover and connect to RustFS S3 storage.

    The provider exposes a single object store capability named "rustfs"
    that can be used for S3-compatible storage operations.
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the RustFS resource provider.

        Returns:
            PluginMetadata containing name, version, description, and tags.
            Tagged with "core", "storage", and "s3" for discovery.

        """
        return PluginMetadata(
            name="rustfs",
            version="0.1.0",
            description="RustFS object-store capability for Phlo",
            tags=["core", "storage", "s3"],
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Return resource specs exposed by this provider.

        Currently returns an empty list as RustFS does not expose any
        generic resources. Object store capabilities are exposed via
        get_object_stores instead.

        Returns:
            Empty list of ResourceSpec objects.

        """
        return []

    def get_object_stores(self) -> list[ObjectStoreSpec]:
        """Return object-store capability specs exposed by this provider.

        Returns a list containing a single ObjectStoreSpec for the RustFS
        S3-compatible storage. The spec includes metadata about the storage
        type and endpoint URL.

        Returns:
            List containing one ObjectStoreSpec for the "rustfs" object store.

        Example:
            >>> provider = RustfsResourceProvider()
            >>> stores = provider.get_object_stores()
            >>> len(stores)
            1
            >>> stores[0].name
            "rustfs"

        """
        provider = RustfsObjectStoreProvider()
        return [
            ObjectStoreSpec(
                name="rustfs",
                provider=provider,
                metadata={
                    "storage_system": "s3",
                    "type": "s3",
                    "endpoint": provider.to_sling_connection()["endpoint"],
                },
            )
        ]
