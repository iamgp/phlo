import { describe, expect, it } from 'vitest'

import { coreNavItems } from './AppSidebar'

describe('AppSidebar core navigation', () => {
  it('includes all primary observatory routes', () => {
    const routes = coreNavItems.map((item) => item.to)

    expect(routes).toEqual(
      expect.arrayContaining([
        '/',
        '/hub',
        '/data',
        '/graph',
        '/quality',
        '/logs',
        '/branches',
        '/assets',
        '/settings',
      ]),
    )
  })
})
