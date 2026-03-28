"""MinIO service and resource provider plugin for Phlo.

This module provides the complete MinIO integration for Phlo, including:
- Service plugin for MinIO server deployment
- Bucket initialization (setup) service
- Object storage capability provider
- Resource provider for S3-compatible storage

The module implements Phlo's plugin interfaces to provide S3-compatible
object storage capabilities for data lake operations.

Examples:
    Service plugin usage:
        >>> from phlo_minio.plugin import MinioServicePlugin
        >>> plugin = MinioServicePlugin()
        >>> defn = plugin.service_definition
        >>> print(defn['services'].keys())
        dict_keys(['minio'])

    Object store provider:
        >>> from phlo_minio.plugin import MinioObjectStoreProvider
        >>> provider = MinioObjectStoreProvider()
        >>> conn = provider.to_sling_connection()
        >>> print(conn['type'])
        's3'

    Resource provider integration:
        >>> from phlo_minio.plugin import MinioResourceProvider
        >>> rp = MinioResourceProvider()
        >>> stores = rp.get_object_stores()
        >>> print(stores[0].name)
        'minio'

See Also:
    phlo_minio.settings: Configuration management for MinIO connections.
    phlo.plugins: Phlo plugin framework interfaces.

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
    """Load and parse a YAML service definition file.

    Reads a YAML service definition from the package resources and
    returns the parsed configuration. Includes performance logging
    for monitoring load times.

    Args:
        resource_name: Name of the YAML file in the package (e.g., "service.yaml").
        service_name: Logical name of the service for logging purposes.

    Returns:
        dict[str, Any]: Parsed YAML service definition.

    Raises:
        Exception: If file reading or YAML parsing fails. Error is logged
            with timing information before re-raising.

    Examples:
        Load MinIO service definition:
            >>> defn = _load_service_definition("service.yaml", "minio")
            >>> print(defn['services']['minio']['image'])
            'minio/minio:latest'

        Load setup service:
            >>> defn = _load_service_definition("minio-setup.yaml", "minio-setup")
            >>> print(defn['services']['minio-setup']['command'])
            ['sh', '-c', '...']

    Logging:
        Emits structured logs:
            - minio_service_definition_load_started: When loading begins
            - minio_service_definition_load_completed: On success with timing
            - minio_service_definition_load_failed: On failure with timing

    Implementation:
        Uses importlib.resources for package-relative file access:
            service_path = resources.files("phlo_minio").joinpath(resource_name)

    """
    start = perf_counter()
    logger.info(
        "minio_service_definition_load_started",
        service_name=service_name,
        resource_name=resource_name,
    )
    service_path = resources.files("phlo_minio").joinpath(resource_name)
    try:
        data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
    except Exception:
        logger.error(
            "minio_service_definition_load_failed",
            service_name=service_name,
            resource_name=resource_name,
            elapsed_ms=round((perf_counter() - start) * 1000, 2),
            exc_info=True,
        )
        raise

    service_count = len(data.get("services", {})) if isinstance(data, dict) else None
    logger.info(
        "minio_service_definition_load_completed",
        service_name=service_name,
        resource_name=resource_name,
        elapsed_ms=round((perf_counter() - start) * 1000, 2),
        service_count=service_count,
    )
    return data


class MinioServicePlugin(ServicePlugin):
    """Service plugin for deploying MinIO S3-compatible object storage.

    This plugin provides the MinIO service definition for Docker Compose
    deployment. It implements the ServicePlugin interface to integrate
    MinIO into Phlo's service management system.

    The MinIO service runs on two ports:
    - API port (default 10001): S3-compatible API endpoint
    - Console port (default 10002): Web-based management UI

    Examples:
        Plugin instantiation:
            >>> plugin = MinioServicePlugin()
            >>> print(plugin.metadata.name)
            'minio'

        Access service definition:
            >>> plugin = MinioServicePlugin()
            >>> defn = plugin.service_definition
            >>> print(defn['services']['minio']['ports'])
            ['10001:9000', '10002:9001']

        Check metadata:
            >>> plugin = MinioServicePlugin()
            >>> plugin.metadata.tags
            ['core', 'storage', 's3']

    Attributes:
        metadata: PluginMetadata with name, version, and service info.

    Note:
        Service definition loaded from service.yaml in package resources.
        Default credentials: minio / minio123

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the MinIO service plugin.

        Returns:
            PluginMetadata: Plugin identity and display metadata.

        """
        return PluginMetadata(
            name="minio",
            version="0.1.0",
            description="S3-compatible object storage for data lake",
            author="Phlo Team",
            tags=["core", "storage", "s3"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the MinIO service definition from package resources.

        Returns:
            dict[str, Any]: Parsed Docker Compose service configuration
                from service.yaml. Contains services, volumes, and
                network definitions.

        Examples:
            Get service definition:
                >>> plugin = MinioServicePlugin()
                >>> defn = plugin.service_definition
                >>> services = defn.get('services', {})
                >>> print(list(services.keys()))
                ['minio']

            Inspect MinIO configuration:
                >>> plugin = MinioServicePlugin()
                >>> minio_svc = plugin.service_definition['services']['minio']
                >>> print(minio_svc['environment']['MINIO_ROOT_USER'])
                'minio'

        Structure:
            The returned dict typically contains:
                {
                    'services': {
                        'minio': {
                            'image': 'minio/minio:latest',
                            'ports': ['10001:9000', '10002:9001'],
                            'environment': {...},
                            'volumes': [...],
                            'command': [...]
                        }
                    },
                    'volumes': {...}
                }

        """
        return _load_service_definition("service.yaml", "minio")


