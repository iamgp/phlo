"""
Cascade CLI

Command-line interface for Cascade workflows.

Available commands:
- phlo test        - Run tests with optional local mode
- phlo materialize - Materialize assets via Docker
- phlo create-workflow - Interactive workflow scaffolding

Usage:
    phlo [command] [options]

Examples:
    phlo test weather_observations --local
    phlo materialize weather_observations --partition 2024-01-15
    phlo create-workflow --type ingestion --domain weather
"""

__version__ = "1.0.0"
