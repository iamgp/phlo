import { describe, expect, it } from 'vitest'

import { buildContributingRowsQuery } from '@/server/contributing.server'

describe('contributing rows query builder', () => {
  it('uses _phlo_row_id equality when present upstream', () => {
    const result = buildContributingRowsQuery({
      downstreamTableName: 'mrt_language_distribution',
      upstream: {
        schema: 'gold',
        table: 'fct_repository_languages',
        fullName: '"iceberg"."gold"."fct_repository_languages"',
        columnTypes: { _phlo_row_id: 'varchar', primary_language: 'varchar' },
      },
      rowData: { _phlo_row_id: 'abc123', primary_language: 'Go' },
      pageSize: 50,
      page: 0,
    })

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.mode).toBe('entity')
    expect(result.query).toMatch(/WHERE\s+"?_phlo_row_id"?\s*=\s*'abc123'/)
    expect(result.query).toMatch(/ORDER BY "_phlo_row_id"/)
  })

  it('uses deterministic ordering when sampling aggregate contributing rows', () => {
    const result = buildContributingRowsQuery({
      downstreamTableName: 'mrt_contribution_patterns',
      upstream: {
        schema: 'silver',
        table: 'fct_github_events',
        fullName: '"iceberg"."silver"."fct_github_events"',
        columnTypes: {
          _phlo_partition_date: 'date',
          hour_of_day: 'integer',
          day_of_week: 'integer',
          _phlo_row_id: 'varchar',
        },
      },
      rowData: {
        _phlo_partition_date: '2025-01-01',
        hour_of_day: 3,
        day_of_week: 2,
      },
      pageSize: 25,
      page: 2,
    })

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.mode).toBe('aggregate')
    expect(result.query).toMatch(/ORDER BY xxhash64/)
    expect(result.query).toMatch(/OFFSET 50 LIMIT 26$/)
  })
})
