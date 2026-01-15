"""
Phlo Compose Plugin Module

Docker Compose generation and native process execution for service definitions.
"""

from phlo.plugins.compose.generator import ComposeGenerator
from phlo.plugins.compose.native import NativeProcess, NativeProcessManager

__all__ = [
    "ComposeGenerator",
    "NativeProcess",
    "NativeProcessManager",
]
