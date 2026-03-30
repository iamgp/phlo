# Plugin (/docs/python-reference/core/phlo/plugins/base/plugin/Plugin)



Base class for all Phlo plugins.

This abstract base class defines the interface that all plugin types must
implement. It provides lifecycle hooks for initialization and cleanup, and
requires concrete implementations to provide metadata.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;initialize&#x22;" type="&#x22;(self, config) -> None&#x22;">
  Initialize the plugin with configuration.

  This method is called once when the plugin is loaded.
  Override to perform initialization tasks like:

  * Validating configuration
  * Setting up connections
  * Loading resources

  <PySourceCode>
    ```python
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the plugin with configuration.

        This method is called once when the plugin is loaded.
        Override to perform initialization tasks like:
        - Validating configuration
        - Setting up connections
        - Loading resources

        Args:
            config: Configuration dictionary for the plugin

        """
        return
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;config&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      Configuration dictionary for the plugin
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;cleanup&#x22;" type="&#x22;(self) -> None&#x22;">
  Clean up plugin resources.

  This method is called when the plugin is being unloaded.
  Override to perform cleanup tasks like:

  * Closing connections
  * Releasing resources
  * Saving state

  <PySourceCode>
    ```python
    def cleanup(self) -> None:
        """Clean up plugin resources.

        This method is called when the plugin is being unloaded.
        Override to perform cleanup tasks like:
        - Closing connections
        - Releasing resources
        - Saving state
        """
        return
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
