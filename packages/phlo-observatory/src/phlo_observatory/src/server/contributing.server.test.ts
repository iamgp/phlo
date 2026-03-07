import { describe, expect, it } from 'vitest'

import {
  transformContributingRowsPageResult,
  transformContributingRowsQueryResult,
} from '@/server/contributing.server'

describe('contributing.server transforms', () => {
  it('keeps contributing query payload stable', () => {
    expect(
      transformContributingRowsQueryResult({
        query: 'SELECT * FROM foo LIMIT 10',
        upstream: { schema: 'gold', table: 'fct_orders' },
      }),
    ).toEqual({
      query: 'SELECT * FROM foo LIMIT 10',
      upstream: { schema: 'gold', table: 'fct_orders' },
    })
  })

  it('camelizes contributing page payload from phlo-api', () => {
    expect(
      transformContributingRowsPageResult({
        mode: 'aggregate',
        page: 2,
        page_size: 50,
        has_more: true,
        query: 'SELECT * FROM foo OFFSET 100 LIMIT 51',
        upstream: { schema: 'silver', table: 'stg_orders' },
        columns: ['order_id'],
        column_types: ['varchar'],
        rows: [{ order_id: 'abc123' }],
      }),
    ).toEqual({
      mode: 'aggregate',
      page: 2,
      pageSize: 50,
      hasMore: true,
      query: 'SELECT * FROM foo OFFSET 100 LIMIT 51',
      upstream: { schema: 'silver', table: 'stg_orders' },
      columns: ['order_id'],
      columnTypes: ['varchar'],
      rows: [{ order_id: 'abc123' }],
    })
  })
})
