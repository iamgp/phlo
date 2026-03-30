# severity (/docs/python-reference/packages/phlo-pandera/phlo_pandera/severity)



Severity mapping utilities for quality checks.

This module provides functions to map quality check results to severity levels
that are consumed by the orchestration system (Dagster). The severity determines
how check failures are handled - whether they block downstream execution,
trigger warnings, or are purely informational.

Severity Levels:

* `None` (or omitted): Check passed successfully
* `"warn"`: Check failed but is non-blocking; may trigger alerts
* `"error"`: Check failed and is blocking; stops downstream execution

Severity Policies:

* Pandera schema contract checks are always blocking (ERROR on failure)
* Quality checks use configurable thresholds to determine WARN vs ERROR
* dbt tests use tags and test types to determine severity

Example:

```python
from phlo_pandera.severity import severity_for_quality_check

# Determine severity based on failure rate
severity = severity_for_quality_check(
    passed=False,
    failure_fraction=0.15,  # 15% of rows failed
    warn_threshold=0.10,     # Warn threshold is 10%
)
# Returns: "error" (exceeds warn threshold)

# Below warn threshold
severity = severity_for_quality_check(
    passed=False,
    failure_fraction=0.05,  # 5% of rows failed
    warn_threshold=0.10,     # Warn threshold is 10%
)
# Returns: "warn"
```

See Also:

* `contract.py`: Quality check contract definitions
* `decorator.py`: `@phlo_pandera` which uses these severity mappings

<PyAttribute name="&#x22;DBT_WARN_TAGS&#x22;" type="null" value="&#x22;{'warn', 'anomaly'}&#x22;" />

<PyAttribute name="&#x22;DBT_BLOCKING_TAGS&#x22;" type="null" value="&#x22;{'blocking'}&#x22;" />

