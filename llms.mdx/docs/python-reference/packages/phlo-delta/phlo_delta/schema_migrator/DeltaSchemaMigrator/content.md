# DeltaSchemaMigrator (/docs/python-reference/packages/phlo-delta/phlo_delta/schema_migrator/DeltaSchemaMigrator)



SchemaMigrator backed by Delta Lake tables.

This class implements the SchemaMigrator protocol for Delta Lake,
providing schema comparison, migration planning, and change application.
It supports various schema change types including field addition, removal,
renaming, type changes, and nullability adjustments.

Functions [#functions]

<PyFunction name="&#x22;supported_changes&#x22;" type="&#x22;(self) -> set[str]&#x22;">
  Return the set of change types supported natively by Delta Lake.

  Delta Lake supports various schema evolution operations including
  field addition, removal, renaming, type widening/narrowing, and
  nullability changes.

  <PySourceCode>
    ```python
    def supported_changes(self) -> set[str]:
        """Return the set of change types supported natively by Delta Lake.

        Delta Lake supports various schema evolution operations including
        field addition, removal, renaming, type widening/narrowing, and
        nullability changes.

        Returns:
            set[str]: Set of supported change type strings:
                - "add": Add new columns
                - "drop": Remove existing columns
                - "rename": Rename columns
                - "widen_type": Expand type (e.g., int32 -> int64)
                - "narrow_type": Restrict type (e.g., int64 -> int32)
                - "nullability_relaxed": Allow nulls where not allowed before
                - "nullability_tightened": Require non-null where nulls were allowed

        """
        return {
            "add",
            "drop",
            "rename",
            "widen_type",
            "narrow_type",
            "nullability_relaxed",
            "nullability_tightened",
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;set&#x22;">
    set\[str]: Set of supported change type strings:

    * "add": Add new columns
    * "drop": Remove existing columns
    * "rename": Rename columns
    * "widen\_type": Expand type (e.g., int32 -> int64)
    * "narrow\_type": Restrict type (e.g., int64 -> int32)
    * "nullability\_relaxed": Allow nulls where not allowed before
    * "nullability\_tightened": Require non-null where nulls were allowed
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;classify_change&#x22;" type="&#x22;(self, change_type, **details) -> str&#x22;">
  Classify a change with Delta-specific overrides.

  Delta supports rename (safe) and drop (warning, recoverable via
  time travel). All other change types fall through to the default
  classifier.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    cls = migrator.classify\_change("rename")

    Returns: "safe" [#returns-safe]
  </Callout>

  <PySourceCode>
    ```python
    def classify_change(self, change_type: str, **details: Any) -> str:
        """Classify a change with Delta-specific overrides.

        Delta supports rename (safe) and drop (warning, recoverable via
        time travel). All other change types fall through to the default
        classifier.

        Args:
            change_type: Type of schema change being classified.
            **details: Additional details about the change for classification.

        Returns:
            str: Classification result ("safe", "warning", or "breaking").

        Example:
            cls = migrator.classify_change("rename")
            # Returns: "safe"

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
      Type of schema change being classified.
    </PyParameter>

    <PyParameter name="&#x22;details&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Classification result ("safe", "warning", or "breaking").
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;diff_schema&#x22;" type="&#x22;(self, *, table_name, desired) -> SchemaMigrationPlan&#x22;">
  Compare *desired* schema against current Delta table schema.

  Analyzes differences between the desired schema and the existing
  table schema, generating a migration plan with all detected changes.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    from phlo.capabilities.specs import NormalizedSchema, NormalizedField

    desired = NormalizedSchema(fields=\[
    NormalizedField(name="id", dtype="string", nullable=False),
    ])
    plan = migrator.diff\_schema(table\_name="raw\.events", desired=desired)
  </Callout>

  <PySourceCode>
    ```python
    def diff_schema(self, *, table_name: str, desired: NormalizedSchema) -> SchemaMigrationPlan:
        """Compare *desired* schema against current Delta table schema.

        Analyzes differences between the desired schema and the existing
        table schema, generating a migration plan with all detected changes.

        Args:
            table_name: Fully qualified table name (namespace.table).
            desired: Target NormalizedSchema to compare against.

        Returns:
            SchemaMigrationPlan: Plan describing every detected change,
                including classifications and recommendations.

        Raises:
            Exception: If the table cannot be accessed or read.

        Example:
            from phlo.capabilities.specs import NormalizedSchema, NormalizedField

            desired = NormalizedSchema(fields=[
                NormalizedField(name="id", dtype="string", nullable=False),
            ])
            plan = migrator.diff_schema(table_name="raw.events", desired=desired)

        """
        from deltalake import DeltaTable

        table_uri = _resolve_table_uri(table_name)
        opts = _default_storage_options()

        dt = DeltaTable(table_uri, storage_options=opts)
        current_schema = cast(Any, dt.schema()).to_pyarrow()

        current_fields: dict[str, tuple[str, bool]] = {}
        for field in current_schema:
            current_fields[field.name] = (_arrow_type_to_dtype(field.type), field.nullable)

        desired_fields: dict[str, tuple[str, bool]] = {}
        for f in desired.fields:
            desired_fields[f.name] = (f.dtype, f.nullable)

        changes: list[SchemaChange] = []

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
            recommendations.append("Dropped columns are recoverable via Delta Lake time travel.")

        plan = SchemaMigrationPlan(
            table_name=table_name,
            changes=changes,
            classification=overall,
            recommendations=recommendations,
            requires_approval=requires_approval,
        )

        emitter = SchemaMigrationEventEmitter(
            SchemaMigrationEventContext(table_name=table_name, tags={"backend": "delta"})
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
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;desired&#x22;" type="&#x22;NormalizedSchema&#x22;" value="undefined">
      Target NormalizedSchema to compare against.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.specs.SchemaMigrationPlan&#x22;">
    Plan describing every detected change,
    including classifications and recommendations.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;apply_plan&#x22;" type="&#x22;(self, *, plan, approved=False) -> dict[str, Any]&#x22;">
  Execute a migration plan against a Delta table.

  Applies all changes in the migration plan to the target table.
  Breaking changes require explicit approval.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    plan = migrator.diff\_schema(table\_name="raw\.events", desired=schema)
    if not plan.requires\_approval:
    result = migrator.apply\_plan(plan=plan, approved=True)
    print(f"Applied \{result\['applied\_count']} changes")
  </Callout>

  <PySourceCode>
    ```python
    def apply_plan(self, *, plan: SchemaMigrationPlan, approved: bool = False) -> dict[str, Any]:
        """Execute a migration plan against a Delta table.

        Applies all changes in the migration plan to the target table.
        Breaking changes require explicit approval.

        Args:
            plan: SchemaMigrationPlan containing changes to apply.
            approved: Whether breaking changes have been explicitly approved.

        Returns:
            dict[str, Any]: Migration results including status, applied count,
                and list of applied changes.

        Raises:
            ValueError: If the plan contains breaking changes and
                ``approved`` is not ``True``.
            Exception: If any schema change operation fails.

        Example:
            plan = migrator.diff_schema(table_name="raw.events", desired=schema)
            if not plan.requires_approval:
                result = migrator.apply_plan(plan=plan, approved=True)
                print(f"Applied {result['applied_count']} changes")

        """
        if plan.requires_approval and not approved:
            raise ValueError(
                f"Plan for {plan.table_name} contains breaking changes and requires approval."
            )

        from deltalake import DeltaTable

        table_uri = _resolve_table_uri(plan.table_name)
        opts = _default_storage_options()

        dt = DeltaTable(table_uri, storage_options=opts)
        current_schema = cast(Any, dt.schema()).to_pyarrow()

        new_fields: list[pa.Field] = list(current_schema)
        applied: list[str] = []

        applied_changes: list[SchemaChange] = []
        for change in plan.changes:
            if change.change_type == "add":
                arrow_type = _dtype_to_arrow_type(change.new_value or "string")
                new_fields.append(pa.field(change.field_name, arrow_type, nullable=True))
                applied.append(f"add:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type == "drop":
                new_fields = [f for f in new_fields if f.name != change.field_name]
                applied.append(f"drop:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type == "rename":
                old_name = change.old_value or change.field_name
                new_name = change.new_value or change.field_name
                new_fields = [
                    pa.field(new_name, f.type, nullable=f.nullable) if f.name == old_name else f
                    for f in new_fields
                ]
                applied.append(f"rename:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type in {"widen_type", "narrow_type"}:
                arrow_type = _dtype_to_arrow_type(change.new_value or "string")
                new_fields = [
                    pa.field(f.name, arrow_type, nullable=f.nullable)
                    if f.name == change.field_name
                    else f
                    for f in new_fields
                ]
                applied.append(f"{change.change_type}:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type == "nullability_relaxed":
                new_fields = [
                    pa.field(f.name, f.type, nullable=True) if f.name == change.field_name else f
                    for f in new_fields
                ]
                applied.append(f"nullability_relaxed:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type == "nullability_tightened":
                new_fields = [
                    pa.field(f.name, f.type, nullable=False) if f.name == change.field_name else f
                    for f in new_fields
                ]
                applied.append(f"nullability_tightened:{change.field_name}")
                applied_changes.append(change)

        new_schema = pa.schema(new_fields)

        empty = pa.table(
            {field.name: pa.array([], type=field.type) for field in new_schema},
            schema=new_schema,
        )

        from deltalake import write_deltalake

        write_deltalake(
            table_uri,
            empty,
            mode="overwrite",
            schema_mode="overwrite",
            storage_options=opts,
        )

        logger.info(
            "delta_schema_migration_applied",
            table_name=plan.table_name,
            applied_count=len(applied),
            changes=applied,
        )

        emitter = SchemaMigrationEventEmitter(
            SchemaMigrationEventContext(table_name=plan.table_name, tags={"backend": "delta"})
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plan&#x22;" type="&#x22;SchemaMigrationPlan&#x22;" value="undefined">
      SchemaMigrationPlan containing changes to apply.
    </PyParameter>

    <PyParameter name="&#x22;approved&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
      Whether breaking changes have been explicitly approved.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Migration results including status, applied count,
    and list of applied changes.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_schema_history&#x22;" type="&#x22;(self, *, table_name, limit=10) -> list[dict[str, Any]]&#x22;">
  Return version-level history for *table\_name*.

  Retrieves the schema change history by listing table versions.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    history = migrator.get\_schema\_history(table\_name="raw\.events", limit=5)
    for entry in history:
    print(f"Version \{entry\['version']}: \{entry\['operation']}")
  </Callout>

  <PySourceCode>
    ```python
    def get_schema_history(self, *, table_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return version-level history for *table_name*.

        Retrieves the schema change history by listing table versions.

        Args:
            table_name: Fully qualified table name (namespace.table).
            limit: Maximum number of historical versions to retrieve (default: 10).

        Returns:
            list[dict[str, Any]]: List of version history dictionaries,
                each containing version, timestamp, operation, and parameters.

        Example:
            history = migrator.get_schema_history(table_name="raw.events", limit=5)
            for entry in history:
                print(f"Version {entry['version']}: {entry['operation']}")

        """
        from phlo_delta.tables import list_table_versions

        return list_table_versions(table_name=table_name, limit=limit)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name (namespace.table).
    </PyParameter>

    <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="&#x22;10&#x22;">
      Maximum number of historical versions to retrieve (default: 10).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[dict\[str, Any]]: List of version history dictionaries,
    each containing version, timestamp, operation, and parameters.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
