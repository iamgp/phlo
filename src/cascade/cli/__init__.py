"""
Cascade CLI

Command-line interface for Cascade workflows.

Available commands:
- cascade test        - Run tests with optional local mode
- cascade materialize - Materialize assets via Docker
- cascade create-workflow - Interactive workflow scaffolding

Usage:
    cascade [command] [options]

Examples:
    cascade test weather_observations --local
    cascade materialize weather_observations --partition 2024-01-15
    cascade create-workflow --type ingestion --domain weather
"""

__version__ = "1.0.0"