<PyAttribute name="&#x22;DBT_BLOCKING_TEST_TYPES&#x22;" type="null" value="&#x22;{'not_null', 'unique', 'relationships'}&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;normalize_dbt_tags&#x22;" type="&#x22;(tags) -> set[str]&#x22;">
      Normalize dbt test tags for severity evaluation.

      Converts tags to lowercase, strips whitespace, and filters out empty values.
      This ensures consistent tag matching regardless of formatting variations.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        normalize_dbt_tags(["WARN", " blocking ", ""])
        # Returns: \{"warn", "blocking"\}

        normalize_dbt_tags(None)
        # Returns: set()
        ```
      </Callout>

      <PySourceCode>
        ````python
        def normalize_dbt_tags(tags: Iterable[str] | None) -> set[str]:
            """Normalize dbt test tags for severity evaluation.

            Converts tags to lowercase, strips whitespace, and filters out empty values.
            This ensures consistent tag matching regardless of formatting variations.

            Args:
                tags: Raw dbt tags as an iterable of strings, or None.

            Returns:
                Set of normalized, lowercase, non-empty tag strings.

            Example:
                \```python
                normalize_dbt_tags(["WARN", " blocking ", ""])
                # Returns: {"warn", "blocking"}

                normalize_dbt_tags(None)
                # Returns: set()
                \```

            """

            if tags is None:
                return set()
            return {tag.strip().lower() for tag in tags if tag and tag.strip()}
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;tags&#x22;" type="&#x22;Iterable[str] | None&#x22;" value="undefined">
          Raw dbt tags as an iterable of strings, or None.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;set&#x22;">
        Set of normalized, lowercase, non-empty tag strings.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;severity_for_pandera_contract&#x22;" type="&#x22;(*, passed) -> str | None&#x22;">
      Map Pandera contract pass/fail state to severity.

      Pandera schema contract checks are always blocking. A failure indicates
      that the data does not conform to the expected schema, which is typically
      a serious data quality issue that should halt processing.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        severity_for_pandera_contract(passed=True)
        # Returns: None

        severity_for_pandera_contract(passed=False)
        # Returns: "error"
        ```
      </Callout>

      <PySourceCode>
        ````python
        def severity_for_pandera_contract(*, passed: bool) -> str | None:
            """Map Pandera contract pass/fail state to severity.

            Pandera schema contract checks are always blocking. A failure indicates
            that the data does not conform to the expected schema, which is typically
            a serious data quality issue that should halt processing.

            Args:
                passed: Whether the Pandera contract evaluation passed.

            Returns:
                ``None`` if passed (no severity needed), otherwise ``"error"``.

            Example:
                \```python
                severity_for_pandera_contract(passed=True)
                # Returns: None

                severity_for_pandera_contract(passed=False)
                # Returns: "error"
                \```

            """

            return None if passed else "error"
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether the Pandera contract evaluation passed.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        `None` if passed (no severity needed), otherwise `"error"`.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;severity_for_quality_check&#x22;" type="&#x22;(*, passed, failure_fraction, warn_threshold) -> str | None&#x22;">
      Map quality-check result values to severity.

      Determines the appropriate severity level based on whether the check
      passed and, if it failed, what fraction of rows failed. This enables
      configurable tolerance for data quality issues.

      <Callout title="&#x22;Logic&#x22;" type="&#x22;logic&#x22;">
        * If `passed` is True: returns None (no severity)
        * If `failure_fraction` is 0 or less: returns "error"
        * If `warn_threshold` > 0 and `failure_fraction` \<= `warn_threshold`:
          returns "warn"
        * Otherwise: returns "error"
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        # Passed check
        severity_for_quality_check(passed=True, failure_fraction=0.0, warn_threshold=0.1)
        # Returns: None

        # Failed but within warn threshold
        severity_for_quality_check(passed=False, failure_fraction=0.05, warn_threshold=0.1)
        # Returns: "warn"

        # Failed and exceeds warn threshold
        severity_for_quality_check(passed=False, failure_fraction=0.15, warn_threshold=0.1)
        # Returns: "error"
        ```
      </Callout>

      <PySourceCode>
        ````python
        def severity_for_quality_check(
            *, passed: bool, failure_fraction: float, warn_threshold: float
        ) -> str | None:
            """Map quality-check result values to severity.

            Determines the appropriate severity level based on whether the check
            passed and, if it failed, what fraction of rows failed. This enables
            configurable tolerance for data quality issues.

            Logic:
                - If ``passed`` is True: returns None (no severity)
                - If ``failure_fraction`` is 0 or less: returns "error"
                - If ``warn_threshold`` > 0 and ``failure_fraction`` <= ``warn_threshold``:
                  returns "warn"
                - Otherwise: returns "error"

            Args:
                passed: Whether the quality check passed.
                failure_fraction: Failed rows divided by total rows (0.0 to 1.0).
                warn_threshold: Maximum failure fraction treated as a warning.
                    Values above this threshold are treated as errors.

            Returns:
                ``None`` for pass, ``"warn"`` for bounded failures, ``"error"`` otherwise.

            Example:
                \```python
                # Passed check
                severity_for_quality_check(passed=True, failure_fraction=0.0, warn_threshold=0.1)
                # Returns: None

                # Failed but within warn threshold
                severity_for_quality_check(passed=False, failure_fraction=0.05, warn_threshold=0.1)
                # Returns: "warn"

                # Failed and exceeds warn threshold
                severity_for_quality_check(passed=False, failure_fraction=0.15, warn_threshold=0.1)
                # Returns: "error"
                \```

            """

            if passed:
                return None
            if failure_fraction <= 0:
                return "error"
            if warn_threshold > 0 and failure_fraction <= warn_threshold:
                return "warn"
            return "error"
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;passed&#x22;" type="&#x22;bool&#x22;" value="undefined">
          Whether the quality check passed.
        </PyParameter>

        <PyParameter name="&#x22;failure_fraction&#x22;" type="&#x22;float&#x22;" value="undefined">
          Failed rows divided by total rows (0.0 to 1.0).
        </PyParameter>

        <PyParameter name="&#x22;warn_threshold&#x22;" type="&#x22;float&#x22;" value="undefined">
          Maximum failure fraction treated as a warning.
          Values above this threshold are treated as errors.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        `None` for pass, `"warn"` for bounded failures, `"error"` otherwise.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;severity_for_dbt_test&#x22;" type="&#x22;(*, test_type, tags) -> str&#x22;">
      Map dbt test metadata to severity.

      Determines severity for dbt tests based on test type and tags.
      Certain test types (not\_null, unique, relationships) are considered
      blocking by default. Tags can override this behavior.

      <Callout title="&#x22;Tag Overrides&#x22;" type="&#x22;tag-overrides&#x22;">
        * `tag:blocking`: Forces severity to "error"
        * `tag:warn` or `tag:anomaly`: Forces severity to "warn"
      </Callout>

      <Callout title="&#x22;Blocking Test Types&#x22;" type="&#x22;blocking-test-types&#x22;">
        * `not_null`: Missing values are critical
        * `unique`: Duplicate keys are critical
        * `relationships`: Referential integrity violations are critical
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        # Blocking test type
        severity_for_dbt_test(test_type="not_null", tags=[])
        # Returns: "error"

        # Non-blocking test type
        severity_for_dbt_test(test_type="accepted_values", tags=[])
        # Returns: "warn"

        # Tag override to blocking
        severity_for_dbt_test(test_type="accepted_values", tags=["blocking"])
        # Returns: "error"

        # Tag override to warn
        severity_for_dbt_test(test_type="not_null", tags=["warn"])
        # Returns: "warn"
        ```
      </Callout>

      <PySourceCode>
        ````python
        def severity_for_dbt_test(*, test_type: str | None, tags: Iterable[str] | None) -> str:
            """Map dbt test metadata to severity.

            Determines severity for dbt tests based on test type and tags.
            Certain test types (not_null, unique, relationships) are considered
            blocking by default. Tags can override this behavior.

            Tag Overrides:
                - ``tag:blocking``: Forces severity to "error"
                - ``tag:warn`` or ``tag:anomaly``: Forces severity to "warn"

            Blocking Test Types:
                - ``not_null``: Missing values are critical
                - ``unique``: Duplicate keys are critical
                - ``relationships``: Referential integrity violations are critical

            Args:
                test_type: dbt test type string (e.g., "not_null", "accepted_values").
                tags: dbt test tags as an iterable of strings.

            Returns:
                ``"error"`` when blocking tags or blocking test types are present,
                otherwise ``"warn"``.

            Example:
                \```python
                # Blocking test type
                severity_for_dbt_test(test_type="not_null", tags=[])
                # Returns: "error"

                # Non-blocking test type
                severity_for_dbt_test(test_type="accepted_values", tags=[])
                # Returns: "warn"

                # Tag override to blocking
                severity_for_dbt_test(test_type="accepted_values", tags=["blocking"])
                # Returns: "error"

                # Tag override to warn
                severity_for_dbt_test(test_type="not_null", tags=["warn"])
                # Returns: "warn"
                \```

            """

            normalized_tags = normalize_dbt_tags(tags)
            normalized_test_type = (test_type or "").strip().lower()

            if normalized_tags & DBT_BLOCKING_TAGS:
                return "error"
            if normalized_tags & DBT_WARN_TAGS:
                return "warn"
            if normalized_test_type in DBT_BLOCKING_TEST_TYPES:
                return "error"
            return "warn"
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_type&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          dbt test type string (e.g., "not\_null", "accepted\_values").
        </PyParameter>

        <PyParameter name="&#x22;tags&#x22;" type="&#x22;Iterable[str] | None&#x22;" value="undefined">
          dbt test tags as an iterable of strings.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        `"error"` when blocking tags or blocking test types are present,
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
