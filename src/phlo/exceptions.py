"""
Phlo Exception Classes

Structured error classes with error codes, contextual messages, and suggestions.
"""

from enum import Enum
from typing import List, Optional


class PhloErrorCode(Enum):
    """Error codes for Phlo exceptions."""

    # Discovery and Configuration Errors (PHLO-001 to PHLO-099)
    ASSET_NOT_DISCOVERED = "PHLO-001"
    SCHEMA_MISMATCH = "PHLO-002"
    INVALID_CRON = "PHLO-003"
    VALIDATION_FAILED = "PHLO-004"
    MISSING_SCHEMA = "PHLO-005"

    # Runtime and Integration Errors (PHLO-100 to PHLO-199)
    INGESTION_FAILED = "PHLO-006"
    TABLE_NOT_FOUND = "PHLO-007"
    INFRASTRUCTURE_ERROR = "PHLO-008"

    # Schema and Type Errors (PHLO-200 to PHLO-299)
    SCHEMA_CONVERSION_ERROR = "PHLO-200"
    TYPE_CONVERSION_ERROR = "PHLO-201"

    # DLT Errors (PHLO-300 to PHLO-399)
    DLT_PIPELINE_FAILED = "PHLO-300"
    DLT_SOURCE_ERROR = "PHLO-301"

    # Iceberg Errors (PHLO-400 to PHLO-499)
    ICEBERG_CATALOG_ERROR = "PHLO-400"
    ICEBERG_TABLE_ERROR = "PHLO-401"
    ICEBERG_WRITE_ERROR = "PHLO-402"


class PhloError(Exception):
    """
    Base exception for Phlo framework errors.

    All Phlo exceptions include:
    - Error code for searchability
    - Contextual error message
    - Suggested actions to resolve
    - Link to documentation

    Example:
        raise PhloError(
            message="unique_key 'observation_id' not found in schema",
            code=PhloErrorCode.SCHEMA_MISMATCH,
            suggestions=[
                "Check that unique_key matches a field in validation_schema",
                "Available fields: id, city, temperature, timestamp",
            ]
        )
    """

    def __init__(
        self,
        message: str,
        code: PhloErrorCode,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize PhloError.

        Args:
            message: Clear description of what went wrong
            code: Error code from PhloErrorCode enum
            suggestions: List of suggested actions to resolve the error
            cause: Original exception that caused this error (if wrapping)
        """
        self.code = code
        self.suggestions = suggestions or []
        self.cause = cause
        self.doc_url = f"https://docs.phlo.dev/errors/{code.value}"

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


class PhloDiscoveryError(PhloError):
    """Raised when assets cannot be discovered by Dagster."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=PhloErrorCode.ASSET_NOT_DISCOVERED,
            suggestions=suggestions,
        )


class PhloSchemaError(PhloError):
    """Raised when schema configuration is invalid."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=PhloErrorCode.SCHEMA_MISMATCH,
            suggestions=suggestions,
        )


class PhloCronError(PhloError):
    """Raised when cron expression is invalid."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=PhloErrorCode.INVALID_CRON,
            suggestions=suggestions
            or [
                "Use standard cron format: [minute] [hour] [day_of_month] [month] [day_of_week]",
                'Examples: "0 */1 * * *" (hourly), "0 0 * * *" (daily)',
                "Test your cron at: https://crontab.guru",
            ],
        )


class PhloValidationError(PhloError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=PhloErrorCode.VALIDATION_FAILED,
            suggestions=suggestions,
            cause=cause,
        )


class PhloConfigError(PhloError):
    """Raised when decorator configuration is invalid."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=PhloErrorCode.MISSING_SCHEMA,
            suggestions=suggestions,
        )


class PhloIngestionError(PhloError):
    """Raised when data ingestion fails."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=PhloErrorCode.INGESTION_FAILED,
            suggestions=suggestions,
            cause=cause,
        )


class PhloTableError(PhloError):
    """Raised when Iceberg table operations fail."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=PhloErrorCode.TABLE_NOT_FOUND,
            suggestions=suggestions,
        )


class PhloInfrastructureError(PhloError):
    """Raised when infrastructure services are unavailable."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=PhloErrorCode.INFRASTRUCTURE_ERROR,
            suggestions=suggestions,
            cause=cause,
        )


class SchemaConversionError(PhloError):
    """Raised when Pandera schema cannot be converted to PyIceberg."""

    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code=PhloErrorCode.SCHEMA_CONVERSION_ERROR,
            suggestions=suggestions,
        )


class DLTPipelineError(PhloError):
    """Raised when DLT pipeline execution fails."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=PhloErrorCode.DLT_PIPELINE_FAILED,
            suggestions=suggestions,
            cause=cause,
        )


class IcebergCatalogError(PhloError):
    """Raised when Iceberg catalog operations fail."""

    def __init__(
        self,
        message: str,
        suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            code=PhloErrorCode.ICEBERG_CATALOG_ERROR,
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
