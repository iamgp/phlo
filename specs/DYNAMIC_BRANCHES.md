# Technical Specification: Dynamic Branch Workflow with Automated Quality Gates

**Version**: 1.0
**Date**: 2025-01-11
**Status**: Approved

## 1. Overview

### Goal

Transform from static dev/main branches to dynamic feature branches with comprehensive validation gates and automatic promotion to main after all tests pass.

### Current State

- Static `dev` and `main` branches created at startup
- Manual promotion via `promote_dev_to_main` asset
- No validation gates before promotion
- Asset checks are non-blocking

### Target State

- Dynamic `pipeline/run-{id}` branches per pipeline run
- Automatic promotion after all validations pass
- Blocking validation gates (Pandera, dbt tests, freshness, schema compatibility)
- Configurable retention and validation strictness
- Automatic retry with logging for failed validations

---

## 2. Architecture

### 2.1 Branch Lifecycle

```
Pipeline Start
    ↓
Create pipeline/run-{dagster_run_id} from main
    ↓
Ingest data to pipeline branch
    ↓
Run transformations on pipeline branch
    ↓
Run validation gates (BLOCKING)
    ├─ Pandera validation (critical checks block, non-critical warn)
    ├─ DBT tests (all must pass)
    ├─ Freshness checks (configurable: block or warn)
    └─ Schema compatibility (allow additive, block breaking)
    ↓
All validations passed?
    ├─ YES → Auto-promote to main
    │         ├─ Fast-forward merge (assign_branch)
    │         ├─ Create timestamp tag v{YYYYMMDD_HHMMSS}
    │         └─ Schedule branch cleanup (sensor-based)
    └─ NO → Log failures, retry if configured
            └─ Keep branch for debugging
            └─ Manual cleanup after retention period
```

### 2.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   BranchManagerResource                     │
│  - create_pipeline_branch(run_id) → branch_name             │
│  - cleanup_old_branches(retention_days)                     │
│  - get_branch_metadata(branch_name) → metadata              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Pipeline Assets (on pipeline branch)       │
│  - ingest_data (DLT → Parquet → Iceberg)                    │
│  - transform_data (dbt on pipeline branch)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Validation Orchestrator                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PanderaValidator (severity-based blocking)         │   │
│  │  - Critical checks: BLOCK                           │   │
│  │  - Non-critical checks: WARN                        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DBTTestValidator                                   │   │
│  │  - Run dbt test on pipeline branch                  │   │
│  │  - Parse results, BLOCK if any failures             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FreshnessValidator (configurable blocking)         │   │
│  │  - Check Dagster FreshnessPolicy status             │   │
│  │  - BLOCK or WARN based on config                    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  SchemaCompatibilityValidator                       │   │
│  │  - Compare pipeline branch vs main schemas          │   │
│  │  - BLOCK: dropped columns, type changes             │   │
│  │  - ALLOW: new columns (additive changes)            │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  RetryLogic                                         │   │
│  │  - Automatic retry on validation failures           │   │
│  │  - Detailed logging of retry attempts               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              PromotionSensor (automatic trigger)             │
│  - Monitors validation_orchestrator completion               │
│  - If all_passed=True → trigger promote_to_main             │
│  - If all_passed=False → log failures, keep branch          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     promote_to_main Asset                    │
│  - assign_branch(main, pipeline_branch)                      │
│  - tag_snapshot(v{timestamp}, main)                          │
│  - trigger cleanup_sensor                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               CleanupSensor (triggered after promotion)      │
│  - Waits for retention period (N days)                       │
│  - Deletes old pipeline branches                             │
│  - Logs cleanup operations                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Configuration Schema

### 3.1 New Configuration Fields

**File**: `src/cascade/config.py`

```python
class CascadeConfig(BaseSettings):
    # ... existing fields ...

    # Nessie Branch Management
    branch_retention_days: int = Field(
        default=7,
        description="Days to retain pipeline branches after successful merge"
    )
    branch_retention_days_failed: int = Field(
        default=14,
        description="Days to retain pipeline branches that failed validation"
    )
    auto_promote_enabled: bool = Field(
        default=True,
        description="Enable automatic promotion to main after validation passes"
    )

    # Validation Gates
    freshness_blocks_promotion: bool = Field(
        default=False,
        description="Whether freshness policy failures should block promotion to main"
    )
    pandera_critical_level: str = Field(
        default="error",
        description="Pandera check severity that blocks promotion (error|warning|info)"
    )

    # Validation Retry
    validation_retry_enabled: bool = Field(
        default=True,
        description="Enable automatic retry of failed validations"
    )
    validation_retry_max_attempts: int = Field(
        default=3,
        description="Maximum number of validation retry attempts"
    )
    validation_retry_delay_seconds: int = Field(
        default=300,
        description="Delay between validation retry attempts (seconds)"
    )

    # Freshness Thresholds (override asset-level policies)
    glucose_freshness_hours: int = Field(
        default=24,
        description="Max age of glucose data before considered stale"
    )
    github_events_freshness_hours: int = Field(
        default=24,
        description="Max age of GitHub events before considered stale"
    )
    github_stats_freshness_hours: int = Field(
        default=48,
        description="Max age of GitHub repo stats before considered stale"
    )
```

---

## 4. Component Specifications

### 4.1 BranchManagerResource

