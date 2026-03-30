# schema_migrate_contracts (/docs/python-reference/core/phlo/cli/commands/schema_migrate_contracts)



Helpers for schema-migration contract export and scaffold generation.

<PyAttribute name="&#x22;CONTRACT_VERSION&#x22;" type="null" value="&#x22;1&#x22;" />

<PyAttribute name="&#x22;MIGRATION_SCAFFOLD_VERSION&#x22;" type="null" value="&#x22;1&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;table_to_artifact_stem&#x22;" type="&#x22;(table_name) -> str&#x22;">
      Return a filesystem-safe artifact stem for a table name.

      <PySourceCode>
        ```python
        def table_to_artifact_stem(table_name: str) -> str:
            """Return a filesystem-safe artifact stem for a table name."""
            sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", table_name.strip())
            return sanitized.replace(".", "__")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;default_contract_path&#x22;" type="&#x22;(table_name) -> Path&#x22;">
      Return default contract path for a table.

      <PySourceCode>
        ```python
        def default_contract_path(table_name: str) -> Path:
            """Return default contract path for a table."""
            return Path(".phlo/contracts") / f"{table_to_artifact_stem(table_name)}.json"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;default_scaffold_yaml_path&#x22;" type="&#x22;(table_name) -> Path&#x22;">
      Return default scaffold YAML path for a table.

      <PySourceCode>
        ```python
        def default_scaffold_yaml_path(table_name: str) -> Path:
            """Return default scaffold YAML path for a table."""
            return Path(".phlo/migrations") / f"{table_to_artifact_stem(table_name)}.yaml"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;list_recent_contract_paths&#x22;" type="&#x22;(*, contracts_dir=Path('.phlo/contracts'), since_hours=24, limit=None) -> list[Path]&#x22;">
      List recently modified contract files in descending mtime order.

      <PySourceCode>
        ```python
        def list_recent_contract_paths(
            *,
            contracts_dir: Path = Path(".phlo/contracts"),
            since_hours: int = 24,
            limit: int | None = None,
        ) -> list[Path]:
            """List recently modified contract files in descending mtime order."""
            if since_hours < 0:
                raise ValueError("since_hours must be >= 0")
            if not contracts_dir.exists():
                return []

            cutoff = datetime.now(UTC) - timedelta(hours=since_hours)
            candidates: list[tuple[float, Path]] = []
            for path in contracts_dir.glob("*.json"):
                mtime = path.stat().st_mtime
                if datetime.fromtimestamp(mtime, tz=UTC) >= cutoff:
                    candidates.append((mtime, path))

            ordered = [path for _, path in sorted(candidates, key=lambda item: item[0], reverse=True)]
            if limit is not None:
                return ordered[:limit]
            return ordered
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;contracts_dir&#x22;" type="&#x22;Path&#x22;" value="&#x22;Path('.phlo/contracts')&#x22;" />

        <PyParameter name="&#x22;since_hours&#x22;" type="&#x22;int&#x22;" value="&#x22;24&#x22;" />

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;list[pathlib.Path]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;write_contract&#x22;" type="&#x22;(path, payload, force=False) -> None&#x22;">
      Write contract JSON atomically.

      <PySourceCode>
        ```python
        def write_contract(path: Path, payload: dict[str, Any], force: bool = False) -> None:
            """Write contract JSON atomically."""
            _write_json(path=path, payload=payload, force=force)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;read_contract&#x22;" type="&#x22;(path) -> dict[str, Any]&#x22;">
      Load a contract document from disk.

      <PySourceCode>
        ```python
        def read_contract(path: Path) -> dict[str, Any]:
            """Load a contract document from disk."""
            if not path.exists():
                raise FileNotFoundError(f"Contract file not found: {path}")
            raw = path.read_text(encoding="utf-8")
            loaded = json.loads(raw)
            if not isinstance(loaded, dict):
                raise ValueError(f"Contract root must be an object: {path}")
            return loaded
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;stable_operation_id&#x22;" type="&#x22;(*, table_name, field_name, change_type, old_value, new_value) -> str&#x22;">
      Build deterministic operation id for migration review and replay.

      <PySourceCode>
        ```python
        def stable_operation_id(
            *,
            table_name: str,
            field_name: str,
            change_type: str,
            old_value: str | None,
            new_value: str | None,
        ) -> str:
            """Build deterministic operation id for migration review and replay."""
            base = "|".join([table_name, field_name, change_type, old_value or "", new_value or ""]).encode(
                "utf-8"
            )
            return hashlib.sha1(base).hexdigest()[:12]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;field_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;change_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;old_value&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;new_value&#x22;" type="&#x22;str | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;build_scaffold_payload&#x22;" type="&#x22;(*, table_name, contract, migration_plan, generated_at) -> dict[str, Any]&#x22;">
      Build migration scaffold payload from a contract and live plan.

      <PySourceCode>
        ```python
        def build_scaffold_payload(
            *,
            table_name: str,
            contract: dict[str, Any],
            migration_plan: Any,
            generated_at: str,
        ) -> dict[str, Any]:
            """Build migration scaffold payload from a contract and live plan."""
            operations: list[dict[str, Any]] = []
            for change in migration_plan.changes:
                operations.append(
                    {
                        "operation_id": stable_operation_id(
                            table_name=table_name,
                            field_name=change.field_name,
                            change_type=change.change_type,
                            old_value=change.old_value,
                            new_value=change.new_value,
                        ),
                        "field_name": change.field_name,
                        "change_type": change.change_type,
                        "old_value": change.old_value,
                        "new_value": change.new_value,
                        "classification": change.classification,
                    }
                )

            return {
                "schema_migration_version": MIGRATION_SCAFFOLD_VERSION,
                "generated_at": generated_at,
                "table_name": table_name,
                "contract_version": contract.get("contract_version"),
                "classification": migration_plan.classification,
                "requires_approval": migration_plan.requires_approval,
                "recommendations": list(migration_plan.recommendations),
                "context": {
                    "table_store": contract.get("table_store"),
                    "schema_migrator": contract.get("schema_migrator"),
                    "quality_checks": contract.get("quality_checks", []),
                    "transform_refs": contract.get("transform_refs", []),
                },
                "operations": operations,
            }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;contract&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;migration_plan&#x22;" type="&#x22;Any&#x22;" value="null" />

        <PyParameter name="&#x22;generated_at&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;write_scaffold_yaml&#x22;" type="&#x22;(path, payload, force=False) -> None&#x22;">
      Write migration scaffold YAML atomically.

      <PySourceCode>
        ```python
        def write_scaffold_yaml(path: Path, payload: dict[str, Any], force: bool = False) -> None:
            """Write migration scaffold YAML atomically."""
            if path.exists() and not force:
                raise FileExistsError(f"Output already exists: {path} (use --force to overwrite)")
            path.parent.mkdir(parents=True, exist_ok=True)

            temp_path = path.with_suffix(f"{path.suffix}.tmp")
            temp_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            temp_path.replace(path)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_write_json&#x22;" type="&#x22;(path, payload, force) -> None&#x22;">
      <PySourceCode>
        ```python
        def _write_json(path: Path, payload: dict[str, Any], force: bool) -> None:
            if path.exists() and not force:
                raise FileExistsError(f"Output already exists: {path} (use --force to overwrite)")
            path.parent.mkdir(parents=True, exist_ok=True)

            temp_path = path.with_suffix(f"{path.suffix}.tmp")
            temp_path.write_text(f"{json.dumps(payload, indent=2, sort_keys=False)}\n", encoding="utf-8")
            temp_path.replace(path)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
