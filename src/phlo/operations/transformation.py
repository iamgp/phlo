"""Transformation operation contracts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar


@dataclass
class TransformationResult:
    """Transformation execution summary."""

    status: str
    models_built: int
    models_failed: int
    tests_passed: int
    tests_failed: int
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Logger(Protocol):
    """Minimal logging protocol for transformation operations."""

    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log an informational transformation message."""

    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log a transformation warning message."""

    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log a transformation error message."""


ContextT = TypeVar("ContextT")


class BaseTransformer(Generic[ContextT], ABC):
    """Base contract for transformation engines."""

    def __init__(self, context: ContextT, logger: Logger):
        """Initialize a transformer.

        Args:
            context: Engine-specific execution context.
            logger: Logger used for execution output.
        """
        self.context = context
        self.logger = logger

    @abstractmethod
    def run_transform(
        self,
        partition_key: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> TransformationResult:
        """Run transformations for an optional partition.

        Args:
            partition_key: Partition key for partition-scoped runs.
            parameters: Backend-specific runtime parameters.

        Returns:
            Transformation execution result metadata.
        """
        ...
