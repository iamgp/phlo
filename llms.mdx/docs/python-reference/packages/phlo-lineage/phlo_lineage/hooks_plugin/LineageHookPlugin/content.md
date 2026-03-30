# LineageHookPlugin (/docs/python-reference/packages/phlo-lineage/phlo_lineage/hooks_plugin/LineageHookPlugin)



Hook plugin that synchronizes lineage events to graph and database.

This plugin subscribes to lineage events from the Phlo event system and
ensures lineage information is propagated to both the in-memory graph
(for immediate visibility) and the persistent store (for durability).

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata with name="lineage", version="0.1.0"
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_hooks&#x22;" type="&#x22;(self) -> list[HookRegistration]&#x22;">
  Register hook handlers with the Phlo event system.

  Returns a list of HookRegistration objects defining which events
  this plugin wants to receive and which handler method to invoke.

  <Callout title="&#x22;Filtering&#x22;" type="&#x22;filtering&#x22;">
    The filter ensures this plugin only receives lineage.edges
    event types, ignoring other lineage-related events.
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = LineageHookPlugin()
    > > > hooks = plugin.get\_hooks()
    > > > print(len(hooks))
    > > > 1
    > > > print(hooks\[0].hook\_name)
    > > > 'lineage\_updates'
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    phlo.plugins.hooks.HookRegistration for registration structure.
  </Callout>

  <PySourceCode>
    ```python
    def get_hooks(self) -> list[HookRegistration]:
        """Register hook handlers with the Phlo event system.

        Returns a list of HookRegistration objects defining which events
        this plugin wants to receive and which handler method to invoke.

        Returns:
            List containing one HookRegistration:
                - hook_name: "lineage_updates"
                - handler: self._handle_lineage method
                - filters: HookFilter(event_types={"lineage.edges"})

        Filtering:
            The filter ensures this plugin only receives lineage.edges
            event types, ignoring other lineage-related events.

        Example:
            >>> plugin = LineageHookPlugin()
            >>> hooks = plugin.get_hooks()
            >>> print(len(hooks))
            1
            >>> print(hooks[0].hook_name)
            'lineage_updates'

        See Also:
            phlo.plugins.hooks.HookRegistration for registration structure.

        """
        return [
            HookRegistration(
                hook_name="lineage_updates",
                handler=self._handle_lineage,
                filters=HookFilter(event_types={"lineage.edges"}),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing one HookRegistration:

    * hook\_name: "lineage\_updates"
    * handler: self.\_handle\_lineage method
    * filters: HookFilter(event\_types=\{"lineage.edges"})
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_handle_lineage&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Process a lineage event and update graph and database.

  This is the core event handler method. It receives lineage events,
  updates the in-memory graph immediately, and attempts to persist
  to the database if configured.

  <Callout title="&#x22;Processing Flow&#x22;" type="&#x22;processing-flow&#x22;">
    1. Type check: Ignore non-LineageEvent objects
    2. Log start with edge count and asset key count
    3. Update in-memory graph via get\_lineage\_graph()
    4. Resolve database connection string
    5. If no database: log skip message and return
    6. Persist edges via LineageStore
    7. Log success with persisted edge count
    8. On exception: log warning with error details
  </Callout>

  <Callout title="&#x22;Logging&#x22;" type="&#x22;logging&#x22;">
    * INFO: lineage\_sync\_started, lineage\_sync\_succeeded
    * WARNING: lineage\_sync\_skipped\_missing\_db\_url, Failed to persist
  </Callout>

  <Callout title="&#x22;Side Effects&#x22;" type="&#x22;side-effects&#x22;">
    * Modifies global \_lineage\_graph singleton
    * Writes to PostgreSQL phlo.asset\_lineage\_edges table
    * Emits structured log records
  </Callout>

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > from phlo.hooks import LineageEvent
    > > > event = LineageEvent(
    > > > ...     event\_type="lineage.edges",
    > > > ...     edges=\[("a", "b"), ("b", "c")],
    > > > ...     asset\_keys=\["a", "b", "c"],
    > > > ... )
    > > > plugin = LineageHookPlugin()
    > > > plugin.\_handle\_lineage(event)
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This method is called automatically by the hooks system.
    Manual invocation is primarily useful for testing.
  </Callout>

  <PySourceCode>
    ```python
    def _handle_lineage(self, event: Any) -> None:
        """Process a lineage event and update graph and database.

        This is the core event handler method. It receives lineage events,
        updates the in-memory graph immediately, and attempts to persist
        to the database if configured.

        Args:
            event: Hook event payload. Must be a LineageEvent instance;
                other types are silently ignored.

        Processing Flow:
            1. Type check: Ignore non-LineageEvent objects
            2. Log start with edge count and asset key count
            3. Update in-memory graph via get_lineage_graph()
            4. Resolve database connection string
            5. If no database: log skip message and return
            6. Persist edges via LineageStore
            7. Log success with persisted edge count
            8. On exception: log warning with error details

        Logging:
            - INFO: lineage_sync_started, lineage_sync_succeeded
            - WARNING: lineage_sync_skipped_missing_db_url, Failed to persist

        Side Effects:
            - Modifies global _lineage_graph singleton
            - Writes to PostgreSQL phlo.asset_lineage_edges table
            - Emits structured log records

        Example:
            >>> from phlo.hooks import LineageEvent
            >>> event = LineageEvent(
            ...     event_type="lineage.edges",
            ...     edges=[("a", "b"), ("b", "c")],
            ...     asset_keys=["a", "b", "c"],
            ... )
            >>> plugin = LineageHookPlugin()
            >>> plugin._handle_lineage(event)

        Note:
            This method is called automatically by the hooks system.
            Manual invocation is primarily useful for testing.

        """
        if not isinstance(event, LineageEvent):
            return
        edge_count = len(event.edges)
        asset_key_count = len(event.asset_keys or [])
        graph = get_lineage_graph()
        for source, target in event.edges:
            graph.add_edge(source, target)

        connection_string = resolve_lineage_db_url_with_postgres_fallback()
        if not connection_string:
            logger.info(
                "lineage_sync_skipped_missing_db_url",
                event_type=event.event_type,
                edge_count=edge_count,
                asset_key_count=asset_key_count,
            )
            return

        logger.info(
            "lineage_sync_started",
            event_type=event.event_type,
            edge_count=edge_count,
            asset_key_count=asset_key_count,
        )
        try:
            store = LineageStore(connection_string)
            persisted_edges = store.record_asset_edges(
                event.edges,
                asset_keys=event.asset_keys,
                metadata=event.metadata,
                tags=event.tags,
            )
            logger.info(
                "lineage_sync_succeeded",
                event_type=event.event_type,
                edge_count=edge_count,
                asset_key_count=asset_key_count,
                persisted_edge_count=persisted_edges,
            )
        except Exception as exc:
            logger.warning(
                "Failed to persist asset lineage edges: %s",
                exc,
                event_type=event.event_type,
                edge_count=edge_count,
                asset_key_count=asset_key_count,
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Hook event payload. Must be a LineageEvent instance;
      other types are silently ignored.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