**File**: `src/cascade/defs/nessie/branch_manager.py`

**Responsibilities**:

- Create dynamic pipeline branches
- Track branch lifecycle metadata
- Schedule and execute branch cleanup

**Key Methods**:

```python
class BranchManagerResource(ConfigurableResource):
    """Manages dynamic Nessie branch lifecycle."""

    nessie: NessieResource
    retention_days: int
    retention_days_failed: int

    def create_pipeline_branch(
        self,
        run_id: str,
        source_ref: str = "main"
    ) -> dict[str, Any]:
        """
        Create a new pipeline branch for this pipeline run.

        Args:
            run_id: Dagster run ID
            source_ref: Source branch to branch from (default: main)

        Returns:
            {
                "branch_name": "pipeline/run-{run_id}",
                "created_from": source_ref,
                "created_at": ISO timestamp,
                "source_hash": commit hash
            }
        """
        branch_name = f"pipeline/run-{run_id}"
        result = self.nessie.create_branch(branch_name, source_ref)
        return {
            "branch_name": branch_name,
            "created_from": source_ref,
            "created_at": datetime.now().isoformat(),
            "source_hash": result.get("hash")
        }

    def schedule_cleanup(
        self,
        branch_name: str,
        retention_days: int,
        promotion_succeeded: bool
    ) -> dict[str, Any]:
        """
        Schedule branch for cleanup after retention period.

        Stores metadata in Dagster storage for cleanup sensor to process.

        Args:
            branch_name: Branch to cleanup
            retention_days: Days to retain
            promotion_succeeded: Whether promotion succeeded

        Returns:
            {
                "branch_name": branch_name,
                "cleanup_after": ISO timestamp,
                "promotion_succeeded": bool
            }
        """
        cleanup_after = datetime.now() + timedelta(days=retention_days)
        return {
            "branch_name": branch_name,
            "cleanup_after": cleanup_after.isoformat(),
            "promotion_succeeded": promotion_succeeded,
            "scheduled_at": datetime.now().isoformat()
        }

    def cleanup_old_branches(self, dry_run: bool = False) -> list[str]:
        """
        Clean up branches past retention period.

        Called by cleanup sensor.

        Args:
            dry_run: If True, return branches that would be deleted without deleting

        Returns:
            List of deleted (or would-be-deleted) branch names
        """
        # Query Dagster storage for branches scheduled for cleanup
        # Filter by cleanup_after <= now()
        # Delete branches if not dry_run
        # Return list of deleted branches
```

### 4.2 Validation Orchestrator

**File**: `src/cascade/defs/validation/orchestrator.py`

**Responsibilities**:

- Coordinate all validation gates
- Aggregate validation results
- Support retry logic

**Implementation**:

```python
@asset(
    deps=[
        "fct_glucose_readings",
        "fct_daily_glucose_metrics",
        "fct_github_user_events",
        "fct_github_repo_stats"
    ],
    retry_policy=RetryPolicy(max_retries=3, delay=300)
)
def validation_orchestrator(
    context: AssetExecutionContext,
    pandera_validator: PanderaValidatorResource,
    dbt_validator: DBTValidatorResource,
    freshness_validator: FreshnessValidatorResource,
    schema_validator: SchemaCompatibilityValidatorResource,
    config: CascadeConfig,
) -> MaterializeResult:
    """
    Runs all validation gates and aggregates results.

    Supports automatic retry with detailed logging.

    Returns:
        MaterializeResult with metadata:
        {
            "all_passed": bool,
            "pandera_results": {...},
            "dbt_results": {...},
            "freshness_results": {...},
            "schema_results": {...},
            "blocking_failures": [list of failure descriptions],
            "warnings": [list of warnings],
            "retry_attempt": int,
            "branch_name": str
        }
    """
    branch_name = context.run_config.get("branch_name")
    retry_attempt = context.retry_number

    context.log.info(f"Running validation orchestrator on branch {branch_name} (attempt {retry_attempt + 1})")

    # Run all validators
    pandera_results = pandera_validator.validate_all_tables(branch_name)
    dbt_results = dbt_validator.run_tests(branch_name)
    freshness_results = freshness_validator.check_freshness(context)
    schema_results = schema_validator.check_compatibility(branch_name, "main")

    # Aggregate results
    all_passed = all([
        pandera_results["all_passed"],
        dbt_results["all_passed"],
        freshness_results["all_fresh"] or not config.freshness_blocks_promotion,
        schema_results["compatible"]
    ])

    blocking_failures = []
    warnings = []

    if not pandera_results["all_passed"]:
        blocking_failures.extend(pandera_results["critical_failures"])
        warnings.extend(pandera_results.get("warnings", []))

    if not dbt_results["all_passed"]:
        blocking_failures.extend([f"dbt test failed: {f['test_name']}" for f in dbt_results["failures"]])

    if not freshness_results["all_fresh"] and config.freshness_blocks_promotion:
        blocking_failures.extend([f"Freshness violation: {v['asset']}" for v in freshness_results["violations"]])
    elif not freshness_results["all_fresh"]:
        warnings.extend([f"Freshness warning: {v['asset']}" for v in freshness_results["violations"]])

    if not schema_results["compatible"]:
        blocking_failures.extend([f"Schema breaking change: {c['details']}" for c in schema_results["breaking_changes"]])

    # Log results
    if all_passed:
        context.log.info(f"All validations passed for branch {branch_name}")
    else:
        context.log.error(f"Validation failures for branch {branch_name}: {blocking_failures}")
        if config.validation_retry_enabled and retry_attempt < config.validation_retry_max_attempts - 1:
            context.log.warning(f"Will retry validation (attempt {retry_attempt + 2}/{config.validation_retry_max_attempts})")

    return MaterializeResult(
        metadata={
            "all_passed": all_passed,
            "branch_name": branch_name,
            "pandera_results": pandera_results,
            "dbt_results": dbt_results,
            "freshness_results": freshness_results,
            "schema_results": schema_results,
            "blocking_failures": blocking_failures,
            "warnings": warnings,
            "retry_attempt": retry_attempt,
            "validated_at": datetime.now().isoformat()
        }
    )
```

