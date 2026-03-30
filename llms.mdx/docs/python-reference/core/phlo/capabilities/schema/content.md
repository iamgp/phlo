# schema (/docs/python-reference/core/phlo/capabilities/schema)



Default schema change classification helper.

Provides conservative (lowest-common-denominator) classification rules that
storage providers can override via `SchemaMigrator.classify_change`.

<PyAttribute name="&#x22;CLASSIFICATION_ORDER&#x22;" type="null" value="&#x22;('safe', 'warning', 'breaking')&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;default_classify_change&#x22;" type="&#x22;(change_type, **details) -> str&#x22;">
      Classify a schema change using conservative defaults.

      <PySourceCode>
        ```python
        def default_classify_change(change_type: str, **details: Any) -> str:
            """Classify a schema change using conservative defaults.

            Args:
                change_type: One of the recognised change type strings.
                **details: Extra context (e.g. ``nullable``, ``has_default``).

            Returns:
                Classification string: ``"safe"``, ``"warning"``, or ``"breaking"``.
            """
            if change_type == "add":
                nullable = details.get("nullable", True)
                has_default = details.get("has_default", False)
                if not nullable and not has_default:
                    return "breaking"
                if not nullable and has_default:
                    return "warning"
                return "safe"

            return _DEFAULT_CLASSIFICATIONS.get(change_type, "breaking")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;change_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          One of the recognised change type strings.
        </PyParameter>

        <PyParameter name="&#x22;details&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Classification string: `"safe"`, `"warning"`, or `"breaking"`.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;worst_classification&#x22;" type="&#x22;(classifications) -> str&#x22;">
      Return the most severe classification from a list.

      <PySourceCode>
        ```python
        def worst_classification(classifications: list[str]) -> str:
            """Return the most severe classification from a list.

            Args:
                classifications: List of classification strings.

            Returns:
                The worst (most severe) classification present.
            """
            if not classifications:
                return "safe"
            worst_idx = max(CLASSIFICATION_ORDER.index(c) for c in classifications)
            return CLASSIFICATION_ORDER[worst_idx]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;classifications&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          List of classification strings.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        The worst (most severe) classification present.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
