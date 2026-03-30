# QualityCheckPlugin (/docs/python-reference/core/phlo/plugins/base/quality/QualityCheckPlugin)



Base class for quality check plugins.

Quality check plugins enable custom data validation logic
beyond the built-in checks.

Example:

```python
from phlo_quality.checks import QualityCheck, QualityCheckResult

class BusinessRuleCheck(QualityCheckPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="business_rule",
            version="1.0.0",
            description="Validate business rules",
        )

    def create_check(self, **kwargs) -> QualityCheck:
        rule = kwargs.get("rule")
        return BusinessRuleQualityCheck(rule=rule)


class BusinessRuleQualityCheck(QualityCheck):
    def __init__(self, rule: str):
        self.rule = rule

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        # Implement rule validation
        violations = df.query(f"not (\{self.rule\})")

        return QualityCheckResult(
            passed=len(violations) == 0,
            metric_name="business_rule",
            metric_value=\{"violations": len(violations)\},
        )

    @property
    def name(self) -> str:
        return f"business_rule_\{self.rule\}"
```

Functions [#functions]

<PyFunction name="&#x22;create_check&#x22;" type="&#x22;(self, **kwargs) -> TQualityCheck&#x22;">
  Create a quality check instance.

  This factory method creates instances of quality checks
  that can be used with @phlo\_quality decorator.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    def create_check(self, column: str, threshold: float) -> QualityCheck:
        return CustomQualityCheck(column=column, threshold=threshold)
    ```
  </Callout>

  <PySourceCode>
    ````python
    @abstractmethod
    def create_check(self, **kwargs) -> TQualityCheck:
        """Create a quality check instance.

        This factory method creates instances of quality checks
        that can be used with @phlo_quality decorator.

        Args:
            **kwargs: Parameters for configuring the check

        Returns:
            QualityCheck instance

        Example:
            \```python
            def create_check(self, column: str, threshold: float) -> QualityCheck:
                return CustomQualityCheck(column=column, threshold=threshold)
            \```

        """
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;kwargs&#x22;" type="null" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.quality.TQualityCheck&#x22;">
    QualityCheck instance
  </PyFunctionReturn>
</PyFunction>
