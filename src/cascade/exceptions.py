"""
Cascade Exception Classes

Structured error classes with error codes, contextual messages, and suggestions.
"""

from enum import Enum
from typing import List, Optional


class CascadeErrorCode(Enum):
    """Error codes for Cascade exceptions."""

    # Discovery and Configuration Errors (CASCADE-001 to CASCADE-099)
    ASSET_NOT_DISCOVERED = "CASCADE-001"
    SCHEMA_MISMATCH = "CASCADE-002"
    INVALID_CRON = "CASCADE-003"
    VALIDATION_FAILED = "CASCADE-004"
    MISSING_SCHEMA = "CASCADE-005"

    # Runtime and Integration Errors (CASCADE-100 to CASCADE-199)
    INGESTION_FAILED = "CASCADE-006"
    TABLE_NOT_FOUND = "CASCADE-007"
    INFRASTRUCTURE_ERROR = "CASCADE-008"

    # Schema and Type Errors (CASCADE-200 to CASCADE-299)
    SCHEMA_CONVERSION_ERROR = "CASCADE-200"
    TYPE_CONVERSION_ERROR = "CASCADE-201"

    # DLT Errors (CASCADE-300 to CASCADE-399)
    DLT_PIPELINE_FAILED = "CASCADE-300"
    DLT_SOURCE_ERROR = "CASCADE-301"

    # Iceberg Errors (CASCADE-400 to CASCADE-499)
    ICEBERG_CATALOG_ERROR = "CASCADE-400"
    ICEBERG_TABLE_ERROR = "CASCADE-401"
    ICEBERG_WRITE_ERROR = "CASCADE-402"


class CascadeError(Exception):
    """
    Base exception for Cascade framework errors.

    All Cascade exceptions include:
    - Error code for searchability
    - Contextual error message
    - Suggested actions to resolve
    - Link to documentation

    Example:
        raise CascadeError(
            message="unique_key 'observation_id' not found in schema",
            code=CascadeErrorCode.SCHEMA_MISMATCH,
            suggestions=[
                "Check that unique_key matches a field in validation_schema",
                "Available fields: id, city, temperature, timestamp",
            ]
        )
    """

    def __init__(
        self,
        message: str,
        code: CascadeErrorCode,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize CascadeError.

        Args:
            message: Clear description of what went wrong
            code: Error code from CascadeErrorCode enum
            suggestions: List of suggested actions to resolve the error
            cause: Original exception that caused this error (if wrapping)
        """
        self.code = code
        self.suggestions = suggestions or []
        self.cause = cause
        self.doc_url = f"https://docs.cascade.dev/errors/{code.value}"

        # Build formatted error message
        full_message = self._format_message(message)

        super().__init__(full_message)

    def _format_message(self, message: str) -> str:
        """Format error message with code, suggestions, and documentation link."""

        lines = [
            f"{self.__class__.__name__} ({self.code.value}): {message}",
        ]

        if self.suggestions:
            lines.append("")
            lines.append("Suggested actions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"  {i}. {suggestion}")

        if self.cause:
            lines.append("")
            lines.append(f"Caused by: {type(self.cause).__name__}: {str(self.cause)}")

        lines.append("")
        lines.append(f"Documentation: {self.doc_url}")

        return "\n".join(lines)


# Specific Error Classes


class CascadeDiscoveryError(CascadeError):
    """Raised when assets cannot be discovered by Dagster."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=CascadeErrorCode.ASSET_NOT_DISCOVERED,
            suggestions=suggestions,
        )


class CascadeSchemaError(CascadeError):
    """Raised when schema configuration is invalid."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=CascadeErrorCode.SCHEMA_MISMATCH,
            suggestions=suggestions,
        )


class CascadeCronError(CascadeError):
    """Raised when cron expression is invalid."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=CascadeErrorCode.INVALID_CRON,
            suggestions=suggestions or [
                "Use standard cron format: [minute] [hour] [day_of_month] [month] [day_of_week]",
                'Examples: "0 */1 * * *" (hourly), "0 0 * * *" (daily)',
                "Test your cron at: https://crontab.guru",
            ],
        )


class CascadeValidationError(CascadeError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=CascadeErrorCode.VALIDATION_FAILED,
            suggestions=suggestions,
            cause=cause,
        )


class CascadeConfigError(CascadeError):
    """Raised when decorator configuration is invalid."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=CascadeErrorCode.MISSING_SCHEMA,
            suggestions=suggestions,
        )


class CascadeIngestionError(CascadeError):
    """Raised when data ingestion fails."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=CascadeErrorCode.INGESTION_FAILED,
            suggestions=suggestions,
            cause=cause,
        )


class CascadeTableError(CascadeError):
    """Raised when Iceberg table operations fail."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=CascadeErrorCode.TABLE_NOT_FOUND,
            suggestions=suggestions,
        )


class CascadeInfrastructureError(CascadeError):
    """Raised when infrastructure services are unavailable."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=CascadeErrorCode.INFRASTRUCTURE_ERROR,
            suggestions=suggestions,
            cause=cause,
        )


class SchemaConversionError(CascadeError):
    """Raised when Pandera schema cannot be converted to PyIceberg."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=CascadeErrorCode.SCHEMA_CONVERSION_ERROR,
            suggestions=suggestions,
        )


class DLTPipelineError(CascadeError):
    """Raised when DLT pipeline execution fails."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=CascadeErrorCode.DLT_PIPELINE_FAILED,
            suggestions=suggestions,
            cause=cause,
        )


class IcebergCatalogError(CascadeError):
    """Raised when Iceberg catalog operations fail."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=CascadeErrorCode.ICEBERG_CATALOG_ERROR,
            suggestions=suggestions,
            cause=cause,
        )


# Utility Functions for Error Suggestions


def suggest_similar_field_names(
    invalid_field: str,
    valid_fields: List[str],
    max_suggestions: int = 3,
) -> List[str]:
    """
    Generate "Did you mean?" suggestions for field name typos.

    Uses fuzzy matching to suggest similar field names.

    Args:
        invalid_field: The invalid field name provided by user
        valid_fields: List of valid field names from schema
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of suggested field names
    """
    from difflib import get_close_matches

    similar = get_close_matches(
        invalid_field,
        valid_fields,
        n=max_suggestions,
        cutoff=0.6,  # Similarity threshold (0-1)
    )

    if similar:
        return [f"Did you mean '{field}'?" for field in similar]
    else:
        return [f"Available fields: {', '.join(valid_fields)}"]


def format_field_list(fields: List[str]) -> str:
    """Format a list of fields for error messages."""
    return ", ".join(f"'{field}'" for field in fields)
