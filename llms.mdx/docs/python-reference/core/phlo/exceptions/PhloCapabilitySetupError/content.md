# PhloCapabilitySetupError (/docs/python-reference/core/phlo/exceptions/PhloCapabilitySetupError)



Raised when a capability is present but cannot be set up correctly.

Attributes [#attributes]

<PyAttribute name="&#x22;capability&#x22;" type="null" value="&#x22;capability&#x22;" />

<PyAttribute name="&#x22;required&#x22;" type="null" value="&#x22;required&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, capability, message, *, required, suggestions=None, cause=None)&#x22;">
  <PySourceCode>
    ```python
    def __init__(
        self,
        capability: str,
        message: str,
        *,
        required: bool,
        suggestions: list[str] | None = None,
        cause: Exception | None = None,
    ):
        self.capability = capability
        self.required = required
        super().__init__(
            message=message,
            code=PhloErrorCode.INFRASTRUCTURE_ERROR,
            suggestions=suggestions,
            cause=cause,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;capability&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;required&#x22;" type="&#x22;bool&#x22;" value="null" />

    <PyParameter name="&#x22;suggestions&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;cause&#x22;" type="&#x22;Exception | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>
