# IcebergSchemaMigrator (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/schema_migrator/IcebergSchemaMigrator)



SchemaMigrator implementation for Iceberg-backed tables.

Detects schema differences between a desired state and current table schema,
classifies changes by impact level, and applies migrations with optional
approval workflows.

Iceberg's native capabilities allow safe operations like column rename
and time-travel recovery for dropped columns.

Attributes [#attributes]

<PyAttribute name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="&#x22;field(default_factory=(lambda: get_settings().iceberg_default_ref))&#x22;">
  Nessie branch/tag reference for catalog operations.
  Defaults to settings value (typically `main`).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;supported_changes&#x22;" type="&#x22;(self) -> set[str]&#x22;">
  Return the set of change types supported by Iceberg.

  Iceberg's native schema evolution supports all common change types
  including safe renames, type widening, and nullability changes.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Check supported changes::

    migrator = IcebergSchemaMigrator()
    supported = migrator.supported\_changes()
    print(f"Can rename columns: \{'rename' in supported}")
  </Callout>

  <PySourceCode>
    ```python
    def supported_changes(self) -> set[str]:
        """Return the set of change types supported by Iceberg.

        Iceberg's native schema evolution supports all common change types
        including safe renames, type widening, and nullability changes.

        Returns:
            set[str]: Supported change type identifiers:
                - ``add``: Add new columns
                - ``drop``: Remove columns
                - ``rename``: Rename columns (native support)
                - ``widen_type``: Type promotion
                - ``narrow_type``: Type restriction
                - ``reorder``: Column reordering
                - ``nullability_relaxed``: Make nullable
                - ``nullability_tightened``: Make required

        Example:
            Check supported changes::

                migrator = IcebergSchemaMigrator()
                supported = migrator.supported_changes()
                print(f"Can rename columns: {'rename' in supported}")

        """
        return {
            "add",
            "drop",
            "rename",
            "widen_type",
            "narrow_type",
            "reorder",
            "nullability_relaxed",
            "nullability_tightened",
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;set&#x22;">
    set\[str]: Supported change type identifiers:

    * `add`: Add new columns
    * `drop`: Remove columns
    * `rename`: Rename columns (native support)
    * `widen_type`: Type promotion
    * `narrow_type`: Type restriction
    * `reorder`: Column reordering
    * `nullability_relaxed`: Make nullable
    * `nullability_tightened`: Make required
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;classify_change&#x22;" type="&#x22;(self, change_type, **details) -> str&#x22;">
  Classify a schema change by impact level.

  Iceberg-specific overrides:

  * `rename`: Always "safe" (native rename support)
  * `drop`: "warning" (data loss risk but recoverable via snapshots)
  * Other types: Delegate to default classifier

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Classify individual changes::

    migrator = IcebergSchemaMigrator()

    Safe operations [#safe-operations]

    assert migrator.classify\_change("rename") == "safe"

    Warning level [#warning-level]

    assert migrator.classify\_change("drop") == "warning"

    Breaking without default [#breaking-without-default]

    assert migrator.classify\_change("add", nullable=False, has\_default=False) == "breaking"
  </Callout>

  <PySourceCode>
    ```python
    def classify_change(self, change_type: str, **details: Any) -> str:
        """Classify a schema change by impact level.

        Iceberg-specific overrides:
        - ``rename``: Always "safe" (native rename support)
        - ``drop``: "warning" (data loss risk but recoverable via snapshots)
        - Other types: Delegate to default classifier

        Args:
            change_type: Type of change (e.g., ``add``, ``drop``, ``rename``).
            **details: Additional context for classification.

        Returns:
            str: Classification level:
                - ``safe``: No risk of data loss
                - ``warning``: Potential issues but recoverable
                - ``breaking``: Risk of data loss or errors

        Example:
            Classify individual changes::

                migrator = IcebergSchemaMigrator()

                # Safe operations
                assert migrator.classify_change("rename") == "safe"

                # Warning level
                assert migrator.classify_change("drop") == "warning"

                # Breaking without default
                assert migrator.classify_change("add", nullable=False, has_default=False) == "breaking"

        """
        if change_type == "rename":
            return "safe"
        if change_type == "drop":
            return "warning"
        return default_classify_change(change_type, **details)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;change_type&#x22;" type="&#x22;str&#x22;" value="undefined">
      Type of change (e.g., `add`, `drop`, `rename`).
    </PyParameter>

    <PyParameter name="&#x22;details&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Classification level:

    * `safe`: No risk of data loss
    * `warning`: Potential issues but recoverable
    * `breaking`: Risk of data loss or errors
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;diff_schema&#x22;" type="&#x22;(self, *, table_name, desired) -> SchemaMigrationPlan&#x22;">
  Compare desired schema against current table schema.

  Detects all differences between the desired schema and the current
  table schema, classifying each change by impact level.

  <Callout title="&#x22;Detected changes&#x22;" type="&#x22;detected-changes&#x22;">
    * Added columns (not in current schema)
    * Dropped columns (not in desired schema)
    * Type changes (widening or narrowing)
    * Nullability changes (relaxed or tightened)
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Detect schema drift::

    migrator = IcebergSchemaMigrator()

    Current table has columns: id (int), name (string) [#current-table-has-columns-id-int-name-string]

    Desired adds: email (string), changes id to int64 [#desired-adds-email-string-changes-id-to-int64]

    desired = NormalizedSchema(
    fields=\[
    NormalizedField(name="id", dtype="int64", nullable=False),
    NormalizedField(name="name", dtype="string", nullable=True),
    NormalizedField(name="email", dtype="string", nullable=True),
    ]
    )

    plan = migrator.diff\_schema(
    table\_name="raw\.users",
    desired=desired
    )

    print(f"Changes: \{len(plan.changes)}")
    for change in plan.changes:
    print(f"  \{change.field\_name}: \{change.change\_type} (\{change.classification})")

    if plan.requires\_approval:
    print("Requires approval before applying")
  </Callout>

  <PySourceCode>
    ```python
    def diff_schema(self, *, table_name: str, desired: NormalizedSchema) -> SchemaMigrationPlan:
        """Compare desired schema against current table schema.

        Detects all differences between the desired schema and the current
        table schema, classifying each change by impact level.

        Detected changes:
            - Added columns (not in current schema)
            - Dropped columns (not in desired schema)
            - Type changes (widening or narrowing)
            - Nullability changes (relaxed or tightened)

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            desired: Target schema definition as NormalizedSchema.

        Returns:
            SchemaMigrationPlan: Complete migration plan including:
                - List of SchemaChange objects with classifications
                - Overall classification (worst of all changes)
                - Recommendations for handling
                - Whether approval is required

        Example:
            Detect schema drift::

                migrator = IcebergSchemaMigrator()

                # Current table has columns: id (int), name (string)
                # Desired adds: email (string), changes id to int64
                desired = NormalizedSchema(
                    fields=[
                        NormalizedField(name="id", dtype="int64", nullable=False),
                        NormalizedField(name="name", dtype="string", nullable=True),
                        NormalizedField(name="email", dtype="string", nullable=True),
                    ]
                )

                plan = migrator.diff_schema(
                    table_name="raw.users",
                    desired=desired
                )

                print(f"Changes: {len(plan.changes)}")
                for change in plan.changes:
                    print(f"  {change.field_name}: {change.change_type} ({change.classification})")

                if plan.requires_approval:
                    print("Requires approval before applying")

        """
        catalog = get_catalog(ref=self.ref)
        table = catalog.load_table(table_name)
        current_schema = table.schema()

        current_fields: dict[str, tuple[str, bool]] = {}
        for f in current_schema.fields:
            if f.name in _SYSTEM_METADATA_FIELDS:
                continue
            current_fields[f.name] = (_iceberg_type_to_dtype(f.field_type), f.required is False)

        desired_fields: dict[str, tuple[str, bool]] = {}
        for f in desired.fields:
            desired_fields[f.name] = (f.dtype, f.nullable)

        changes: list[SchemaChange] = []

        # Added fields
        for name, (dtype, nullable) in desired_fields.items():
            if name not in current_fields:
                cls = self.classify_change("add", nullable=nullable, has_default=False)
                changes.append(
                    SchemaChange(
                        field_name=name,
                        change_type="add",
                        new_value=dtype,
                        classification=cls,
                    )
                )

        # Dropped fields
        for name in current_fields:
            if name not in desired_fields:
                cls = self.classify_change("drop")
                changes.append(
                    SchemaChange(
                        field_name=name,
                        change_type="drop",
                        old_value=current_fields[name][0],
                        classification=cls,
                    )
                )

        # Type and nullability changes on common fields
        for name in current_fields.keys() & desired_fields.keys():
            cur_dtype, cur_nullable = current_fields[name]
            des_dtype, des_nullable = desired_fields[name]

            if cur_dtype != des_dtype:
                if (cur_dtype, des_dtype) in _WIDEN_PAIRS:
                    change_type = "widen_type"
                else:
                    change_type = "narrow_type"
                cls = self.classify_change(change_type)
                changes.append(
                    SchemaChange(
                        field_name=name,
                        change_type=change_type,
                        old_value=cur_dtype,
                        new_value=des_dtype,
                        classification=cls,
                    )
                )

            if cur_nullable != des_nullable:
                if des_nullable and not cur_nullable:
                    change_type = "nullability_relaxed"
                else:
                    change_type = "nullability_tightened"
                cls = self.classify_change(change_type)
                changes.append(
                    SchemaChange(
                        field_name=name,
                        change_type=change_type,
                        old_value=str(cur_nullable),
                        new_value=str(des_nullable),
                        classification=cls,
                    )
                )

        classifications = [c.classification for c in changes]
        overall = worst_classification(classifications)
        requires_approval = overall == "breaking"

        recommendations: list[str] = []
        if requires_approval:
            recommendations.append("Breaking changes detected — requires explicit approval.")
        if any(c.change_type == "drop" for c in changes):
            recommendations.append("Dropped columns are recoverable via Iceberg snapshot rollback.")

        plan = SchemaMigrationPlan(
            table_name=table_name,
            changes=changes,
            classification=overall,
            recommendations=recommendations,
            requires_approval=requires_approval,
        )

        emitter = SchemaMigrationEventEmitter(
            SchemaMigrationEventContext(table_name=table_name, tags={"backend": "iceberg"})
        )
        emitter.emit(
            status="planned",
            classification=overall,
            change_count=len(changes),
            changes=[asdict(c) for c in changes],
        )

        return plan
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;desired&#x22;" type="&#x22;NormalizedSchema&#x22;" value="undefined">
      Target schema definition as NormalizedSchema.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.specs.SchemaMigrationPlan&#x22;">
    Complete migration plan including:

    * List of SchemaChange objects with classifications
    * Overall classification (worst of all changes)
    * Recommendations for handling
    * Whether approval is required
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;apply_plan&#x22;" type="&#x22;(self, *, plan, approved=False) -> dict[str, Any]&#x22;">
  Execute a migration plan against the Iceberg catalog.

  Applies all changes in the plan using Iceberg's schema update API.
  Breaking changes require explicit approval via the `approved` flag.

  <Callout title="&#x22;Supported operations&#x22;" type="&#x22;supported-operations&#x22;">
    * Add column: \`\`update.add\_column()\`\`\`
    * Drop column: \`\`update.delete\_column()\`\`\`
    * Rename column: \`\`update.rename\_column()\`\`\`
    * Type change: \`\`update.update\_column()\`\`\`
    * Nullability: `update.set_column_optional()` / `set_column_required()`
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Apply safe changes automatically::

    plan = migrator.diff\_schema(table\_name="raw\.users", desired=schema)

    if not plan.requires\_approval:
    result = migrator.apply\_plan(plan=plan)
    print(f"Applied \{result\['applied\_count']} changes")
    else:
    print("Manual approval required")

    Apply with approval::

    After reviewing the plan... [#after-reviewing-the-plan]

    result = migrator.apply\_plan(plan=plan, approved=True)
    print(f"Applied changes: \{result\['changes\_applied']}")
  </Callout>

  <PySourceCode>
    ````python
    def apply_plan(self, *, plan: SchemaMigrationPlan, approved: bool = False) -> dict[str, Any]:
        """Execute a migration plan against the Iceberg catalog.

        Applies all changes in the plan using Iceberg's schema update API.
        Breaking changes require explicit approval via the ``approved`` flag.

        Supported operations:
            - Add column: ``update.add_column()\```
            - Drop column: ``update.delete_column()\```
            - Rename column: ``update.rename_column()\```
            - Type change: ``update.update_column()\```
            - Nullability: ``update.set_column_optional()`` / ``set_column_required()``

        Args:
            plan: Migration plan from ``diff_schema()``.
            approved: Must be ``True`` to apply breaking changes.

        Returns:
            dict[str, Any]: Application results containing:
                - ``status``: "applied"
                - ``applied_count``: Number of changes applied
                - ``changes_applied``: List of change descriptions

        Raises:
            ValueError: If plan contains breaking changes and ``approved`` is False.
            Exception: Any Iceberg catalog errors during update.

        Example:
            Apply safe changes automatically::

                plan = migrator.diff_schema(table_name="raw.users", desired=schema)

                if not plan.requires_approval:
                    result = migrator.apply_plan(plan=plan)
                    print(f"Applied {result['applied_count']} changes")
                else:
                    print("Manual approval required")

            Apply with approval::

                # After reviewing the plan...
                result = migrator.apply_plan(plan=plan, approved=True)
                print(f"Applied changes: {result['changes_applied']}")

        """
        if plan.requires_approval and not approved:
            raise ValueError(
                f"Plan for {plan.table_name} contains breaking changes and requires approval."
            )

        catalog = get_catalog(ref=self.ref)
        table = catalog.load_table(plan.table_name)

        applied: list[str] = []
        applied_changes: list[SchemaChange] = []
        with table.update_schema() as update:
            for change in plan.changes:
                if change.change_type == "add":
                    iceberg_type = _dtype_to_iceberg_type(change.new_value or "string")
                    update.add_column(
                        path=change.field_name,
                        field_type=iceberg_type,
                    )
                    applied.append(f"add:{change.field_name}")
                    applied_changes.append(change)
                elif change.change_type == "drop":
                    update.delete_column(path=change.field_name)
                    applied.append(f"drop:{change.field_name}")
                    applied_changes.append(change)
                elif change.change_type == "rename":
                    update.rename_column(
                        path=change.old_value or change.field_name,
                        new_name=change.new_value or change.field_name,
                    )
                    applied.append(f"rename:{change.field_name}")
                    applied_changes.append(change)
                elif change.change_type in {"widen_type", "narrow_type"}:
                    iceberg_type = _dtype_to_iceberg_type(change.new_value or "string")
                    update.update_column(
                        path=change.field_name,
                        field_type=iceberg_type,
                    )
                    applied.append(f"{change.change_type}:{change.field_name}")
                    applied_changes.append(change)
                elif change.change_type == "nullability_relaxed":
                    update.set_column_optional(path=change.field_name)
                    applied.append(f"nullability_relaxed:{change.field_name}")
                    applied_changes.append(change)
                elif change.change_type == "nullability_tightened":
                    update.set_column_required(path=change.field_name)
                    applied.append(f"nullability_tightened:{change.field_name}")
                    applied_changes.append(change)

        logger.info(
            "iceberg_schema_migration_applied",
            table_name=plan.table_name,
            applied_count=len(applied),
            changes=applied,
        )

        emitter = SchemaMigrationEventEmitter(
            SchemaMigrationEventContext(table_name=plan.table_name, tags={"backend": "iceberg"})
        )
        emitter.emit(
            status="applied",
            classification=plan.classification,
            change_count=len(applied),
            changes=[asdict(c) for c in applied_changes],
        )

        return {
            "status": "applied",
            "applied_count": len(applied),
            "changes_applied": applied,
        }
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plan&#x22;" type="&#x22;SchemaMigrationPlan&#x22;" value="undefined">
      Migration plan from `diff_schema()`.
    </PyParameter>

    <PyParameter name="&#x22;approved&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
      Must be `True` to apply breaking changes.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Application results containing:

    * `status`: "applied"
    * `applied_count`: Number of changes applied
    * `changes_applied`: List of change descriptions
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_schema_history&#x22;" type="&#x22;(self, *, table_name, limit=10) -> list[dict[str, Any]]&#x22;">
  Return snapshot-level schema history for a table.

  Retrieves Iceberg snapshots which capture schema state at each
  table modification. Includes metadata about operation type,
  timestamp, and parent snapshot relationships.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Review table history::

    history = migrator.get\_schema\_history(
    table\_name="raw\.users",
    limit=5
    )

    for snapshot in history:
    ts = datetime.fromtimestamp(snapshot\['timestamp\_ms'] / 1000)
    print(f"\{ts}: \{snapshot\['summary']}")
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Schema history is derived from Iceberg snapshots, which
    capture the entire table state including schema at each
    commit point.
  </Callout>

  <PySourceCode>
    ```python
    def get_schema_history(self, *, table_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return snapshot-level schema history for a table.

        Retrieves Iceberg snapshots which capture schema state at each
        table modification. Includes metadata about operation type,
        timestamp, and parent snapshot relationships.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            limit: Maximum number of snapshots to return (default: 10).

        Returns:
            list[dict[str, Any]]: Snapshot history sorted by timestamp
                (newest first), each containing:
                - ``snapshot_id``: Unique snapshot identifier
                - ``timestamp_ms``: Unix timestamp in milliseconds
                - ``summary``: Operation summary dict
                - ``parent_id``: Parent snapshot ID (if any)

        Example:
            Review table history::

                history = migrator.get_schema_history(
                    table_name="raw.users",
                    limit=5
                )

                for snapshot in history:
                    ts = datetime.fromtimestamp(snapshot['timestamp_ms'] / 1000)
                    print(f"{ts}: {snapshot['summary']}")

        Note:
            Schema history is derived from Iceberg snapshots, which
            capture the entire table state including schema at each
            commit point.

        """
        catalog = get_catalog(ref=self.ref)
        table = catalog.load_table(table_name)

        snapshots = sorted(table.snapshots(), key=lambda s: s.timestamp_ms, reverse=True)
        results: list[dict[str, Any]] = []
        for snap in snapshots[:limit]:
            results.append(
                {
                    "snapshot_id": snap.snapshot_id,
                    "timestamp_ms": snap.timestamp_ms,
                    "summary": dict(snap.summary.additional_properties) if snap.summary else {},
                    "parent_id": snap.parent_snapshot_id,
                }
            )
        return results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (`namespace.table`).
    </PyParameter>

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;">
      Maximum number of snapshots to return (default: 10).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict\[str, Any]]: Snapshot history sorted by timestamp
    (newest first), each containing:

    * `snapshot_id`: Unique snapshot identifier
    * `timestamp_ms`: Unix timestamp in milliseconds
    * `summary`: Operation summary dict
    * `parent_id`: Parent snapshot ID (if any)
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, ref=(lambda: get_settings().iceberg_default_ref)()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="&#x22;(lambda: get_settings().iceberg_default_ref)()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
