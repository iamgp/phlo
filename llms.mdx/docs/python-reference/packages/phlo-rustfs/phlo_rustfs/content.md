# phlo_rustfs (/docs/python-reference/packages/phlo-rustfs/phlo_rustfs)



RustFS service plugin package.

This package provides a Phlo plugin for integrating RustFS (Rust-based S3-compatible
object storage) into the data platform. It exposes service definitions for running
RustFS containers and bucket initialization, along with resource providers for
S3-compatible storage capabilities.

Exports:
RustfsServicePlugin: Main service plugin for running RustFS container.
RustfsSettings: Configuration settings for RustFS connectivity.
get\_settings: Cached factory function returning RustfsSettings instance.

Example:

> > > from phlo\_rustfs import RustfsSettings, get\_settings
> > > settings = get\_settings()
> > > print(settings.rustfs\_endpoint())
> > > "localhost:9000"

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['RustfsServicePlugin', 'RustfsSettings', 'get_settings']&#x22;" />

<PyAttribute name="&#x22;__version__&#x22;" type="null" value="&#x22;'0.2.4'&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/settings&#x22;" title="&#x22;settings&#x22;" />
    </Cards>
  </Tab>
</Tabs>