### 4.3 PanderaValidatorResource

**File**: `src/cascade/defs/validation/pandera_validator.py`

**Responsibilities**:

- Execute Pandera schema validation
- Support severity-based blocking (critical vs non-critical)
- Return detailed failure information

**Implementation**:

```python
class PanderaValidatorResource(ConfigurableResource):
    """Validates data using Pandera schemas with severity-based blocking."""

    trino: TrinoResource
    critical_level: str  # "error" | "warning" | "info"

    def validate_all_tables(
        self,
        branch_name: str
    ) -> dict[str, Any]:
        """
        Run Pandera validation on all fact tables on given branch.

        Returns:
            {
                "tables_validated": int,
                "all_passed": bool,
                "critical_failures": [
                    {
                        "table": "fct_glucose_readings",
                        "severity": "error",
                        "failed_checks": [...],
                        "sample_failures": [...]
                    }
                ],
                "warnings": [...]
            }
        """
        tables_to_validate = [
            ("fct_glucose_readings", FactGlucoseReadings),
            ("fct_daily_glucose_metrics", FactDailyGlucoseMetrics),
            ("fct_github_user_events", FactGitHubUserEvents),
            ("fct_github_repo_stats", FactGitHubRepoStats),
        ]

        critical_failures = []
        warnings = []

        for table_name, schema_class in tables_to_validate:
            result = self._validate_table(table_name, schema_class, branch_name)

            if result["has_failures"]:
                # Filter by severity
                for failure in result["failures"]:
                    if failure["severity"] == self.critical_level:
                        critical_failures.append(failure)
                    else:
                        warnings.append(failure)

        all_passed = len(critical_failures) == 0

        return {
            "tables_validated": len(tables_to_validate),
            "all_passed": all_passed,
            "critical_failures": critical_failures,
            "warnings": warnings
        }

    def _validate_table(
        self,
        table_name: str,
        schema_class: Type[pa.DataFrameModel],
        branch_name: str
    ) -> dict[str, Any]:
        """Validate a single table against its Pandera schema."""
        # Query table from Trino with branch session property
        conn = self.trino.get_connection(override_ref=branch_name)
        df = pd.read_sql(f"SELECT * FROM silver.{table_name}", conn)

        try:
            schema_class.validate(df, lazy=True)
            return {"has_failures": False}
        except pandera.errors.SchemaErrors as err:
            failure_cases = err.failure_cases

            # Extract severity from field metadata
            failures = []
            for _, failure_row in failure_cases.iterrows():
                field_name = failure_row["column"]
                field = schema_class.__fields__[field_name]
                severity = field.metadata.get("severity", "error")

                failures.append({
                    "table": table_name,
                    "column": field_name,
                    "severity": severity,
                    "check": failure_row["check"],
                    "failure_count": 1
                })

            return {
                "has_failures": True,
                "failures": failures
            }
```

**Pandera Schema Enhancement**:

**File**: `src/cascade/schemas/glucose.py`

```python
class FactGlucoseReadings(pa.DataFrameModel):
    """Fact table schema with severity annotations."""

    class Config:
        strict = True
        coerce = True

    entry_id: pa.typing.Series[str] = pa.Field(
        unique=True,
        nullable=False,
        metadata={"severity": "error"}  # Critical check
    )

    glucose_mg_dl: pa.typing.Series[int] = pa.Field(
        ge=20,
        le=600,
        metadata={"severity": "error"}  # Critical check
    )

    direction: pa.typing.Series[str] = pa.Field(
        isin=VALID_DIRECTIONS,
        metadata={"severity": "warning"}  # Non-critical check
    )

    reading_timestamp: pa.typing.Series[pd.Timestamp] = pa.Field(
        nullable=False,
        metadata={"severity": "error"}
    )

    hour_of_day: pa.typing.Series[int] = pa.Field(
        ge=0,
        le=23,
        metadata={"severity": "error"}
    )

    day_of_week: pa.typing.Series[int] = pa.Field(
        ge=0,
        le=6,
        metadata={"severity": "error"}
    )

    glucose_category: pa.typing.Series[str] = pa.Field(
        isin=["hypoglycemia", "in_range", "hyperglycemia_mild", "hyperglycemia_severe"],
        metadata={"severity": "warning"}
    )

    is_in_range: pa.typing.Series[bool] = pa.Field(
        nullable=False,
        metadata={"severity": "warning"}
    )
```

### 4.4 DBTValidatorResource

**File**: `src/cascade/defs/validation/dbt_validator.py`

**Responsibilities**:

- Execute dbt test command on specified branch
- Parse test results from run_results.json
- Return aggregated pass/fail status

**Implementation**:

```python
import json
import subprocess
from pathlib import Path

class DBTValidatorResource(ConfigurableResource):
    """Runs dbt tests and parses results."""

    dbt_project_dir: str = "/opt/dagster/app/transforms/dbt"
    dbt_profiles_dir: str = "/opt/dagster/app/transforms/dbt/profiles"

    def run_tests(
        self,
        branch_name: str,
        select: str | None = None
    ) -> dict[str, Any]:
        """
        Run dbt test command on specified branch.

        Args:
            branch_name: Nessie branch to test
            select: dbt selection syntax (e.g., "tag:bronze")

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
            "--project-dir", self.dbt_project_dir,
            "--profiles-dir", self.dbt_profiles_dir,
            "--vars", f'{{"nessie_ref": "{branch_name}"}}'
        ]

        if select:
            cmd.extend(["--select", select])

        # Execute dbt test
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, "NESSIE_REF": branch_name}
        )

        # Parse run_results.json
        results_path = Path(self.dbt_project_dir) / "target" / "run_results.json"

        if not results_path.exists():
            return {
                "tests_run": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "all_passed": False,
                "failures": [{"error": "run_results.json not found"}]
            }

        with open(results_path) as f:
            run_results = json.load(f)

        # Aggregate results
        tests_run = 0
        passed = 0
        failed = 0
        skipped = 0
        failures = []

        for result_node in run_results["results"]:
            if result_node["node"]["resource_type"] == "test":
                tests_run += 1

                if result_node["status"] == "pass":
                    passed += 1
                elif result_node["status"] == "fail":
                    failed += 1
                    failures.append({
                        "test_name": result_node["node"]["name"],
                        "model": result_node["node"].get("attached_node"),
                        "error_message": result_node.get("message", ""),
                        "failed_rows": result_node.get("failures", 0)
                    })
                elif result_node["status"] == "skipped":
                    skipped += 1

        all_passed = failed == 0

        return {
            "tests_run": tests_run,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "all_passed": all_passed,
            "failures": failures
        }
```

### 4.5 FreshnessValidatorResource

**File**: `src/cascade/defs/validation/freshness_validator.py`

**Responsibilities**:

- Check Dagster FreshnessPolicy status
- Query asset event logs for last materialization
- Support configurable blocking behavior

**Implementation**:

```python
from dagster import AssetExecutionContext, DagsterInstance
from datetime import datetime, timedelta

class FreshnessValidatorResource(ConfigurableResource):
    """Validates data freshness based on FreshnessPolicy and config."""

    blocks_promotion: bool
    glucose_freshness_hours: int
    github_events_freshness_hours: int
    github_stats_freshness_hours: int

    def check_freshness(
        self,
        context: AssetExecutionContext
    ) -> dict[str, Any]:
        """
        Check Dagster FreshnessPolicy status for all assets.

        Returns:
            {
                "all_fresh": bool,
                "blocks_promotion": bool,
                "violations": [
                    {
                        "asset": "dlt_glucose_entries",
                        "last_updated": ISO timestamp,
                        "age_hours": 36,
                        "threshold_hours": 24,
                        "severity": "fail"|"warn"
                    }
                ]
            }
        """
        assets_to_check = [
            ("dlt_glucose_entries", self.glucose_freshness_hours),
            ("dlt_github_user_events", self.github_events_freshness_hours),
            ("dlt_github_repo_stats", self.github_stats_freshness_hours),
        ]

        violations = []

        for asset_key, threshold_hours in assets_to_check:
            last_materialization = self._get_last_materialization(context, asset_key)

            if last_materialization is None:
                violations.append({
                    "asset": asset_key,
                    "last_updated": None,
                    "age_hours": float("inf"),
                    "threshold_hours": threshold_hours,
                    "severity": "fail"
                })
                continue

            age = datetime.now() - last_materialization
            age_hours = age.total_seconds() / 3600

            if age_hours > threshold_hours:
                violations.append({
                    "asset": asset_key,
                    "last_updated": last_materialization.isoformat(),
                    "age_hours": age_hours,
                    "threshold_hours": threshold_hours,
                    "severity": "fail" if self.blocks_promotion else "warn"
                })

        all_fresh = len(violations) == 0

        return {
            "all_fresh": all_fresh,
            "blocks_promotion": self.blocks_promotion,
            "violations": violations
        }

    def _get_last_materialization(
        self,
        context: AssetExecutionContext,
        asset_key: str
    ) -> datetime | None:
        """Get timestamp of last materialization for asset."""
        instance = context.instance

        events = instance.get_event_records(
            event_records_filter=EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=AssetKey([asset_key])
            ),
            limit=1
        )

        if not events:
            return None

        return events[0].timestamp
```

### 4.6 SchemaCompatibilityValidatorResource

**File**: `src/cascade/defs/validation/schema_validator.py`

**Responsibilities**:

- Compare Iceberg schemas between branches
- Detect breaking changes (dropped columns, type changes)
- Allow additive changes (new columns)

**Implementation**:

