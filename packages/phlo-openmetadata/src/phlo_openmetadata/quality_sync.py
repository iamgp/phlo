"""
Quality check synchronization to OpenMetadata.

Maps quality checks from @phlo_quality decorator and dbt tests
to OpenMetadata test definitions and publishes results.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from phlo_openmetadata.openmetadata import OpenMetadataClient

from phlo_quality.checks import (
    CountCheck,
    CustomSQLCheck,
    FreshnessCheck,
    NullCheck,
    QualityCheckResult,
    RangeCheck,
    UniqueCheck,
)

logger = logging.getLogger(__name__)


class QualityCheckMapper:
    """
    Maps quality checks to OpenMetadata test definitions.

    Converts @phlo_quality checks to OpenMetadata TestDefinition objects
    and handles parameter mapping.
    """

    # Mapping of quality check types to OpenMetadata test types
    CHECK_TYPE_MAP = {
        "NullCheck": "nullCheck",
        "RangeCheck": "rangeCheck",
        "UniqueCheck": "uniqueCheck",
        "CountCheck": "countCheck",
        "FreshnessCheck": "freshnessCheck",
        "SchemaCheck": "schemaCheck",
        "CustomSQLCheck": "customSQLCheck",
    }

    @classmethod
    def map_check_to_openmetadata_test_definition(
        cls,
        check: Any,  # Union of quality check classes
        table_fqn: str,
    ) -> dict[str, Any]:
        """
        Convert quality check to OpenMetadata test definition format.

        Args:
            check: Quality check instance
            table_fqn: Fully qualified name of table being tested

        Returns:
            Dictionary with test definition format
        """
        check_type = type(check).__name__
        om_test_type = cls.CHECK_TYPE_MAP.get(check_type, "customCheck")

        # Get human-readable test name
        test_name = cls._get_test_name(check)

        return {
            "name": test_name,
            "displayName": test_name,
            "description": cls._get_test_description(check),
            "entityType": cls._get_entity_type(check),
            "parameterDefinition": cls._get_parameter_definition(check),
            "testPlatforms": ["OpenMetadata"],
            "testType": om_test_type,
        }

    @classmethod
    def map_check_to_test_case(
        cls,
        check: Any,
        table_fqn: str,
        test_suite_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Convert quality check to OpenMetadata test case format.

        Args:
            check: Quality check instance
            table_fqn: Fully qualified name of table being tested
            test_suite_name: Optional name for test suite

        Returns:
            Dictionary with test case format
        """
        test_name = cls._get_test_name(check)

        if not test_suite_name:
            # Create suite name from table name
            table_name = table_fqn.split(".")[-1]
            test_suite_name = f"{table_name}_quality_suite"

        test_suite_name = cls._sanitize_name(test_suite_name)
        test_case_name = f"{cls._sanitize_name(table_fqn)}_{cls._sanitize_name(test_name)}"

        return {
            "name": test_case_name,
            "entityLink": cls._get_entity_link(check, table_fqn),
            "testDefinition": {
                "name": cls._sanitize_name(test_name),
                "type": "testDefinition",
            },
            "testSuite": {
                "name": test_suite_name,
                "type": "testSuite",
            },
            "parameterValues": cls._get_parameter_values(check),
            "description": cls._get_test_description(check),
        }

    @classmethod
    def map_check_result_to_test_result(
        cls,
        check_result: QualityCheckResult,
        test_case_fqn: str,
        execution_timestamp: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Convert quality check result to OpenMetadata test result format.

        Args:
            check_result: QualityCheckResult from executing a check
            test_case_fqn: Fully qualified name of test case
            execution_timestamp: When the test executed

        Returns:
            Dictionary with test result format
        """
        if execution_timestamp is None:
            execution_timestamp = datetime.utcnow()

        return {
            "result": "Success" if check_result.passed else "Failed",
            "testCaseStatus": "Success" if check_result.passed else "Failed",
            "timestamp": int(execution_timestamp.timestamp() * 1000),
            "result_value": str(check_result.metric_value),
            "failureDetails": {
                "testFailureMessage": check_result.failure_message,
                "testFailureMetadata": json.dumps(check_result.metadata),
            }
            if not check_result.passed
            else None,
        }

    @classmethod
    def map_dbt_test_to_openmetadata(
        cls,
        dbt_test: dict[str, Any],
        table_fqn: str,
    ) -> dict[str, Any]:
        """
        Convert dbt test to OpenMetadata test case format.

        Args:
            dbt_test: dbt test metadata from manifest
            table_fqn: Fully qualified name of table being tested

        Returns:
            Dictionary with test case format
        """
        test_name = dbt_test.get("name", "unknown_test")
        test_type = (
            dbt_test.get("type") or dbt_test.get("test_metadata", {}).get("name") or "unknown"
        )

        test_def_name = cls._sanitize_name(f"dbt_{test_type}")

        return {
            "name": f"{cls._sanitize_name(table_fqn)}_dbt_{cls._sanitize_name(test_name)}",
            "entityLink": cls._build_entity_link(table_fqn, None),
            "testDefinition": {
                "name": test_def_name,
                "type": "testDefinition",
            },
            "testSuite": {
                "name": cls._sanitize_name(f"{table_fqn.split('.')[-1]}_dbt_suite"),
                "type": "testSuite",
            },
            "parameterValues": cls._get_dbt_test_parameters(dbt_test),
            "description": dbt_test.get("description"),
        }

    @staticmethod
    def _get_test_name(check: Any) -> str:
        """Generate OpenMetadata-friendly test name from check."""
        if isinstance(check, NullCheck):
            cols = "_".join(check.columns)
            return QualityCheckMapper._sanitize_name(f"null_check_{cols}")
        if isinstance(check, RangeCheck):
            return QualityCheckMapper._sanitize_name(f"range_check_{check.column}")
        if isinstance(check, UniqueCheck):
            cols = "_".join(check.columns)
            return QualityCheckMapper._sanitize_name(f"unique_check_{cols}")
        if isinstance(check, CountCheck):
            return "count_check"
        if isinstance(check, FreshnessCheck):
            return QualityCheckMapper._sanitize_name(
                f"freshness_check_{check.timestamp_column}"
            )
        if isinstance(check, CustomSQLCheck):
            return QualityCheckMapper._sanitize_name(check.name_)
        return QualityCheckMapper._sanitize_name(type(check).__name__.lower())

    @staticmethod
    def _sanitize_name(value: str) -> str:
        """Sanitize entity names for OpenMetadata compatibility."""
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value).strip("_")
        return cleaned or "phlo"

    @staticmethod
    def _build_entity_link(table_fqn: str, column: str | None) -> str:
        if column:
            return f"<#E::table::{table_fqn}::columns::{column}>"
        return f"<#E::table::{table_fqn}>"

    @classmethod
    def _get_entity_link(cls, check: Any, table_fqn: str) -> str:
        column: str | None = None
        if isinstance(check, NullCheck) and len(check.columns) == 1:
            column = check.columns[0]
        elif isinstance(check, RangeCheck):
            column = check.column
        elif isinstance(check, FreshnessCheck):
            column = check.timestamp_column
        elif isinstance(check, UniqueCheck) and len(check.columns) == 1:
            column = check.columns[0]
        return cls._build_entity_link(table_fqn, column)

    @staticmethod
    def _get_entity_type(check: Any) -> str:
        if isinstance(check, (NullCheck, RangeCheck, FreshnessCheck)):
            return "COLUMN"
        if isinstance(check, UniqueCheck) and len(check.columns) == 1:
            return "COLUMN"
        return "TABLE"

    @staticmethod
    def _get_test_description(check: Any) -> str:
        """Generate human-readable description for a quality check."""
        if isinstance(check, NullCheck):
            return f"Check that columns {', '.join(check.columns)} have no null values"
        if isinstance(check, RangeCheck):
            return (
                f"Check that column {check.column} values are between "
                f"{check.min_value} and {check.max_value}"
            )
        if isinstance(check, UniqueCheck):
            return f"Check that columns {', '.join(check.columns)} values are unique"
        if isinstance(check, CountCheck):
            return f"Check that row count is between {check.min_rows} and {check.max_rows}"
        if isinstance(check, FreshnessCheck):
            return (
                f"Check that data is not older than {check.max_age_hours} hours based on "
                f"{check.timestamp_column}"
            )
        if isinstance(check, CustomSQLCheck):
            return f"Custom SQL quality check: {check.name_}"
        return "Quality check"

    @staticmethod
    def _get_parameter_definition(check: Any) -> list[dict[str, Any]]:
        """Extract parameter definitions for check type."""
        if isinstance(check, NullCheck):
            return [
                {"name": "columns", "dataType": "STRING", "required": True},
                {"name": "allow_threshold", "dataType": "NUMBER", "required": False},
            ]
        if isinstance(check, RangeCheck):
            return [
                {"name": "column", "dataType": "STRING", "required": True},
                {"name": "min_value", "dataType": "NUMBER", "required": False},
                {"name": "max_value", "dataType": "NUMBER", "required": False},
            ]
        if isinstance(check, UniqueCheck):
            return [
                {"name": "columns", "dataType": "STRING", "required": True},
            ]
        if isinstance(check, CountCheck):
            return [
                {"name": "min_rows", "dataType": "NUMBER", "required": False},
                {"name": "max_rows", "dataType": "NUMBER", "required": False},
            ]
        if isinstance(check, FreshnessCheck):
            return [
                {"name": "timestamp_column", "dataType": "STRING", "required": True},
                {"name": "max_age_hours", "dataType": "NUMBER", "required": True},
            ]
        if isinstance(check, CustomSQLCheck):
            return [
                {"name": "sql", "dataType": "STRING", "required": True},
            ]
        return []

    @staticmethod
    def _get_parameter_values(check: Any) -> list[dict[str, str]]:
        """Extract parameter values from a check instance."""
        params: list[dict[str, str]] = []

        if isinstance(check, NullCheck):
            params.append({"name": "columns", "value": ",".join(check.columns)})
            params.append({"name": "allow_threshold", "value": str(check.allow_threshold)})
        elif isinstance(check, RangeCheck):
            params.append({"name": "column", "value": check.column})
            params.append({"name": "min_value", "value": str(check.min_value)})
            params.append({"name": "max_value", "value": str(check.max_value)})
        elif isinstance(check, UniqueCheck):
            params.append({"name": "columns", "value": ",".join(check.columns)})
        elif isinstance(check, CountCheck):
            if check.min_rows is not None:
                params.append({"name": "min_rows", "value": str(check.min_rows)})
            if check.max_rows is not None:
                params.append({"name": "max_rows", "value": str(check.max_rows)})
        elif isinstance(check, FreshnessCheck):
            params.append({"name": "timestamp_column", "value": check.timestamp_column})
            params.append({"name": "max_age_hours", "value": str(check.max_age_hours)})
        elif isinstance(check, CustomSQLCheck):
            params.append({"name": "sql", "value": check.sql})

        return params

    @staticmethod
    def _get_dbt_test_parameters(dbt_test: dict[str, Any]) -> list[dict[str, str]]:
        """Extract parameter values from dbt test metadata."""
        params: list[dict[str, str]] = []
        kwargs = dbt_test.get("kwargs") or dbt_test.get("test_metadata", {}).get("kwargs", {})

        for key, value in kwargs.items():
            params.append({"name": key, "value": str(value)})

        return params


class QualityCheckPublisher:
    """
    Publishes quality check results to OpenMetadata.

    Handles creating test definitions, cases, and publishing results.
    """

    def __init__(self, om_client: OpenMetadataClient):
        self.om_client = om_client

    def publish_test_definitions(
        self,
        checks: list[Any],
        table_fqn: str,
    ) -> dict[str, int]:
        """
        Publish quality check definitions to OpenMetadata.

        Args:
            checks: List of quality checks
            table_fqn: Fully qualified table name

        Returns:
            Dictionary with publication statistics
        """
        stats = {"created": 0, "failed": 0}

        for check in checks:
            try:
                test_def = QualityCheckMapper.map_check_to_openmetadata_test_definition(
                    check, table_fqn
                )

                # Create test definition (idempotent)
                self.om_client.create_test_definition(
                    test_name=test_def["name"],
                    test_type=test_def.get("testType"),
                    description=test_def.get("description"),
                    entity_type=test_def.get("entityType"),
                    parameter_definition=test_def.get("parameterDefinition"),
                    test_platforms=test_def.get("testPlatforms"),
                )

                logger.info(f"Published test definition: {test_def['name']}")
                stats["created"] += 1

            except Exception as e:
                logger.error(f"Failed to publish test definition for {table_fqn}: {e}")
                stats["failed"] += 1

        return stats

    def publish_test_cases(
        self,
        checks: list[Any],
        table_fqn: str,
        test_suite_name: Optional[str] = None,
    ) -> dict[str, int]:
        """
        Publish quality check cases to OpenMetadata.

        Args:
            checks: List of quality checks
            table_fqn: Fully qualified table name
            test_suite_name: Optional test suite name

        Returns:
            Dictionary with publication statistics
        """
        stats = {"created": 0, "failed": 0}

        for check in checks:
            try:
                test_case = QualityCheckMapper.map_check_to_test_case(
                    check, table_fqn, test_suite_name
                )

                self.om_client.create_test_case(
                    test_case_name=test_case["name"],
                    table_fqn=table_fqn,
                    test_definition_name=test_case["testDefinition"]["name"],
                    parameters={
                        p["name"]: p["value"] for p in test_case.get("parameterValues", [])
                    },
                    description=test_case.get("description"),
                    entity_link=test_case.get("entityLink"),
                    test_suite_name=test_case.get("testSuite", {}).get("name"),
                )

                logger.info(f"Published test case: {test_case['name']}")
                stats["created"] += 1

            except Exception as e:
                logger.error(f"Failed to publish test case for {table_fqn}: {e}")
                stats["failed"] += 1

        return stats

    def publish_test_results(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, int]:
        """
        Publish quality check results to OpenMetadata.

        Args:
            results: List of test result dictionaries with
                     'test_case_fqn', 'check_result', and 'timestamp' keys

        Returns:
            Dictionary with publication statistics
        """
        stats = {"published": 0, "failed": 0}

        for result in results:
            try:
                test_case_fqn = result.get("test_case_fqn")
                check_result = result.get("check_result")
                timestamp = result.get("timestamp")

                if not test_case_fqn or not check_result:
                    logger.warning(f"Skipping invalid test result: {result}")
                    continue

                om_result = QualityCheckMapper.map_check_result_to_test_result(
                    check_result, test_case_fqn, timestamp
                )

                self.om_client.publish_test_result(
                    test_case_fqn=test_case_fqn,
                    result=om_result["result"],
                    test_execution_date=datetime.fromtimestamp(om_result["timestamp"] / 1000),
                    result_value=om_result.get("result_value"),
                )

                logger.info(f"Published test result: {test_case_fqn}")
                stats["published"] += 1

            except Exception as e:
                logger.error(f"Failed to publish test result: {e}")
                stats["failed"] += 1

        return stats

    def publish_dbt_tests(
        self,
        dbt_tests: list[dict[str, Any]],
        table_fqn: str,
    ) -> dict[str, int]:
        """
        Publish dbt test definitions to OpenMetadata.

        Args:
            dbt_tests: List of dbt tests from manifest
            table_fqn: Fully qualified table name

        Returns:
            Dictionary with publication statistics
        """
        stats = {"created": 0, "failed": 0}

        for dbt_test in dbt_tests:
            try:
                test_case = QualityCheckMapper.map_dbt_test_to_openmetadata(dbt_test, table_fqn)

                self.om_client.create_test_case(
                    test_case_name=test_case["name"],
                    table_fqn=table_fqn,
                    test_definition_name=test_case["testDefinition"]["name"],
                    parameters={
                        p["name"]: p["value"] for p in test_case.get("parameterValues", [])
                    },
                    description=test_case.get("description"),
                    entity_link=test_case.get("entityLink"),
                    test_suite_name=test_case.get("testSuite", {}).get("name"),
                )

                logger.info(f"Published dbt test case: {test_case['name']}")
                stats["created"] += 1

            except Exception as e:
                logger.error(f"Failed to publish dbt test for {table_fqn}: {e}")
                stats["failed"] += 1

        return stats
