# catalog_scanner (/docs/python-reference/packages/phlo-nessie/phlo_nessie/catalog_scanner)



Nessie catalog scanner for table discovery.

This module provides a lightweight Nessie API client focused on catalog discovery:

* namespaces (schemas)
* tables within namespaces
* per-table metadata payloads

The scanner supports fallback to Trino query engine when direct Nessie REST API
calls fail. It deliberately does not know about any downstream metadata systems
(e.g., OpenMetadata), maintaining separation of concerns.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;NessieTableScanner&#x22;" href="&#x22;/docs/python-reference/packages/phlo-nessie/phlo_nessie/catalog_scanner/NessieTableScanner&#x22;" />
    </Cards>
  </Tab>
</Tabs>