```python
from pyiceberg.schema import Schema
from pyiceberg.table import Table

class SchemaCompatibilityValidatorResource(ConfigurableResource):
    """Validates schema compatibility between branches."""

    def check_compatibility(
        self,
        feature_branch: str,
        target_branch: str = "main"
    ) -> dict[str, Any]:
        """
        Compare schemas between feature and target branches.

        Allows:
        - New columns (additive changes)

        Blocks:
        - Dropped columns
        - Type changes
        - Constraint changes (nullability, etc.)

        Returns:
            {
                "compatible": bool,
                "tables_checked": [str],
                "breaking_changes": [
                    {
                        "table": "bronze.entries",
                        "change_type": "column_dropped",
                        "details": "Column 'device' exists in main but not in feature branch"
                    }
                ],
                "additive_changes": [
                    {
                        "table": "bronze.entries",
                        "change_type": "column_added",
                        "details": "New column 'noise_level' in feature branch"
                    }
                ]
            }
        """
        # Get catalogs for both branches
        feature_catalog = get_catalog(ref=feature_branch)
        target_catalog = get_catalog(ref=target_branch)

        # Get list of tables to compare
        tables_to_check = [
            "bronze.entries",
            "silver.fct_glucose_readings",
            "silver.fct_daily_glucose_metrics",
            "bronze.github_user_events",
            "silver.fct_github_user_events",
            "bronze.github_repo_stats",
            "silver.fct_github_repo_stats",
        ]

        breaking_changes = []
        additive_changes = []

        for table_name in tables_to_check:
            try:
                feature_table = feature_catalog.load_table(table_name)
                target_table = target_catalog.load_table(table_name)

                changes = self._compare_schemas(
                    table_name,
                    feature_table.schema(),
                    target_table.schema()
                )

                breaking_changes.extend(changes["breaking"])
                additive_changes.extend(changes["additive"])

            except Exception as e:
                # Table doesn't exist in one of the branches
                if table_name in str(e):
                    additive_changes.append({
                        "table": table_name,
                        "change_type": "table_added",
                        "details": f"New table '{table_name}' in {feature_branch}"
                    })

        compatible = len(breaking_changes) == 0

        return {
            "compatible": compatible,
            "tables_checked": tables_to_check,
            "breaking_changes": breaking_changes,
            "additive_changes": additive_changes
        }

    def _compare_schemas(
        self,
        table_name: str,
        feature_schema: Schema,
        target_schema: Schema
    ) -> dict[str, list]:
        """Compare two schemas and categorize changes."""
        breaking = []
        additive = []

        # Build field maps
        feature_fields = {f.name: f for f in feature_schema.fields}
        target_fields = {f.name: f for f in target_schema.fields}

        # Check for dropped columns (breaking)
        for field_name, field in target_fields.items():
            if field_name not in feature_fields:
                breaking.append({
                    "table": table_name,
                    "change_type": "column_dropped",
                    "details": f"Column '{field_name}' exists in {target_branch} but not in {feature_branch}"
                })

        # Check for new columns (additive)
        for field_name, field in feature_fields.items():
            if field_name not in target_fields:
                additive.append({
                    "table": table_name,
                    "change_type": "column_added",
                    "details": f"New column '{field_name}' in {feature_branch}"
                })
            else:
                # Check for type changes (breaking)
                target_field = target_fields[field_name]
                if field.field_type != target_field.field_type:
                    breaking.append({
                        "table": table_name,
                        "change_type": "type_changed",
                        "details": f"Column '{field_name}' type changed from {target_field.field_type} to {field.field_type}"
                    })

        return {"breaking": breaking, "additive": additive}
```

### 4.7 Promotion and Cleanup Sensors

**File**: `src/cascade/defs/sensors/promotion_sensor.py`

**Responsibilities**:

- Monitor validation_orchestrator completion
- Trigger promote_to_main on success
- Trigger branch cleanup after promotion

**Implementation**:

