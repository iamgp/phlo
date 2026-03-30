# mock_trino (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_trino)



Mock Trino resource backed by DuckDB for testing.

Provides a mock implementation of TrinoResource that uses DuckDB as the backend,
enabling SQL testing without requiring a real Trino server.

Example:

> > > trino = MockTrinoResource()
> > > cursor = trino.cursor()
> > > cursor.execute("CREATE TABLE test AS SELECT 1 as id")
> > > result = cursor.execute("SELECT \* FROM test")
> > > print(cursor.fetchall())

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MockCursor&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_trino/MockCursor&#x22;" />

      <Card title="&#x22;MockConnection&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_trino/MockConnection&#x22;" />

      <Card title="&#x22;MockTrinoResource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_trino/MockTrinoResource&#x22;" />
    </Cards>
  </Tab>
</Tabs>
