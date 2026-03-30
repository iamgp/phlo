# LineageResourceProvider (/docs/python-reference/packages/phlo-lineage/phlo_lineage/resource_provider/LineageResourceProvider)



Expose phlo-lineage as a lineage sink capability.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for capability discovery.

  <Callout title="&#x22;Attributes Returned&#x22;" type="&#x22;attributes-returned&#x22;">
    * name: "lineage"
    * version: "0.1.0"
    * description: "Lineage sink capability provider"
    * tags: \["lineage"]
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > provider = LineageResourceProvider()
    > > > meta = provider.metadata
    > > > print(meta.name)
    > > > 'lineage'
    > > > print(meta.tags)
    > > > \['lineage']
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list&#x22;">
  Return list of raw resources exposed by this provider.

  This provider does not expose any raw resources directly. All lineage
  functionality is accessed through the lineage\_sinks capability interface.

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    get\_lineage\_sinks() for the capability interface.
  </Callout>

  <PySourceCode>
    ```python
    def get_resources(self) -> list:
        """Return list of raw resources exposed by this provider.

        This provider does not expose any raw resources directly. All lineage
        functionality is accessed through the lineage_sinks capability interface.

        Returns:
            Empty list. Raw resources are not exposed in this slice.

        See Also:
            get_lineage_sinks() for the capability interface.

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Empty list. Raw resources are not exposed in this slice.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_lineage_sinks&#x22;" type="&#x22;(self) -> list[LineageSinkSpec]&#x22;">
  Expose the phlo-lineage sink as a capability.

  Returns the lineage sink specification that allows other Phlo components
  to record and query data lineage through a standardized interface.

  <Callout title="&#x22;Capability Usage&#x22;" type="&#x22;capability-usage&#x22;">
    Components can access this sink via:

    > > > from phlo.capabilities import get\_lineage\_sink
    > > > sink = get\_lineage\_sink("phlo-lineage")
    > > > sink.record\_row\_lineage(row\_id="...", table\_name="bronze.orders")
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    PhloLineageSink for the full API documentation.
    phlo.capabilities module for capability discovery patterns.
  </Callout>

  <PySourceCode>
    ```python
    def get_lineage_sinks(self) -> list[LineageSinkSpec]:
        """Expose the phlo-lineage sink as a capability.

        Returns the lineage sink specification that allows other Phlo components
        to record and query data lineage through a standardized interface.

        Returns:
            List containing a single LineageSinkSpec with:
                - name: "phlo-lineage" (identifier for capability lookup)
                - provider: PhloLineageSink instance (the actual sink implementation)

        Capability Usage:
            Components can access this sink via:
            >>> from phlo.capabilities import get_lineage_sink
            >>> sink = get_lineage_sink("phlo-lineage")
            >>> sink.record_row_lineage(row_id="...", table_name="bronze.orders")

        See Also:
            PhloLineageSink for the full API documentation.
            phlo.capabilities module for capability discovery patterns.

        """
        return [
            LineageSinkSpec(
                name="phlo-lineage",
                provider=PhloLineageSink(),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing a single LineageSinkSpec with:

    * name: "phlo-lineage" (identifier for capability lookup)
    * provider: PhloLineageSink instance (the actual sink implementation)
  </PyFunctionReturn>
</PyFunction>
