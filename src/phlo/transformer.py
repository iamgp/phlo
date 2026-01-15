"""Backward compatibility shim - import from phlo.operations.transformation instead."""

from phlo.operations.transformation import BaseTransformer, TransformationResult

__all__ = ["BaseTransformer", "TransformationResult"]
