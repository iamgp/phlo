# QualityCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/QualityCheck)



Abstract base class for all quality checks.

All quality checks must inherit from this class and implement the
`execute` method which validates data and returns a `QualityCheckResult`.
The `name` property provides a stable identifier for the check.

Subclasses should typically use the `@dataclass` decorator for clean,
declarative configuration.

Example:

```python
from dataclasses import dataclass

@dataclass
class CustomCheck(QualityCheck):
    column: str
    expected_value: str

    def execute(self, df, context):
        passed = (df[self.column] == self.expected_value).all()
        return QualityCheckResult(
            passed=passed,
            metric_name="custom_check",
            metric_value=\{"matches": int(passed)\},
        )

    @property
    def name(self) -> str:
        return f"custom_\{self.column\}"
```

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Human-readable name for this check.

  This property should return a stable, unique identifier for the check
  that can be used in logging, reporting, and metadata. It typically
  includes the check type and configuration details.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute the quality check on the given DataFrame.

  This method must be implemented by all subclasses to perform the actual
  validation logic. It receives a pandas DataFrame and an optional runtime
  context, and must return a `QualityCheckResult` with the outcome.

  <PySourceCode>
    ```python
    @abstractmethod
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute the quality check on the given DataFrame.

        This method must be implemented by all subclasses to perform the actual
        validation logic. It receives a pandas DataFrame and an optional runtime
        context, and must return a ``QualityCheckResult`` with the outcome.

        Args:
            df: DataFrame to validate, containing the data loaded from the
                target table or query.
            context: Runtime context for logging and resource access. May be
                None in testing scenarios.

        Returns:
            QualityCheckResult containing pass/fail status, metric values,
            metadata, and optional failure message.

        Raises:
            Exception: Subclasses may raise exceptions for unrecoverable errors,
                though they should generally catch and return failed results.

        """
        pass
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      DataFrame to validate, containing the data loaded from the
      target table or query.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context for logging and resource access. May be
      None in testing scenarios.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult containing pass/fail status, metric values,
  </PyFunctionReturn>
</PyFunction>
