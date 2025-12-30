from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TransformationResult:
    status: str
    models_built: int
    models_failed: int
    tests_passed: int
    tests_failed: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseTransformer(ABC):
    """
    Abstract base class for Phlo Transformation Engines.

    This ensures that different transformation backends (dbt, SQLMesh, Spark)
    adhere to a common contract that Orchestrators (Dagster, Airflow) can consume.
    """

    def __init__(self, context: Any, logger: Any):
        self.context = context
        self.logger = logger

    @abstractmethod
    def run_transform(
        self, partition_key: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None
    ) -> TransformationResult:
        """
        Execute the transformation logic.
        """
        pass
