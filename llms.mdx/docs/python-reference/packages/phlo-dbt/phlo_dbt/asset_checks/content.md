# asset_checks (/docs/python-reference/packages/phlo-dbt/phlo_dbt/asset_checks)



dbt test result extraction and conversion to Phlo check results.

This module provides utilities for extracting dbt test results from run results
and converting them into Phlo's CheckResult format. It handles test type detection,
severity mapping, and metadata extraction for quality checks.

Example:

> > > from phlo\_dbt.asset\_checks import extract\_dbt\_asset\_checks
> > > from phlo\_dbt.translator import DbtSpecTranslator
> > > checks = extract\_dbt\_asset\_checks(
> > > ...     run\_results=run\_results\_data,
> > > ...     manifest=manifest\_data,
> > > ...     translator=DbtSpecTranslator(),
> > > ...     partition\_key="2024-01-01"
> > > ... )
> > > for check in checks:
> > > ...     print(f"\{check.check\_name}: \{'PASS' if check.passed else 'FAIL'}")

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;_CheckContract&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/asset_checks/_CheckContract&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_sanitize_name&#x22;" type="&#x22;(value) -> str&#x22;">
      Normalize a string into a Dagster-safe identifier segment.

      <PySourceCode>
        ```python
        def _sanitize_name(value: str) -> str:
            """Normalize a string into a Dagster-safe identifier segment."""
            cleaned = "".join(char if char.isalnum() else "_" for char in value.strip())
            cleaned = "_".join(part for part in cleaned.split("_") if part)
            return cleaned or "unknown"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_dbt_check_name&#x22;" type="&#x22;(test_type, target) -> str&#x22;">
      Build canonical check name for a dbt test.

      <PySourceCode>
        ```python
        def _dbt_check_name(test_type: str, target: str) -> str:
            """Build canonical check name for a dbt test."""
            return f"dbt__{_sanitize_name(test_type)}__{_sanitize_name(target)}"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_severity_for_dbt_test&#x22;" type="&#x22;(*, test_type, tags) -> str&#x22;">
      Map dbt test metadata to severity.

      <PySourceCode>
        ```python
        def _severity_for_dbt_test(*, test_type: str | None, tags: Iterable[str] | None) -> str:
            """Map dbt test metadata to severity."""
            warn_tags = {"warn", "anomaly"}
            blocking_tags = {"blocking"}
            blocking_test_types = {"not_null", "unique", "relationships"}
            normalized_tags = {tag.strip().lower() for tag in (tags or []) if tag and tag.strip()}
            normalized_test_type = (test_type or "").strip().lower()
            if normalized_tags & blocking_tags:
                return "error"
            if normalized_tags & warn_tags:
                return "warn"
            if normalized_test_type in blocking_test_types:
                return "error"
            return "warn"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_type&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;tags&#x22;" type="&#x22;Iterable[str] | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;extract_dbt_asset_checks&#x22;" type="&#x22;(run_results, manifest, *, translator, partition_key, max_sql_chars=100000) -> list[CheckResult]&#x22;">
      Convert dbt run results into Phlo check results.

      Extracts test results from dbt run\_results.json and manifest.json files,
      converting them into Phlo CheckResult objects. Handles various test types,
      severity mapping, and SQL extraction for quality reporting.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > import json
        > > > from pathlib import Path
        > > > from phlo\_dbt.translator import DbtSpecTranslator
        > > >
        > > > run\_results = json.loads(Path("target/run\_results.json").read\_text())
        > > > manifest = json.loads(Path("target/manifest.json").read\_text())
        > > >
        > > > checks = extract\_dbt\_asset\_checks(
        > > > ...     run\_results=run\_results,
        > > > ...     manifest=manifest,
        > > > ...     translator=DbtSpecTranslator(),
        > > > ...     partition\_key="2024-01-01"
        > > > ... )
        > > >
        > > > passed = sum(1 for c in checks if c.passed)
        > > > failed = len(checks) - passed
        > > > print(f"Tests: \{passed} passed, \{failed} failed")
      </Callout>

      <PySourceCode>
        ```python
        def extract_dbt_asset_checks(
            run_results: Mapping[str, Any],
            manifest: Mapping[str, Any],
            *,
            translator: DbtSpecTranslator,
            partition_key: str | None,
            max_sql_chars: int = 100_000,
        ) -> list[CheckResult]:
            """Convert dbt run results into Phlo check results.

            Extracts test results from dbt run_results.json and manifest.json files,
            converting them into Phlo CheckResult objects. Handles various test types,
            severity mapping, and SQL extraction for quality reporting.

            Args:
                run_results: Parsed dbt run results payload from run_results.json.
                manifest: Parsed dbt manifest payload from manifest.json.
                translator: Translator used to resolve target asset keys from dbt nodes.
                partition_key: Optional partition key for emitted checks (e.g., "2024-01-01").
                max_sql_chars: Maximum SQL length to include in metadata (default: 100,000).

            Returns:
                List of CheckResult objects derived from dbt test nodes.

            Raises:
                Exception: May raise exceptions during asset key translation (logged, not propagated).

            Example:
                >>> import json
                >>> from pathlib import Path
                >>> from phlo_dbt.translator import DbtSpecTranslator
                >>>
                >>> run_results = json.loads(Path("target/run_results.json").read_text())
                >>> manifest = json.loads(Path("target/manifest.json").read_text())
                >>>
                >>> checks = extract_dbt_asset_checks(
                ...     run_results=run_results,
                ...     manifest=manifest,
                ...     translator=DbtSpecTranslator(),
                ...     partition_key="2024-01-01"
                ... )
                >>>
                >>> passed = sum(1 for c in checks if c.passed)
                >>> failed = len(checks) - passed
                >>> print(f"Tests: {passed} passed, {failed} failed")

            """
            nodes = manifest.get("nodes") or {}
            checks: list[CheckResult] = []
            result_entries = run_results.get("results", []) or []
            logger.info(
                "dbt_asset_checks_extraction_started",
                result_count=len(result_entries) if isinstance(result_entries, list) else 0,
                partition_key=partition_key,
            )

            for result in result_entries:
                unique_id = result.get("unique_id")
                if not isinstance(unique_id, str) or not unique_id.startswith("test."):
                    continue

                status = (result.get("status") or "").strip().lower()
                passed = status in {"pass", "skipped", "skip"}

                depends_on = result.get("depends_on") or {}
                depends_nodes = depends_on.get("nodes") or []
                target_unique_id = _first_str(depends_nodes, prefix="model.")
                if target_unique_id is None:
                    target_unique_id = _first_str(depends_nodes)
                if target_unique_id is None:
                    continue

                target_props = nodes.get(target_unique_id)
                if not isinstance(target_props, Mapping):
                    continue

                try:
                    asset_key_str = translator.get_asset_key(target_props)
                except Exception:
                    logger.exception(
                        "dbt_asset_checks_target_translate_failed",
                        test_unique_id=unique_id,
                        target_unique_id=target_unique_id,
                    )
                    continue

                test_props = nodes.get(unique_id, {})
                test_type = _dbt_test_type(test_props, fallback_unique_id=unique_id)
                target_name = str(
                    target_props.get("name") or target_props.get("alias") or target_unique_id.split(".")[-1]
                )
                check_name = _dbt_check_name(test_type, target_name)

                tags = _dbt_tags(test_props)
                failures = _int_or_none(result.get("failures"))
                failed_count = 0 if passed else (failures if failures is not None else 1)

                severity: str | None
                if passed:
                    severity = None
                elif status == "fail":
                    severity_label = _severity_for_dbt_test(test_type=test_type, tags=tags)
                    severity = severity_label or "error"
                else:
                    severity = "error"

                compiled_sql = _dbt_compiled_sql(test_props)
                compiled_sql = _truncate(compiled_sql, max_chars=max_sql_chars)

                contract = _CheckContract(
                    source="dbt",
                    partition_key=partition_key,
                    failed_count=failed_count,
                    total_count=None,
                    query_or_sql=compiled_sql,
                    repro_sql=_repro_sql_from_sql(compiled_sql),
                    sample=_sample_for_result(result, passed=passed),
                )

                metadata: dict[str, Any] = {
                    **contract.to_metadata(),
                    "status": status or "unknown",
                    "test_unique_id": unique_id,
                    "test_type": test_type,
                    "target_unique_id": target_unique_id,
                    "target_name": target_name,
                }
                if tags:
                    metadata["tags"] = sorted(tags)
                if failures is not None:
                    metadata["failed_rows"] = failures

                checks.append(
                    CheckResult(
                        asset_key=asset_key_str,
                        check_name=check_name,
                        passed=passed,
                        severity=severity,
                        metadata=metadata,
                    )
                )

            logger.info(
                "dbt_asset_checks_extraction_finished",
                check_count=len(checks),
                partition_key=partition_key,
            )
            return checks
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;run_results&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          Parsed dbt run results payload from run\_results.json.
        </PyParameter>

        <PyParameter name="&#x22;manifest&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          Parsed dbt manifest payload from manifest.json.
        </PyParameter>

        <PyParameter name="&#x22;translator&#x22;" type="&#x22;DbtSpecTranslator&#x22;" value="undefined">
          Translator used to resolve target asset keys from dbt nodes.
        </PyParameter>

        <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional partition key for emitted checks (e.g., "2024-01-01").
        </PyParameter>

        <PyParameter name="&#x22;max_sql_chars&#x22;" type="&#x22;int&#x22;" value="&#x22;100000&#x22;">
          Maximum SQL length to include in metadata (default: 100,000).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of CheckResult objects derived from dbt test nodes.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_first_str&#x22;" type="&#x22;(values, prefix=None) -> str | None&#x22;">
      Return the first string entry, optionally filtered by prefix.

      <PySourceCode>
        ```python
        def _first_str(values: Iterable[object], prefix: str | None = None) -> str | None:
            """Return the first string entry, optionally filtered by prefix.

            Args:
                values: Candidate values to inspect.
                prefix: Optional required string prefix.

            Returns:
                First matching string, or ``None``.

            """
            for value in values:
                if not isinstance(value, str):
                    continue
                if prefix is not None and not value.startswith(prefix):
                    continue
                return value
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;values&#x22;" type="&#x22;Iterable[object]&#x22;" value="undefined">
          Candidate values to inspect.
        </PyParameter>

        <PyParameter name="&#x22;prefix&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional required string prefix.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        First matching string, or `None`.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_dbt_test_type&#x22;" type="&#x22;(test_props, *, fallback_unique_id) -> str&#x22;">
      Infer the dbt test type label from node properties.

      <PySourceCode>
        ```python
        def _dbt_test_type(test_props: Mapping[str, Any], *, fallback_unique_id: str) -> str:
            """Infer the dbt test type label from node properties.

            Args:
                test_props: dbt test node properties.
                fallback_unique_id: Unique id used as a fallback source.

            Returns:
                Normalized dbt test type string.

            """
            test_metadata = test_props.get("test_metadata")
            if isinstance(test_metadata, Mapping):
                name = test_metadata.get("name")
                if isinstance(name, str) and name.strip():
                    return name.strip()
            resource_type = test_props.get("resource_type")
            if isinstance(resource_type, str) and resource_type.strip():
                return resource_type.strip()
            return fallback_unique_id.split(".")[-1]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          dbt test node properties.
        </PyParameter>

        <PyParameter name="&#x22;fallback_unique_id&#x22;" type="&#x22;str&#x22;" value="undefined">
          Unique id used as a fallback source.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Normalized dbt test type string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_dbt_tags&#x22;" type="&#x22;(test_props) -> set[str]&#x22;">
      Extract normalized non-empty dbt tags.

      <PySourceCode>
        ```python
        def _dbt_tags(test_props: Mapping[str, Any]) -> set[str]:
            """Extract normalized non-empty dbt tags.

            Args:
                test_props: dbt test node properties.

            Returns:
                Unique trimmed tag values.

            """
            tags = test_props.get("tags")
            if not isinstance(tags, list):
                return set()
            normalized: set[str] = set()
            for tag in tags:
                if isinstance(tag, str) and tag.strip():
                    normalized.add(tag.strip())
            return normalized
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          dbt test node properties.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;set&#x22;">
        Unique trimmed tag values.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_dbt_compiled_sql&#x22;" type="&#x22;(test_props) -> str | None&#x22;">
      Return compiled SQL text from known dbt node keys.

      <PySourceCode>
        ```python
        def _dbt_compiled_sql(test_props: Mapping[str, Any]) -> str | None:
            """Return compiled SQL text from known dbt node keys.

            Args:
                test_props: dbt test node properties.

            Returns:
                Compiled SQL text when available, otherwise ``None``.

            """
            for key in ("compiled_code", "compiled_sql", "raw_code"):
                value = test_props.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_props&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          dbt test node properties.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        Compiled SQL text when available, otherwise `None`.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_sample_for_result&#x22;" type="&#x22;(result, *, passed) -> list[dict[str, Any]]&#x22;">
      Build sample metadata for failed dbt tests.

      <PySourceCode>
        ```python
        def _sample_for_result(result: Mapping[str, Any], *, passed: bool) -> list[dict[str, Any]]:
            """Build sample metadata for failed dbt tests.

            Args:
                result: dbt result entry.
                passed: Whether the test passed.

            Returns:
                Sample metadata rows for quality diagnostics.

            """
            if passed:
                return []
            sample: dict[str, Any] = {}
            message = result.get("message")
            if isinstance(message, str) and message.strip():
                sample["message"] = message
            failures = _int_or_none(result.get("failures"))
            if failures is not None:
                sample["failed_rows"] = failures
            return [sample] if sample else []
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;result&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          dbt result entry.
        </PyParameter>

        <PyParameter name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether the test passed.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Sample metadata rows for quality diagnostics.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_truncate&#x22;" type="&#x22;(value, *, max_chars) -> str | None&#x22;">
      Trim long strings to a bounded size.

      <PySourceCode>
        ```python
        def _truncate(value: str | None, *, max_chars: int) -> str | None:
            """Trim long strings to a bounded size.

            Args:
                value: Candidate value to truncate.
                max_chars: Maximum output length.

            Returns:
                Original value when short enough; truncated value otherwise.

            """
            if value is None:
                return None
            if len(value) <= max_chars:
                return value
            return value[: max_chars - 20] + "\n-- [truncated]"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Candidate value to truncate.
        </PyParameter>

        <PyParameter name="&#x22;max_chars&#x22;" type="&#x22;int&#x22;" value="undefined">
          Maximum output length.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        Original value when short enough; truncated value otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_repro_sql_from_sql&#x22;" type="&#x22;(sql) -> str | None&#x22;">
      Create a reproducible SQL snippet for debugging failed checks.

      <PySourceCode>
        ```python
        def _repro_sql_from_sql(sql: str | None) -> str | None:
            """Create a reproducible SQL snippet for debugging failed checks.

            Args:
                sql: Compiled SQL string.

            Returns:
                SQL with a row limit appended when missing, or ``None``.

            """
            if sql is None:
                return None
            trimmed = sql.strip()
            if not trimmed:
                return None
            lower = trimmed.lower()
            if "limit" in lower:
                return trimmed
            return f"{trimmed}\nLIMIT 500"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;sql&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Compiled SQL string.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        SQL with a row limit appended when missing, or `None`.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_int_or_none&#x22;" type="&#x22;(value) -> int | None&#x22;">
      Safely coerce a value to `int`.

      <PySourceCode>
        ```python
        def _int_or_none(value: object) -> int | None:
            """Safely coerce a value to ``int``.

            Args:
                value: Candidate value.

            Returns:
                Parsed integer value, or ``None`` when coercion fails.

            """
            if value is None:
                return None
            if isinstance(value, bool):
                return None
            if isinstance(value, int):
                return value
            try:
                return int(str(value))
            except (ValueError, TypeError):
                return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;object&#x22;" value="undefined">
          Candidate value.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;int | None&#x22;">
        Parsed integer value, or `None` when coercion fails.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
