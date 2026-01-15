from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar


@dataclass
class TransformationResult:
    status: str
    models_built: int
    models_failed: int
    tests_passed: int
    tests_failed: int
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Logger(Protocol):
    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        ...

    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        ...

    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        ...


ContextT = TypeVar("ContextT")


class BaseTransformer(Generic[ContextT], ABC):
    """
    Abstract base class for Phlo Transformation Engines.

    This ensures that different transformation backends (dbt, SQLMesh, Spark)
    adhere to a common contract that Orchestrators (Dagster, Airflow) can consume.
    """

    def __init__(self, context: ContextT, logger: Logger):
        self.context = context
        self.logger = logger

    @abstractmethod
    def run_transform(
        self,
        partition_key: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> TransformationResult:
        """
        Execute the transformation logic.
        """
        ...
