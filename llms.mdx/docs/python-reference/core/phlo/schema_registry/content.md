# schema_registry (/docs/python-reference/core/phlo/schema_registry)



Schema registry for tracking schema evolution and detecting breaking changes.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SchemaSnapshot&#x22;" href="&#x22;/docs/python-reference/core/phlo/schema_registry/SchemaSnapshot&#x22;" />

      <Card title="&#x22;SchemaRegistry&#x22;" href="&#x22;/docs/python-reference/core/phlo/schema_registry/SchemaRegistry&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_registry_db_url&#x22;" type="&#x22;() -> str | None&#x22;">
      Resolve the registry database URL from environment variables.

      <PySourceCode>
        ```python
        def resolve_registry_db_url() -> str | None:
            """Resolve the registry database URL from environment variables."""
            for key in _REGISTRY_DB_KEYS:
                value = os.environ.get(key)
                if value:
                    return value
            return None
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_canonical_schema_json&#x22;" type="&#x22;(schema) -> str&#x22;">
      Serialize a NormalizedSchema to canonical JSON (sorted keys, stable for hashing).

      <PySourceCode>
        ```python
        def _canonical_schema_json(schema: NormalizedSchema) -> str:
            """Serialize a NormalizedSchema to canonical JSON (sorted keys, stable for hashing)."""
            data = {
                "fields": [
                    {
                        "name": f.name,
                        "dtype": f.dtype,
                        "nullable": f.nullable,
                        "default": f.default,
                    }
                    for f in sorted(schema.fields, key=lambda f: f.name)
                ]
            }
            return json.dumps(data, sort_keys=True, separators=(",", ":"))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema&#x22;" type="&#x22;NormalizedSchema&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_schema_hash&#x22;" type="&#x22;(canonical_json) -> str&#x22;">
      Return a truncated SHA-256 hash of canonical schema JSON.

      <PySourceCode>
        ```python
        def _schema_hash(canonical_json: str) -> str:
            """Return a truncated SHA-256 hash of canonical schema JSON."""
            return hashlib.sha256(canonical_json.encode()).hexdigest()[:16]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;canonical_json&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check_compatibility&#x22;" type="&#x22;(previous, current, table_name='unknown') -> SchemaMigrationPlan&#x22;">
      Compare two schemas and classify changes.

      Breaking: column drops, type narrowings, nullability tightening
      Safe: adds, widenings, nullability relaxed

      <PySourceCode>
        ```python
        def check_compatibility(
            previous: NormalizedSchema,
            current: NormalizedSchema,
            table_name: str = "unknown",
        ) -> SchemaMigrationPlan:
            """Compare two schemas and classify changes.

            Breaking: column drops, type narrowings, nullability tightening
            Safe: adds, widenings, nullability relaxed
            """
            prev_fields = {f.name: f for f in previous.fields}
            curr_fields = {f.name: f for f in current.fields}
            changes: list[SchemaChange] = []

            for name in prev_fields:
                if name not in curr_fields:
                    changes.append(
                        SchemaChange(
                            field_name=name,
                            change_type="drop",
                            old_value=prev_fields[name].dtype,
                            classification=default_classify_change("drop"),
                        )
                    )

            for name in curr_fields:
                if name not in prev_fields:
                    f = curr_fields[name]
                    classification = default_classify_change(
                        "add", nullable=f.nullable, has_default=f.default is not None
                    )
                    changes.append(
                        SchemaChange(
                            field_name=name,
                            change_type="add",
                            new_value=f.dtype,
                            classification=classification,
                        )
                    )

            for name in prev_fields:
                if name not in curr_fields:
                    continue
                prev_f = prev_fields[name]
                curr_f = curr_fields[name]

                if prev_f.dtype != curr_f.dtype:
                    if (prev_f.dtype, curr_f.dtype) in _WIDEN_PAIRS:
                        change_type = "widen_type"
                    else:
                        change_type = "narrow_type"
                    changes.append(
                        SchemaChange(
                            field_name=name,
                            change_type=change_type,
                            old_value=prev_f.dtype,
                            new_value=curr_f.dtype,
                            classification=default_classify_change(change_type),
                        )
                    )

                if prev_f.nullable != curr_f.nullable:
                    if prev_f.nullable and not curr_f.nullable:
                        null_change_type = "nullability_tightened"
                    else:
                        null_change_type = "nullability_relaxed"
                    changes.append(
                        SchemaChange(
                            field_name=name,
                            change_type=null_change_type,
                            old_value=str(prev_f.nullable),
                            new_value=str(curr_f.nullable),
                            classification=default_classify_change(null_change_type),
                        )
                    )

            classifications = [c.classification for c in changes]
            overall = worst_classification(classifications)

            return SchemaMigrationPlan(
                table_name=table_name,
                changes=changes,
                classification=overall,
                requires_approval=overall == "breaking",
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;previous&#x22;" type="&#x22;NormalizedSchema&#x22;" value="null" />

        <PyParameter name="&#x22;current&#x22;" type="&#x22;NormalizedSchema&#x22;" value="null" />

        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'unknown'&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.specs.SchemaMigrationPlan&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;deserialize_schema&#x22;" type="&#x22;(schema_json) -> NormalizedSchema&#x22;">
      Deserialize a canonical schema JSON string back to NormalizedSchema.

      <PySourceCode>
        ```python
        def deserialize_schema(schema_json: str) -> NormalizedSchema:
            """Deserialize a canonical schema JSON string back to NormalizedSchema."""
            data = json.loads(schema_json)
            fields = [
                FieldSpec(
                    name=f["name"],
                    dtype=f["dtype"],
                    nullable=f["nullable"],
                    default=f.get("default"),
                )
                for f in data["fields"]
            ]
            return NormalizedSchema(fields=fields)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;schema_json&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.specs.NormalizedSchema&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
