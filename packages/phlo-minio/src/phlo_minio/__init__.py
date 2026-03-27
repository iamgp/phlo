"""MinIO service plugin package."""

from phlo_minio.plugin import MinioServicePlugin
from phlo_minio.settings import MinioSettings, get_settings

__all__ = ["MinioServicePlugin", "MinioSettings", "get_settings"]
__version__ = "0.2.1"
