from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class IngestionResult:
    status: str
    rows_inserted: int
    rows_deleted: int
    metadata: Dict[str, Any]


class BaseIngester(ABC):
    """
    Abstract base class for Phlo Ingestion Engines.

    This ensures that different ingestion backends (DLT, Airbyte, Custom)
    adhere to a common contract that Orchestrators (Dagster, Airflow) can consume.
    """

    def __init__(self, context: Any, logger: Any):
        self.context = context
        self.logger = logger

    @abstractmethod
    def run_ingestion(self, partition_key: str, parameters: Dict[str, Any]) -> IngestionResult:
        """
        Execute the ingestion logic for a specific partition.
        """
        pass
