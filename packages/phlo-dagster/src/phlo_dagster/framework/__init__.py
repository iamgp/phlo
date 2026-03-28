"""Dagster framework helpers for Phlo projects.

This module provides the main entry point for Dagster-based Phlo projects.
It exports the core definitions building functionality that discovers and
loads user workflows from the configured workflows directory.

Exported Components:
    - build_definitions: Function to build merged Dagster definitions from
      user workflows and framework resources
    - defs: Global Definitions instance for Dagster to load

Architecture:
    The framework module serves as the bridge between Phlo's capability-based
    plugin system and Dagster's execution model. It handles:
    - Workflow discovery from user project directories
    - Resource injection and configuration
    - WAP (Write-Audit-Publish) sensor registration
    - Executor selection based on platform

Usage:
    In workspace.yaml::

        load_from:
          - python_module:
              module_name: phlo_dagster.framework.definitions

    Or programmatically::

        from phlo_dagster.framework import build_definitions

        defs = build_definitions(workflows_path="custom_workflows")
"""

from phlo_dagster.framework.definitions import build_definitions, defs

__all__ = ["build_definitions", "defs"]
