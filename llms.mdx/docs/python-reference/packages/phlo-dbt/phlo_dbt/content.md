# phlo_dbt (/docs/python-reference/packages/phlo-dbt/phlo_dbt)



Phlo dbt integration package.

This package provides dbt integration for the Phlo data platform, including:

* Asset specification generation from dbt manifests
* Runtime configuration management for dbt profiles
* Project scaffolding utilities
* CLI commands for dbt operations

Example:

> > > from phlo\_dbt import build\_dbt\_asset\_specs, DbtRuntimeConfig
> > > specs = build\_dbt\_asset\_specs()
> > > config = DbtRuntimeConfig(target\_name="prod")

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['DEFAULT_DBT_TARGET', 'DbtRuntimeConfig', 'DbtSettings', 'build_dbt_asset_specs', 'ensure_dbt_profile', 'get_settings', 'render_dbt_profile_yaml', 'resolve_dbt_target_name', 'resolve_dbt_runtime_config', 'write_dbt_profile', 'write_dbt_scaffold']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/dbt_inject&#x22;" title="&#x22;dbt_inject&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/dbt_schema&#x22;" title="&#x22;dbt_schema&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/asset_checks&#x22;" title="&#x22;asset_checks&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/cli_plugin&#x22;" title="&#x22;cli_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/translator&#x22;" title="&#x22;translator&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/scaffold&#x22;" title="&#x22;scaffold&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/cli_publishing&#x22;" title="&#x22;cli_publishing&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/runtime_config&#x22;" title="&#x22;runtime_config&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/lineage_import&#x22;" title="&#x22;lineage_import&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/transformer&#x22;" title="&#x22;transformer&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/hooks&#x22;" title="&#x22;hooks&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/discovery&#x22;" title="&#x22;discovery&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/assets&#x22;" title="&#x22;assets&#x22;" />
    </Cards>
  </Tab>
</Tabs>