```python
@sensor(
    name="auto_promotion_sensor",
    minimum_interval_seconds=30,
    description="Automatically promotes pipeline branch to main after validation passes"
)
def auto_promotion_sensor(
    context: SensorEvaluationContext,
    config: CascadeConfig,
) -> SensorResult:
    """
    Monitors validation_orchestrator completion.
    Triggers promote_to_main if all validations passed.

    Returns:
        RunRequest to materialize promote_to_main with branch context
    """
    if not config.auto_promote_enabled:
        return SkipReason("Auto-promotion disabled in config")

    # Query latest validation_orchestrator materialization
    instance = context.instance

    events = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=AssetKey(["validation_orchestrator"])
        ),
        limit=1
    )

    if not events:
        return SkipReason("No validation_orchestrator runs found")

    latest_event = events[0]
    metadata = latest_event.asset_materialization.metadata

    all_passed = metadata.get("all_passed", False)
    branch_name = metadata.get("branch_name")

    if not all_passed:
        blocking_failures = metadata.get("blocking_failures", [])
        context.log.warning(
            f"Validation failed for branch {branch_name}. Failures: {blocking_failures}"
        )
        return SkipReason(f"Validation failed for branch {branch_name}")

    # Check if we've already promoted this branch
    cursor_key = f"promoted_{branch_name}"
    if context.cursor and context.cursor.get(cursor_key):
        return SkipReason(f"Branch {branch_name} already promoted")

    context.log.info(f"All validations passed for branch {branch_name}. Triggering promotion.")

    # Update cursor to prevent duplicate promotions
    context.update_cursor({cursor_key: True})

    return RunRequest(
        run_key=f"promote_{branch_name}_{latest_event.timestamp}",
        run_config={"branch_name": branch_name},
        tags={"branch": branch_name, "auto_promoted": "true"}
    )


@sensor(
    name="branch_cleanup_sensor",
    minimum_interval_seconds=3600,  # Run hourly
    description="Cleans up old pipeline branches after retention period"
)
def branch_cleanup_sensor(
    context: SensorEvaluationContext,
    branch_manager: BranchManagerResource,
) -> SensorResult:
    """
    Cleans up pipeline branches that have exceeded their retention period.

    Triggered hourly to check for branches ready for cleanup.
    """
    context.log.info("Checking for branches to clean up")

    # Query Dagster storage for branches scheduled for cleanup
    # This would use instance.get_event_records to find promote_to_main
    # materializations with cleanup metadata

    instance = context.instance

    promote_events = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=AssetKey(["promote_to_main"])
        ),
        limit=100
    )

    branches_to_cleanup = []
    now = datetime.now()

    for event in promote_events:
        metadata = event.asset_materialization.metadata
        branch_name = metadata.get("branch_promoted")
        cleanup_after_str = metadata.get("cleanup_scheduled_for")

        if not cleanup_after_str:
            continue

        cleanup_after = datetime.fromisoformat(cleanup_after_str)

        # Check if it's time to cleanup
        if now >= cleanup_after:
            cursor_key = f"cleaned_{branch_name}"
            if not (context.cursor and context.cursor.get(cursor_key)):
                branches_to_cleanup.append(branch_name)

    if not branches_to_cleanup:
        return SkipReason("No branches ready for cleanup")

    context.log.info(f"Cleaning up {len(branches_to_cleanup)} branches: {branches_to_cleanup}")

    # Perform cleanup
    cleaned_branches = branch_manager.cleanup_old_branches(dry_run=False)

    # Update cursor
    new_cursor = context.cursor or {}
    for branch in cleaned_branches:
        new_cursor[f"cleaned_{branch}"] = True
    context.update_cursor(new_cursor)

    return SensorResult(
        skip_reason=None,
        cursor=json.dumps(new_cursor)
    )
```

### 4.8 Updated promote_to_main Asset

**File**: `src/cascade/defs/nessie/workflow.py`

**Changes**:

- Add dependency on validation_orchestrator
- Accept branch_name from run_config
- Schedule cleanup via metadata (for sensor to pick up)

**Implementation**:

```python
@asset(
    deps=[AssetKey(["validation_orchestrator"])],
    op_tags={"nessie_operation": "promotion"}
)
def promote_to_main(
    context: AssetExecutionContext,
    nessie: NessieResource,
    branch_manager: BranchManagerResource,
    config: CascadeConfig,
) -> MaterializeResult:
    """
    Promote pipeline branch to main after validation.

    Run config:
        branch_name: Name of pipeline branch to promote

    Returns:
        MaterializeResult with promotion metadata
    """
    branch_name = context.run_config.get("branch_name")

    if not branch_name:
        raise ValueError("branch_name must be provided in run_config")

    context.log.info(f"Promoting branch {branch_name} to main")

    # 1. Verify validation_orchestrator passed (redundant check for safety)
    instance = context.instance
    validation_events = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=AssetKey(["validation_orchestrator"])
        ),
        limit=1
    )

    if validation_events:
        validation_metadata = validation_events[0].asset_materialization.metadata
        if not validation_metadata.get("all_passed"):
            raise Exception(
                f"Cannot promote: validation failures exist. "
                f"Failures: {validation_metadata.get('blocking_failures')}"
            )

    # 2. Fast-forward merge to main
    try:
        nessie.assign_branch("main", branch_name)
        context.log.info(f"Successfully merged {branch_name} to main")
    except Exception as e:
        context.log.error(f"Failed to merge {branch_name} to main: {e}")
        raise

    # 3. Create production tag
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        tag_result = nessie.tag_snapshot(f"v{timestamp}", "main")
        context.log.info(f"Created tag: {tag_result['name']}")
    except Exception as e:
        context.log.error(f"Failed to create tag: {e}")
        raise

    # 4. Schedule branch cleanup
    cleanup_result = branch_manager.schedule_cleanup(
        branch_name=branch_name,
        retention_days=config.branch_retention_days,
        promotion_succeeded=True
    )

    context.log.info(
        f"Scheduled cleanup for {branch_name} after {cleanup_result['cleanup_after']}"
    )

    return MaterializeResult(
        metadata={
            "branch_promoted": branch_name,
            "promoted_at": timestamp,
            "tag_created": tag_result["name"],
            "cleanup_scheduled_for": cleanup_result["cleanup_after"]
        }
    )
```

---

## 5. Resource Updates

### 5.1 IcebergResource

**File**: `src/cascade/defs/resources/iceberg.py`

**Changes**:

- Add support for dynamic branch override
- Default to main if no branch specified

```python
class IcebergResource(ConfigurableResource):
    """Iceberg catalog resource with dynamic branch support."""

    ref: str = "main"  # Default branch

    def get_catalog(self, override_ref: str | None = None) -> Catalog:
        """
        Get catalog for specified branch.

        Args:
            override_ref: Override default ref for this operation
        """
        branch = override_ref or self.ref
        return get_catalog(ref=branch)

    def ensure_table(
        self,
        table_name: str,
        schema: Schema,
        partition_spec: PartitionSpec | None = None,
        override_ref: str | None = None
    ) -> Table:
        """
        Ensure table exists on specified branch.

        Args:
            table_name: Fully qualified table name (namespace.table)
            schema: Iceberg schema
            partition_spec: Optional partitioning
            override_ref: Override default branch
        """
        catalog = self.get_catalog(override_ref)
        # ... rest of implementation ...
```

