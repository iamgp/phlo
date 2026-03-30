# BaseConfig (/docs/python-reference/core/phlo/config/base/BaseConfig)



Base configuration class with common settings for all config domains.

This class provides a standardized foundation for all Phlo configuration
classes. It handles environment variable loading from `.phlo/.env` and
`.phlo/.env.local` files with case-insensitive matching.

Attributes [#attributes]

<PyAttribute name="&#x22;model_config&#x22;" type="null" value="&#x22;SettingsConfigDict(env_file=('.phlo/.env', '.phlo/.env.local'), case_sensitive=False, extra='ignore')&#x22;">
  Pydantic settings configuration with env file paths,
  case-insensitive matching, and extra field ignoring.
</PyAttribute>
