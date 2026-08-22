"""Ingestion engine contract implemented by backends and consumed by orchestrators.

BaseIngester (sync) and AsyncIngester define the common run_ingestion()
contract so backends such as DLT stay interchangeable under orchestrators
such as Dagster. partition_key is None for unpartitioned runs; every
execution returns an IngestionResult with row counts and metadata.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class IngestionResult:
    """Outcome payload returned by ingestion executions."""

    status: str
    rows_inserted: int
    rows_deleted: int
    metadata: dict[str, Any]


class BaseIngester(ABC):
    """
    Abstract base class for Phlo Ingestion Engines.

    This ensures that different ingestion backends (DLT, Airbyte, Custom)
    adhere to a common contract that Orchestrators (Dagster, Airflow) can consume.
    """

    def __init__(self, context: Any, logger: Any):
        """Store runtime context and logger for ingestion implementations.

        Args:
            context: Orchestrator-provided execution context.
            logger: Logger used for ingestion diagnostics.
        """

        self.context = context
        self.logger = logger

    @abstractmethod
    def run_ingestion(
        self, partition_key: str | None, parameters: dict[str, Any]
    ) -> IngestionResult:
        """
        Execute the ingestion logic for a specific partition.

        partition_key may be None for unpartitioned runs.
        """


class AsyncIngester(ABC):
    """
    Async abstract base class for ingestion engines.

    Implementations can be adopted incrementally while existing sync
    ingestion engines continue using ``BaseIngester``.
    """

    def __init__(self, context: Any, logger: Any):
        """Store runtime context and logger for async ingestion implementations.

        Args:
            context: Orchestrator-provided execution context.
            logger: Logger used for ingestion diagnostics.
        """

        self.context = context
        self.logger = logger

    @abstractmethod
    async def run_ingestion(
        self, partition_key: str | None, parameters: dict[str, Any]
    ) -> IngestionResult:
        """
        Execute the ingestion logic for a specific partition.

        partition_key may be None for unpartitioned runs.
        """