### 5.2 TrinoResource

**File**: `src/cascade/defs/resources/trino.py`

**Changes**:

- Add branch-specific session properties
- Support dynamic branch override

```python
class TrinoResource(ConfigurableResource):
    """Trino connection with Nessie branch session properties."""

    host: str
    port: int
    user: str
    catalog: str = "iceberg"
    schema: str = "bronze"
    nessie_ref: str = "main"  # Default branch

    def get_connection(self, override_ref: str | None = None):
        """Get Trino connection with branch-specific session properties."""
        branch = override_ref or self.nessie_ref

        session_properties = {
            "iceberg.nessie_reference_name": branch
        }

        return trino.dbapi.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            catalog=self.catalog,
            schema=self.schema,
            session_properties=session_properties,
        )
```

---

## 6. Ingestion Asset Updates

**File**: `src/cascade/defs/ingestion/dlt_assets.py`

**Changes**:

- Accept branch_name from run_config
- Pass branch to IcebergResource operations

**Example**:

```python
@asset(
    group_name="ingestion",
    freshness_policy=FreshnessPolicy.time_window(
        fail_window=timedelta(hours=24),
        warn_window=timedelta(hours=1)
    )
)
def dlt_glucose_entries(
    context: AssetExecutionContext,
    iceberg: IcebergResource,
    config: CascadeConfig,
) -> MaterializeResult:
    """Ingest Nightscout glucose entries to Iceberg via DLT."""

    # Get branch from run_config (set by pipeline job)
    branch_name = context.run_config.get("branch_name", "main")
    context.log.info(f"Ingesting to branch: {branch_name}")

    # ... DLT ingestion logic ...

    # Merge to Iceberg on specified branch
    catalog = iceberg.get_catalog(override_ref=branch_name)
    table = catalog.load_table("bronze.entries")

    # ... merge logic ...

    return MaterializeResult(
        metadata={
            "branch": branch_name,
            "rows_ingested": row_count,
            # ... other metadata ...
        }
    )
```

**Similar updates for**:

- `src/cascade/defs/ingestion/github_assets.py` (all GitHub ingestion assets)

---

## 7. Job Definitions

**File**: `src/cascade/defs/__init__.py`

**Remove**:

- Old `DEV_PIPELINE_JOB` and `PROD_PROMOTION_JOB`

**Add**:

```python
# Full pipeline: branch creation → ingestion → transformation → validation → promotion
full_pipeline_job = define_asset_job(
    name="full_pipeline",
    description="Complete pipeline with automatic promotion",
    selection=AssetSelection.groups(
        "branch_management",
        "ingestion",
        "transform",
        "validation"
    ),
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 4
                }
            }
        }
    }
)

# Individual phase jobs
ingest_job = define_asset_job(
    name="ingest",
    description="Ingest data to pipeline branch",
    selection=AssetSelection.groups("ingestion"),
)

transform_job = define_asset_job(
    name="transform",
    description="Transform data on pipeline branch",
    selection=AssetSelection.groups("transform"),
)

validate_job = define_asset_job(
    name="validate",
    description="Run all validation gates",
    selection=AssetSelection.keys("validation_orchestrator"),
)

promote_job = define_asset_job(
    name="promote",
    description="Promote pipeline branch to main",
    selection=AssetSelection.keys("promote_to_main"),
)

cleanup_job = define_asset_job(
    name="cleanup_branches",
    description="Clean up old pipeline branches",
    selection=AssetSelection.keys("cleanup_old_branches"),
)
```

---

## 8. Docker Compose Updates

**File**: `docker-compose.yml`

**Remove**: `nessie-setup` service block (lines 104-118)

The nessie-setup service currently creates the dev branch at startup. This is no longer needed with dynamic branches.

---

## 9. DBT Profile Updates

**File**: `transforms/dbt/profiles/profiles.yml`

**Changes**:

- Add session property for Nessie branch
- Use NESSIE_REF environment variable

```yaml
cascade:
  target: dev
  outputs:
    dev:
      type: trino
      host: "{{ env_var('TRINO_HOST', 'trino') }}"
      port: "{{ env_var('TRINO_PORT', '10005') | int }}"
      user: dbt
      catalog: iceberg
      schema: bronze
      threads: 8
      session_properties:
        iceberg.nessie_reference_name: "{{ env_var('NESSIE_REF', 'main') }}"

    prod:
      type: trino
      host: "{{ env_var('TRINO_HOST', 'trino') }}"
      port: "{{ env_var('TRINO_PORT', '10005') | int }}"
      user: dbt
      catalog: iceberg
      schema: bronze
      threads: 8
      session_properties:
        iceberg.nessie_reference_name: "main"
```

---

## 10. Environment Configuration

**File**: `.env.example`

**Add**:

