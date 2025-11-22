"""
Cascade Framework Module

This module provides the core framework for discovering and loading user workflows
and integrating them with Dagster.

The framework supports:
- Workflow discovery from external directories
- Plugin integration
- Resource management
- Dagster Definitions building
"""

from cascade.framework.discovery import discover_user_workflows
from cascade.framework.definitions import build_definitions, defs

__all__ = [
    "discover_user_workflows",
    "build_definitions",
    "defs",
]
