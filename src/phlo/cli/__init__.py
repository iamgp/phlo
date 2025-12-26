"""
Phlo CLI

Command-line interface for Phlo workflows.

Available commands:
- phlo test            - Run tests with optional local mode
- phlo create-workflow - Interactive workflow scaffolding
- plus plugin commands from installed packages

Usage:
    phlo [command] [options]

Examples:
    phlo test weather_observations --local
    phlo create-workflow --type ingestion --domain weather
"""

__version__ = "1.0.0"
