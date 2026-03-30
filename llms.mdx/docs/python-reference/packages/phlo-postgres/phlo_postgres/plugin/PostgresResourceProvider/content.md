# PostgresResourceProvider (/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin/PostgresResourceProvider)



Resource provider plugin that exposes PostgreSQL capabilities.

This plugin registers the PostgresResource and PostgresPublishTarget with
the phlo resource system, making them available to other components for
database operations and data publishing.

Example:

> > > provider = PostgresResourceProvider()
> > > resources = provider.get\_resources()
> > > targets = provider.get\_publish\_targets()

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the PostgreSQL resource provider.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > provider = PostgresResourceProvider()
    > > > meta = provider.metadata
    > > > print(meta.name)
    > > > postgres
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Return resource specifications exposed by this provider.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > provider = PostgresResourceProvider()
    > > > specs = provider.get\_resources()
    > > > print(specs\[0].name)
    > > > postgres
  </Callout>

  <PySourceCode>
    ```python
    def get_resources(self) -> list[ResourceSpec]:
        """Return resource specifications exposed by this provider.

        Returns:
            list[ResourceSpec]: List of registered resource specifications
                that can be accessed by other phlo components.

        Example:
            >>> provider = PostgresResourceProvider()
            >>> specs = provider.get_resources()
            >>> print(specs[0].name)
            postgres

        """
        return [ResourceSpec(name="postgres", resource=PostgresResource())]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[ResourceSpec]: List of registered resource specifications
    that can be accessed by other phlo components.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_publish_targets&#x22;" type="&#x22;(self) -> list[PublishTargetSpec]&#x22;">
  Return publish target capability specs exposed by this provider.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > provider = PostgresResourceProvider()
    > > > targets = provider.get\_publish\_targets()
    > > > print(targets\[0].name)
    > > > postgres
    > > > print(targets\[0].metadata)
    > > > \{'target\_system': 'postgres', 'role': 'serving'}
  </Callout>

  <PySourceCode>
    ```python
    def get_publish_targets(self) -> list[PublishTargetSpec]:
        """Return publish target capability specs exposed by this provider.

        Returns:
            list[PublishTargetSpec]: List of publish target specifications
                that define where data can be published to PostgreSQL.

        Example:
            >>> provider = PostgresResourceProvider()
            >>> targets = provider.get_publish_targets()
            >>> print(targets[0].name)
            postgres
            >>> print(targets[0].metadata)
            {'target_system': 'postgres', 'role': 'serving'}

        """
        return [
            PublishTargetSpec(
                name="postgres",
                provider=PostgresPublishTarget(),
                metadata={"target_system": "postgres", "role": "serving"},
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[PublishTargetSpec]: List of publish target specifications
    that define where data can be published to PostgreSQL.
  </PyFunctionReturn>
</PyFunction>
