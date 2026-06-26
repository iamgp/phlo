import { describe, expect, it } from 'vitest'

import { resolveObservatoryExtensions } from './extensions.server'

describe('extensions.server resolveObservatoryExtensions', () => {
  it('returns no extensions when phlo-api extension discovery is unavailable', async () => {
    await expect(
      resolveObservatoryExtensions(async () => {
        throw new Error('phlo-api unavailable')
      }),
    ).resolves.toEqual([])
  })
})
