"""Apache Superset integration for Phlo.

This package provides integration with Apache Superset for business intelligence
and data visualization within the Phlo data platform.

Example:
    >>> from phlo_superset import SupersetSettings, get_settings
    >>> settings = get_settings()
    >>> print(settings.superset_port)
    10007

"""

from phlo_superset.settings import SupersetSettings, get_settings

__all__ = [
    "SupersetSettings",
    "get_settings",
]