```bash
# Nessie Branch Management
BRANCH_RETENTION_DAYS=7
BRANCH_RETENTION_DAYS_FAILED=14
AUTO_PROMOTE_ENABLED=true

# Validation Gates
FRESHNESS_BLOCKS_PROMOTION=false
PANDERA_CRITICAL_LEVEL=error

# Validation Retry
VALIDATION_RETRY_ENABLED=true
VALIDATION_RETRY_MAX_ATTEMPTS=3
VALIDATION_RETRY_DELAY_SECONDS=300

# Freshness Thresholds
GLUCOSE_FRESHNESS_HOURS=24
GITHUB_EVENTS_FRESHNESS_HOURS=24
GITHUB_STATS_FRESHNESS_HOURS=48
```

**Remove**:

```bash
ICEBERG_NESSIE_REF=dev  # No longer needed
```

---

## 11. Testing

### 11.1 Unit Tests

**New test files**:

- `tests/test_branch_manager.py`
- `tests/test_validators.py`
- `tests/test_promotion_sensor.py`

### 11.2 Integration Tests

**Update**: `tests/test_phase9_workflows.sh`

**Changes**:

- Test dynamic branch creation
- Test validation gates
- Test automatic promotion
- Test branch cleanup

**Example additions**:

```bash
# Test 1: Dynamic branch creation
echo "Test 1: Create pipeline branch"
DAGSTER_RUN_ID=$(dagster job launch full_pipeline --config '{}' | grep -oP 'Run ID: \K[a-f0-9-]+')
BRANCH_NAME="pipeline/run-${DAGSTER_RUN_ID}"

# Verify branch was created
docker compose exec -T nessie curl -s http://localhost:19120/api/v1/trees/${BRANCH_NAME} | jq -e '.name'

# Test 2: Validation gates block bad data
echo "Test 2: Inject bad data and verify validation fails"
# ... inject bad data ...
# ... wait for validation_orchestrator ...
# ... verify all_passed=false ...

# Test 3: Automatic promotion on success
echo "Test 3: Verify automatic promotion"
# ... wait for auto_promotion_sensor to trigger ...
# ... verify promote_to_main materialized ...
# ... verify main branch updated ...

# Test 4: Branch cleanup
echo "Test 4: Verify branch cleanup scheduling"
# ... check promote_to_main metadata for cleanup_scheduled_for ...
```

---

## 12. Migration Checklist

### 12.1 Pre-Migration

- [ ] Backup current Nessie repository (main and dev branches)
- [ ] Document current pipeline state
- [ ] Verify no running pipelines

### 12.2 Code Changes

- [ ] Create all new files (9 files)
- [ ] Modify all existing files (15 files)
- [ ] Update .env configuration
- [ ] Update docker-compose.yml

### 12.3 Testing

- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Run full pipeline test with dynamic branch
- [ ] Verify validation gates work as expected
- [ ] Verify automatic promotion triggers
- [ ] Verify branch cleanup works

### 12.4 Deployment

- [ ] Stop all Dagster services
- [ ] Update code
- [ ] Update .env file
- [ ] Restart services (docker compose up -d)
- [ ] Verify services healthy
- [ ] Run test pipeline

### 12.5 Post-Deployment

- [ ] Monitor first few pipeline runs
- [ ] Verify promotions to main
- [ ] Verify branch cleanup
- [ ] Update documentation
- [ ] Archive old dev branch

---

## 13. Open Questions (Resolved)

1. **Freshness blocking**: Configurable via `FRESHNESS_BLOCKS_PROMOTION` ✓
2. **Branch naming**: Use `pipeline/run-{dagster_run_id}` ✓
3. **Cleanup scheduling**: Via sensor (hourly check) ✓
4. **Validation retry**: Yes, with logging via RetryPolicy ✓

---

## 14. Success Criteria

### Functional

- [ ] Dynamic branches created per pipeline run
- [ ] All validation gates execute and block promotion on failure
- [ ] Automatic promotion triggers after successful validation
- [ ] Branch cleanup executes after retention period
- [ ] Retry logic works for transient validation failures

### Non-Functional

- [ ] Pipeline execution time < 15 minutes (same as current)
- [ ] Validation adds < 5 minutes overhead
- [ ] No data loss during migration
- [ ] All tests pass
- [ ] Documentation updated

### Operational

- [ ] Clear logging of validation results
- [ ] Failed validations easily debuggable
- [ ] Branch cleanup doesn't impact performance
- [ ] Monitoring/alerting for failed promotions

---

## 15. Rollback Plan

If issues arise:

1. **Immediate rollback**:
   - Revert code changes (git revert)
   - Restore .env and docker-compose.yml
   - Restart services

2. **Data recovery**:
   - Main branch is never directly modified (safe)
   - Dynamic branches can be manually deleted
   - No data loss risk (Nessie provides time travel)

3. **Partial rollback**:
   - Disable auto-promotion: `AUTO_PROMOTE_ENABLED=false`
   - Use manual promotion workflow temporarily
   - Fix issues and re-enable

---

## 16. Future Enhancements

### Phase 2 (Post-MVP)

- Parallel pipeline runs (multiple branches simultaneously)
- Branch-based CI/CD integration
- Slack/email notifications for promotions/failures
- Grafana dashboards for validation metrics
- Cost optimization (automatic branch archival to cold storage)

### Phase 3 (Advanced)

- ML-based anomaly detection in validation
- Automatic rollback on production issues
- Blue/green deployment for transformations
- Feature flags for experimental transformations
