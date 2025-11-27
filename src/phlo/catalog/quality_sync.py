"""
Quality check synchronization to OpenMetadata.

Maps quality checks from @phlo_quality decorator and dbt tests
to OpenMetadata test definitions and publishes results.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

from phlo.quality.checks import (
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
            "testType": om_test_type,
            "description": cls._get_test_description(check),
            "parameterDefinition": cls._get_parameter_definition(check),
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

        return {
            "name": f"{table_fqn}_{test_name}",
            "entityLink": f"<#{table_fqn}>",
            "testDefinition": {
                "name": test_name,
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
        test_type = dbt_test.get("type", "generic")

        return {
            "name": f"{table_fqn}_dbt_{test_name}",
            "entityLink": f"<#{table_fqn}>",
            "testDefinition": {
                "name": f"dbt_{test_type}",
                "type": "testDefinition",
            },
            "testSuite": {
                "name": f"{table_fqn.split('.')[-1]}_dbt_suite",
                "type": "testSuite",
            },
            "parameterValues": [
                {"name": k, "value": str(v)}
                for k, v in dbt_test.get("kwargs", {}).items()
            ],
            "description": dbt_test.get("description"),
        }

    @staticmethod
    def _get_test_name(check: Any) -> str:
        """Generate OpenMetadata-friendly test name from check."""
        if hasattr(check, "name"):
            return check.name
        return type(check).__name__

    @staticmethod
    def _get_test_description(check: Any) -> str:
        """Generate description for quality check."""
        check_type = type(check).__name__

        descriptions = {
            "NullCheck": "Validates that columns do not contain null values",
            "RangeCheck": "Validates that numeric values fall within expected range",
            "UniqueCheck": "Validates that values are unique (no duplicates)",
            "CountCheck": "Validates row count meets expectations",
            "FreshnessCheck": "Validates data freshness based on timestamp",
            "SchemaCheck": "Validates data against Pandera schema definition",
            "CustomSQLCheck": "Validates data using custom SQL query",
        }

        if isinstance(check, NullCheck):
            return f"Check that columns {check.columns} have no null values"
        elif isinstance(check, RangeCheck):
            return (
                f"Check that {check.column} values are between "
                f"{check.min_value} and {check.max_value}"
            )
        elif isinstance(check, FreshnessCheck):
            return (
                f"Check that data in {check.timestamp_column} "
                f"is less than {check.max_age_hours} hours old"
            )
        elif isinstance(check, UniqueCheck):
            return f"Check that columns {check.columns} have unique values"
        elif isinstance(check, CountCheck):
            return f"Check row count is between {check.min_rows} and {check.max_rows}"
        elif isinstance(check, CustomSQLCheck):
            return f"Custom SQL check: {check.name_}"

        return descriptions.get(check_type, f"Quality check: {check_type}")

    @staticmethod
    def _get_parameter_definition(check: Any) -> list[dict[str, Any]]:
        """Extract parameter definitions from quality check."""
        params = []

        if isinstance(check, NullCheck):
            params = [
                {
                    "name": "columns",
                    "description": "Columns to check for null values",
                    "dataType": "ARRAY",
                    "required": True,
                },
                {
                    "name": "allow_threshold",
                    "description": "Maximum fraction of nulls allowed",
                    "dataType": "DECIMAL",
                    "required": False,
                },
            ]
        elif isinstance(check, RangeCheck):
            params = [
                {
                    "name": "column",
                    "description": "Column to check",
                    "dataType": "STRING",
                    "required": True,
                },
                {
                    "name": "min_value",
                    "description": "Minimum allowed value",
                    "dataType": "DECIMAL",
                    "required": False,
                },
                {
                    "name": "max_value",
                    "description": "Maximum allowed value",
                    "dataType": "DECIMAL",
                    "required": False,
                },
            ]
        elif isinstance(check, FreshnessCheck):
            params = [
                {
                    "name": "timestamp_column",
                    "description": "Timestamp column to check",
                    "dataType": "STRING",
                    "required": True,
                },
                {
                    "name": "max_age_hours",
                    "description": "Maximum age in hours",
                    "dataType": "DECIMAL",
                    "required": True,
                },
            ]
        elif isinstance(check, UniqueCheck):
            params = [
                {
                    "name": "columns",
                    "description": "Columns to check for uniqueness",
                    "dataType": "ARRAY",
                    "required": True,
                }
            ]

        return params

    @staticmethod
    def _get_parameter_values(check: Any) -> list[dict[str, str]]:
        """Extract parameter values from quality check instance."""
        params = []

        if isinstance(check, NullCheck):
            params = [
                {"name": "columns", "value": ",".join(check.columns)},
                {"name": "allow_threshold", "value": str(check.allow_threshold)},
            ]
        elif isinstance(check, RangeCheck):
            params = [
                {"name": "column", "value": check.column},
            ]
            if check.min_value is not None:
                params.append({"name": "min_value", "value": str(check.min_value)})
            if check.max_value is not None:
                params.append({"name": "max_value", "value": str(check.max_value)})
        elif isinstance(check, FreshnessCheck):
            params = [
                {"name": "timestamp_column", "value": check.timestamp_column},
                {"name": "max_age_hours", "value": str(check.max_age_hours)},
            ]
        elif isinstance(check, UniqueCheck):
            params = [
                {"name": "columns", "value": ",".join(check.columns)},
            ]
        elif isinstance(check, CountCheck):
            if check.min_rows is not None:
                params.append({"name": "min_rows", "value": str(check.min_rows)})
            if check.max_rows is not None:
                params.append({"name": "max_rows", "value": str(check.max_rows)})

        return params


class QualityCheckPublisher:
    """
    Publishes quality check results to OpenMetadata.

    Handles publishing test definitions, test cases, and test results.
    """

    def __init__(self, om_client: Any):
        """
        Initialize publisher.

        Args:
            om_client: OpenMetadataClient instance
        """
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

                # Try to create test definition
                self.om_client.create_test_definition(
                    test_name=test_def["name"],
                    test_type=test_def["testType"],
                    description=test_def.get("description"),
                )

                logger.info(f"Published test definition: {test_def['name']}")
                stats["created"] += 1

            except Exception as e:
                logger.error(
                    f"Failed to publish test definition for {table_fqn}: {e}"
                )
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

                # Try to create test case
                self.om_client.create_test_case(
                    test_case_name=test_case["name"],
                    table_fqn=table_fqn,
                    test_definition_name=test_case["testDefinition"]["name"],
                    parameters={
                        p["name"]: p["value"] for p in test_case.get("parameterValues", [])
                    },
                    description=test_case.get("description"),
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

                # Publish to OpenMetadata
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
                test_case = QualityCheckMapper.map_dbt_test_to_openmetadata(
                    dbt_test, table_fqn
                )

                # Create test case for dbt test
                self.om_client.create_test_case(
                    test_case_name=test_case["name"],
                    table_fqn=table_fqn,
                    test_definition_name=test_case["testDefinition"]["name"],
                    parameters={
                        p["name"]: p["value"] for p in test_case.get("parameterValues", [])
                    },
                    description=test_case.get("description"),
                )

                logger.info(f"Published dbt test case: {test_case['name']}")
                stats["created"] += 1

            except Exception as e:
                logger.error(f"Failed to publish dbt test for {table_fqn}: {e}")
                stats["failed"] += 1

        return stats