class MinioSetupServicePlugin(ServicePlugin):
    """Service plugin for MinIO bucket initialization.

    This plugin provides a one-time setup service that creates default
    buckets in MinIO during the initial deployment. It runs as a
    separate container that executes bucket creation commands and exits.

    The setup service:
    - Creates default buckets (bronze, silver, gold for medallion architecture)
    - Sets bucket policies and lifecycle rules
    - Runs once during 'phlo services start' or on demand
    - Exits cleanly after completion

    Examples:
        Plugin usage:
            >>> plugin = MinioSetupServicePlugin()
            >>> print(plugin.metadata.name)
            'minio-setup'

        Service definition:
            >>> plugin = MinioSetupServicePlugin()
            >>> defn = plugin.service_definition
            >>> setup_svc = defn['services']['minio-setup']
            >>> print(setup_svc.get('restart'))
            'no'

    Attributes:
        metadata: PluginMetadata with setup service information.

    Note:
        The setup service has restart policy 'no' to ensure it only
        runs once per deployment.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return metadata describing the MinIO setup plugin.

        Returns:
            PluginMetadata: Plugin identity and display metadata.

        """
        return PluginMetadata(
            name="minio-setup",
            version="0.1.0",
            description="Initialize MinIO buckets for data lake",
            author="Phlo Team",
            tags=["core", "storage", "bootstrap"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the MinIO setup service definition from package resources.

        Returns:
            dict[str, Any]: Parsed Docker Compose service configuration
                from minio-setup.yaml. Contains the setup service definition
                for bucket initialization.

        Examples:
            Get setup definition:
                >>> plugin = MinioSetupServicePlugin()
                >>> defn = plugin.service_definition
                >>> setup_svc = defn['services']['minio-setup']
                >>> print(setup_svc['depends_on'])
                ['minio']

        Structure:
            The setup service typically:
            - Depends on minio service being healthy
            - Uses mc (MinIO Client) to create buckets
            - Has restart policy set to 'no'
            - Exits after creating configured buckets

        """
        return _load_service_definition("minio-setup.yaml", "minio-setup")


class MinioObjectStoreProvider:
    """Capability provider for MinIO-backed S3-compatible object storage.

    This class provides object storage capabilities compatible with
    S3 SDKs and tools. It handles configuration translation between
    Phlo settings and various S3 client formats.

    The provider supports:
    - S3 API operations (boto3, aws-sdk, etc.)
    - Sling replication tool integration
    - Standard S3 endpoint configuration

    Examples:
        Basic provider usage:
            >>> provider = MinioObjectStoreProvider()
            >>> conn = provider.to_sling_connection()
            >>> print(conn['endpoint'])
            'http://minio:10001'

        Integration with boto3:
            >>> import boto3
            >>> provider = MinioObjectStoreProvider()
            >>> conn = provider.to_sling_connection()
            >>> s3 = boto3.client(
            ...     's3',
            ...     endpoint_url=conn['endpoint'],
            ...     aws_access_key_id=conn['access_key_id'],
            ...     aws_secret_access_key=conn['secret_access_key'],
            ...     region_name=conn['region']
            ... )
            >>> # Now use s3.list_buckets(), s3.put_object(), etc.

        List buckets:
            >>> import boto3
            >>> provider = MinioObjectStoreProvider()
            >>> conn = provider.to_sling_connection()
            >>> s3 = boto3.client('s3', **conn)
            >>> response = s3.list_buckets()
            >>> print([b['Name'] for b in response['Buckets']])
            ['bronze', 'silver', 'gold']

    Note:
        Uses phlo_minio.settings.get_settings() for configuration.
        Settings are cached for performance.

    """

    def to_sling_connection(self) -> dict[str, Any]:
        """Return a Sling-compatible S3 connection definition.

        Generates a connection dictionary compatible with the Sling
        data replication tool and similar S3-based systems.

        Returns:
            dict[str, Any]: Connection configuration with:
                - type: Always "s3"
                - endpoint: Full HTTP endpoint URL
                - access_key_id: MinIO root user
                - secret_access_key: MinIO root password
                - region: S3 region identifier

        Examples:
            Sling connection:
                >>> provider = MinioObjectStoreProvider()
                >>> conn = provider.to_sling_connection()
                >>> print(conn)
                {
                    'type': 's3',
                    'endpoint': 'http://minio:10001',
                    'access_key_id': 'minio',
                    'secret_access_key': 'minio123',
                    'region': 'us-east-1'
                }

            Sling replication config:
                >>> provider = MinioObjectStoreProvider()
                >>> conn = provider.to_sling_connection()
                >>> sling_config = {
                ...     'source': conn,
                ...     'target': {'type': 'postgres', ...},
                ...     'streams': {'s3://bucket/key': {'mode': 'full_refresh'}}
                ... }

            Direct S3 operations:
                >>> import boto3
                >>> provider = MinioObjectStoreProvider()
                >>> conn = provider.to_sling_connection()
                >>> s3 = boto3.client(
                ...     's3',
                ...     endpoint_url=conn['endpoint'],
                ...     aws_access_key_id=conn['access_key_id'],
                ...     aws_secret_access_key=conn['secret_access_key'],
                ...     region_name=conn['region']
                ... )
                >>> # Upload a file
                >>> s3.upload_file('data.csv', 'my-bucket', 'data.csv')
                >>> # Download a file
                >>> s3.download_file('my-bucket', 'data.csv', 'downloaded.csv')
                >>> # List objects
                >>> response = s3.list_objects_v2(Bucket='my-bucket', Prefix='data/')
                >>> print([obj['Key'] for obj in response.get('Contents', [])])

        Implementation:
            Loads settings via get_settings() and constructs endpoint:
                endpoint = f"http://{settings.minio_endpoint()}"

        """
        from phlo_minio.settings import get_settings

        settings = get_settings()
        return {
            "type": "s3",
            "endpoint": f"http://{settings.minio_endpoint()}",
            "access_key_id": settings.minio_root_user,
            "secret_access_key": settings.minio_root_password,
            "region": settings.s3_region,
        }


class MinioResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin exposing MinIO object storage capabilities.

    This plugin implements the ResourceProviderPlugin interface to
    expose MinIO as an object storage capability within Phlo's
    capability framework. It enables other Phlo components to
    discover and use MinIO for S3-compatible storage operations.

    The provider exposes:
    - ObjectStoreSpec for S3 operations
    - Metadata for capability discovery
    - Connection parameters for client configuration

    Examples:
        Plugin metadata:
            >>> provider = MinioResourceProvider()
            >>> print(provider.metadata.name)
            'minio'
            >>> print(provider.metadata.tags)
            ['core', 'storage', 's3']

        Get object stores:
            >>> provider = MinioResourceProvider()
            >>> stores = provider.get_object_stores()
            >>> store = stores[0]
            >>> print(store.name)
            'minio'
            >>> print(store.metadata['storage_system'])
            's3'

        Access store provider:
            >>> provider = MinioResourceProvider()
            >>> store = provider.get_object_stores()[0]
            >>> conn = store.provider.to_sling_connection()
            >>> print(conn['endpoint'])
            'http://minio:10001'

    Attributes:
        metadata: PluginMetadata with provider identification and tags.

    See Also:
        phlo.capabilities.ObjectStoreSpec: Object storage capability spec.
        MinioObjectStoreProvider: The underlying capability implementation.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the MinIO resource provider."""
        return PluginMetadata(
            name="minio",
            version="0.1.0",
            description="MinIO object-store capability for Phlo",
            tags=["core", "storage", "s3"],
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Return resource specifications exposed by this provider.

        Currently returns an empty list as MinIO does not expose
        traditional resources through this provider. Object storage
        is provided via get_object_stores().

        Returns:
            list[ResourceSpec]: Empty list (no resources exposed).

        Examples:
            Check resources:
                >>> provider = MinioResourceProvider()
                >>> resources = provider.get_resources()
                >>> len(resources)
                0

        Note:
            This method is required by the ResourceProviderPlugin interface.
            Use get_object_stores() for MinIO storage capabilities.

        """
        return []

    def get_object_stores(self) -> list[ObjectStoreSpec]:
        """Return object storage capability specifications.

        Returns a list of ObjectStoreSpec instances representing the
        MinIO object storage capability. Each spec includes the provider
        instance and metadata for capability discovery.

        Returns:
            list[ObjectStoreSpec]: List containing one ObjectStoreSpec
                for the MinIO instance with:
                - name: "minio"
                - provider: MinioObjectStoreProvider instance
                - metadata: Storage type, endpoint, and S3 configuration

        Examples:
            Get object stores:
                >>> provider = MinioResourceProvider()
                >>> stores = provider.get_object_stores()
                >>> len(stores)
                1
                >>> store = stores[0]
                >>> store.name
                'minio'

            Access store metadata:
                >>> provider = MinioResourceProvider()
                >>> store = provider.get_object_stores()[0]
                >>> print(store.metadata['type'])
                's3'
                >>> print(store.metadata['storage_system'])
                's3'
                >>> print(store.metadata['endpoint'])
                'http://minio:10001'

            Use with S3 client:
                >>> provider = MinioResourceProvider()
                >>> store = provider.get_object_stores()[0]
                >>> conn = store.provider.to_sling_connection()
                >>>
                >>> # Use with boto3
                >>> import boto3
                >>> s3 = boto3.client('s3', **conn)
                >>> buckets = s3.list_buckets()
                >>> print([b['Name'] for b in buckets['Buckets']])
                ['bronze', 'silver', 'gold']

            Use with Sling:
                >>> provider = MinioResourceProvider()
                >>> store = provider.get_object_stores()[0]
                >>> conn = store.provider.to_sling_connection()
                >>>
                >>> # Configure Sling replication
                >>> sling_replication = {
                ...     'source': conn,
                ...     'target': {'type': 'postgres', 'url': '...'},
                ...     'streams': {
                ...         's3://bronze/raw-data/*.csv': {
                ...             'mode': 'incremental',
                ...             'primary_key': ['id']
                ...         }
                ...     }
                ... }

        Implementation:
            Creates ObjectStoreSpec with MinioObjectStoreProvider:
                provider = MinioObjectStoreProvider()
                return [ObjectStoreSpec(
                    name="minio",
                    provider=provider,
                    metadata={...}
                )]

        """
        provider = MinioObjectStoreProvider()
        return [
            ObjectStoreSpec(
                name="minio",
                provider=provider,
                metadata={
                    "storage_system": "s3",
                    "type": "s3",
                    "endpoint": provider.to_sling_connection()["endpoint"],
                },
            )
        ]
