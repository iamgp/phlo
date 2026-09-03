"""Phlo Polaris catalog package.

Provides the Apache Polaris Iceberg REST catalog service, snapshot-based WAP
promotion, Trino catalog properties, PyIceberg configuration, the bootstrap
hook, and the Nessie migration command.
"""

from phlo_polaris.plugin import PolarisServicePlugin

__all__ = ["PolarisServicePlugin"]
__version__ = "0.14.0"
