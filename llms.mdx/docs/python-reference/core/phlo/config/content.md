# config (/docs/python-reference/core/phlo/config)



Phlo configuration module.

This module provides centralized configuration management for the Phlo framework.
It exports configuration classes and utilities for settings management, network
resolution, and base configuration patterns.

Key Components:

* :class:`~phlo.config.base.BaseConfig`: Foundation for all config classes
* :class:`~phlo.config.settings.Settings`: Primary application settings
* :func:`~phlo.config.settings.get_settings`: Access cached settings
* :func:`~phlo.config.network.resolve_host`: DNS resolution with fallback
* :func:`~phlo.config.network.resolve_url`: URL resolution with fallback

Example:

```python
from phlo.config import get_settings, Settings

# Access settings
settings = get_settings()
print(settings.phlo_log_level)

# Use in custom configuration
class MyConfig(BaseConfig):
    my_setting: str = "default"
```

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['BaseConfig', 'Settings', '_get_config', 'config', 'get_settings', 'resolve_host', 'resolve_url']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/core/phlo/config/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/config/network&#x22;" title="&#x22;network&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/config/base&#x22;" title="&#x22;base&#x22;" />
    </Cards>
  </Tab>
</Tabs>
