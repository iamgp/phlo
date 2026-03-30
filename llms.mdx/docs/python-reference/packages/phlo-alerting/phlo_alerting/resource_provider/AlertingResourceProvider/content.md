# AlertingResourceProvider (/docs/python-reference/packages/phlo-alerting/phlo_alerting/resource_provider/AlertingResourceProvider)



Expose phlo-alerting as a neutral alert sink capability.

This resource provider registers phlo-alerting with the Phlo capability
system, allowing other components to discover and use alerting
functionality through the AlertSinkSpec contract.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identity and discovery information.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list&#x22;">
  Return list of raw resources exposed by this provider.

  This provider does not expose any raw resources directly;
  alerting functionality is exposed through get\_alert\_sinks().

  <PySourceCode>
    ```python
    def get_resources(self) -> list:
        """Return list of raw resources exposed by this provider.

        This provider does not expose any raw resources directly;
        alerting functionality is exposed through get_alert_sinks().

        Returns:
            Empty list since no raw resources are exposed.

        Examples:
            >>> provider = AlertingResourceProvider()
            >>> provider.get_resources()
            []

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Empty list since no raw resources are exposed.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_alert_sinks&#x22;" type="&#x22;(self) -> list[AlertSinkSpec]&#x22;">
  Expose phlo-alerting as an alert sink capability.

  Returns a list of AlertSinkSpec objects that define how other
  components can send alerts through this provider.

  <PySourceCode>
    ```python
    def get_alert_sinks(self) -> list[AlertSinkSpec]:
        """Expose phlo-alerting as an alert sink capability.

        Returns a list of AlertSinkSpec objects that define how other
        components can send alerts through this provider.

        Returns:
            List containing a single AlertSinkSpec for the alerting capability.

        Examples:
            >>> provider = AlertingResourceProvider()
            >>> sinks = provider.get_alert_sinks()
            >>> len(sinks)
            1
            >>> sinks[0].name
            'alerting'

        """
        return [
            AlertSinkSpec(
                name="alerting",
                provider=AlertManagerSink(),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing a single AlertSinkSpec for the alerting capability.
  </PyFunctionReturn>
</PyFunction>
