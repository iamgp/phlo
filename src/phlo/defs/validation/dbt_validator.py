"""
DBT Validator Resource for running dbt tests and parsing results.

This module provides a Dagster resource for executing dbt test commands on
specified Nessie branches and parsing the test results to determine pass/fail status.
"""

import json
import os
import subprocess
from typing import Any

import dagster as dg
from phlo.config import config


class DBTValidatorResource(dg.ConfigurableResource):
    """Runs dbt tests and parses results."""

    def run_tests_for_model(
        self,
        model_name: str,
        branch_name: str
    ) -> dict[str, Any]:
        """
        Run dbt tests for a specific model on specified branch.

        Args:
            model_name: Model name (e.g., "fct_glucose_readings")
            branch_name: Nessie branch to test

        Returns:
            Same format as run_tests()
        """
        return self.run_tests(branch_name, select=model_name)

    def run_tests(
        self,
        branch_name: str,
        select: str | None = None
    ) -> dict[str, Any]:
        """
        Run dbt test command on specified branch.

        Args:
            branch_name: Nessie branch to test
            select: dbt selection syntax (e.g., "tag:bronze", "tag:silver")

        Returns:
            {
                "tests_run": int,
                "passed": int,
                "failed": int,
                "skipped": int,
                "all_passed": bool,
                "failures": [
                    {
                        "test_name": "not_null_fct_glucose_readings_entry_id",
                        "model": "fct_glucose_readings",
                        "error_message": "...",
                        "failed_rows": 5
                    }
                ]
            }
        """
        # Build dbt test command
        cmd = [
            "dbt", "test",
            "--project-dir", str(config.dbt_project_path),
            "--profiles-dir", str(config.dbt_profiles_path),
        ]

        if select:
            cmd.extend(["--select", select])

        # Set environment variable for branch
        env = os.environ.copy()
        env["NESSIE_REF"] = branch_name

        try:
            # Execute dbt test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=600  # 10 minute timeout
            )

            # Parse run_results.json
            results_path = config.dbt_project_path / "target" / "run_results.json"

            if not results_path.exists():
                return {
                    "tests_run": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "all_passed": False,
                    "failures": [{
                        "error": "run_results.json not found",
                        "stderr": result.stderr
                    }]
                }

            with open(results_path) as f:
                run_results = json.load(f)

            # Aggregate results
            tests_run = 0
            passed = 0
            failed = 0
            skipped = 0
            failures = []

            for result_node in run_results.get("results", []):
                # Only process test nodes
                if result_node.get("unique_id", "").startswith("test."):
                    tests_run += 1

                    status = result_node.get("status", "unknown")

                    if status == "pass":
                        passed += 1
                    elif status == "fail":
                        failed += 1
                        failures.append({
                            "test_name": result_node.get("unique_id", "unknown").split(".")[-1],
                            "model": self._extract_model_name(result_node),
                            "error_message": result_node.get("message", ""),
                            "failed_rows": result_node.get("failures", 0)
                        })
                    elif status in ["skipped", "skip"]:
                        skipped += 1

            all_passed = failed == 0 and tests_run > 0

            return {
                "tests_run": tests_run,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "all_passed": all_passed,
                "failures": failures
            }

        except subprocess.TimeoutExpired:
            return {
                "tests_run": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "all_passed": False,
                "failures": [{"error": "dbt test command timed out after 10 minutes"}]
            }
        except Exception as e:
            return {
                "tests_run": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "all_passed": False,
                "failures": [{"error": str(e)}]
            }

    def _extract_model_name(self, result_node: dict) -> str:
        """Extract model name from result node."""
        # Try to get from depends_on
        depends_on = result_node.get("depends_on", {})
        nodes = depends_on.get("nodes", [])

        if nodes:
            # Get first dependency (usually the model being tested)
            first_dep = nodes[0]
            if "." in first_dep:
                parts = first_dep.split(".")
                return parts[-1]  # Return last part (model name)

        # Fallback: try to extract from unique_id
        unique_id = result_node.get("unique_id", "")
        if unique_id:
            # Format: test.project.test_name.model_name.column_name
            parts = unique_id.split(".")
            if len(parts) >= 4:
                return parts[3]

        return "unknown"
