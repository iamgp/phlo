// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from 'vitest'

import { observabilityApi } from '@/lib/api'

describe('observabilityApi', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('passes backend selection through health requests', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify({ overall_status: 'healthy' })),
      )

    await observabilityApi.getHealthSummary('custom')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      'http://localhost:3000/api/observability/health?backend=custom',
    )
  })

  it('passes backend selection through parameterized requests', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify({ url: 'http://loki:3100/logs' })),
      )

    await observabilityApi.getLogsQueryLink('dagster', 'custom')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      'http://localhost:3000/api/observability/links/logs?service=dagster&backend=custom',
    )
  })
})
