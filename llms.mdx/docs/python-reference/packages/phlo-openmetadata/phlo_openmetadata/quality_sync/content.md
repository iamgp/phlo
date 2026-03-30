# quality_sync (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync)



Quality check synchronization to OpenMetadata.

Maps quality checks from @phlo\_quality decorator and dbt tests
to OpenMetadata test definitions and publishes results.

This module provides the mapping layer between Phlo's quality framework
and OpenMetadata's data quality testing infrastructure.

Example:

> > > from phlo\_openmetadata.quality\_sync import QualityCheckPublisher
> > > from phlo\_openmetadata import OpenMetadataClient
> > > publisher = QualityCheckPublisher(client)
> > > publisher.publish\_test\_definitions(checks, table\_fqn)
> > > \{'created': 3, 'failed': 0}

<PyAttribute name="&#x22;CountCheck&#x22;" type="null" value="&#x22;_CountCheck&#x22;" />

<PyAttribute name="&#x22;FreshnessCheck&#x22;" type="null" value="&#x22;_FreshnessCheck&#x22;" />

<PyAttribute name="&#x22;NullCheck&#x22;" type="null" value="&#x22;_NullCheck&#x22;" />

<PyAttribute name="&#x22;RangeCheck&#x22;" type="null" value="&#x22;_RangeCheck&#x22;" />

<PyAttribute name="&#x22;UniqueCheck&#x22;" type="null" value="&#x22;_UniqueCheck&#x22;" />

<PyAttribute name="&#x22;CustomSQLCheck&#x22;" type="null" value="&#x22;_CustomSQLCheck&#x22;" />

<PyAttribute name="&#x22;QualityCheckResult&#x22;" type="null" value="&#x22;_QualityCheckResult&#x22;" />

<PyAttribute name="&#x22;T&#x22;" type="null" value="&#x22;TypeVar('T')&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;_CountCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/_CountCheck&#x22;" />

      <Card title="&#x22;_FreshnessCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/_FreshnessCheck&#x22;" />

      <Card title="&#x22;_NullCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/_NullCheck&#x22;" />

      <Card title="&#x22;_RangeCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/_RangeCheck&#x22;" />

      <Card title="&#x22;_UniqueCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/_UniqueCheck&#x22;" />

      <Card title="&#x22;_CustomSQLCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/_CustomSQLCheck&#x22;" />

      <Card title="&#x22;QualityCheckMapper&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/QualityCheckMapper&#x22;" />

      <Card title="&#x22;QualityCheckPublisher&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/QualityCheckPublisher&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_publish_items&#x22;" type="&#x22;(items, publish_fn, item_name_fn, context) -> dict[str, int]&#x22;">
      Generic publish loop with error handling and stats tracking.

      <PySourceCode>
        ```python
        def _publish_items(
            items: list[T],
            publish_fn: Callable[[T], None],
            item_name_fn: Callable[[T], str],
            context: str,
        ) -> dict[str, int]:
            """Generic publish loop with error handling and stats tracking.

            Args:
                items: Items to publish.
                publish_fn: Function to call for each item (should raise on failure).
                item_name_fn: Function to get display name for logging.
                context: Context string for error messages.

            Returns:
                Dict with 'created' and 'failed' counts.

            """
            stats = {"created": 0, "failed": 0}
            for item in items:
                try:
                    publish_fn(item)
                    logger.info(
                        "openmetadata_publish_item_succeeded",
                        context=context,
                        item_name=item_name_fn(item),
                    )
                    stats["created"] += 1
                except Exception as exc:
                    logger.error(
                        "openmetadata_publish_item_failed",
                        context=context,
                        item_name=item_name_fn(item),
                        error=str(exc),
                    )
                    stats["failed"] += 1
            return stats
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;items&#x22;" type="&#x22;list[T]&#x22;" value="undefined">
          Items to publish.
        </PyParameter>

        <PyParameter name="&#x22;publish_fn&#x22;" type="&#x22;Callable[[T], None]&#x22;" value="undefined">
          Function to call for each item (should raise on failure).
        </PyParameter>

        <PyParameter name="&#x22;item_name_fn&#x22;" type="&#x22;Callable[[T], str]&#x22;" value="undefined">
          Function to get display name for logging.
        </PyParameter>

        <PyParameter name="&#x22;context&#x22;" type="&#x22;str&#x22;" value="undefined">
          Context string for error messages.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dict with 'created' and 'failed' counts.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
