import { describe, expect, test } from 'vitest'

import {
  V2_THEME_STORAGE_KEY,
  getV2ThemeSnapshot,
  resolveV2Theme,
} from './theme'

describe('resolveV2Theme', () => {
  test('uses system preference when mode is system', () => {
    expect(resolveV2Theme('system', true)).toBe('dark')
    expect(resolveV2Theme('system', false)).toBe('light')
  })

  test('keeps explicit light and dark modes independent of system preference', () => {
    expect(resolveV2Theme('light', true)).toBe('light')
    expect(resolveV2Theme('dark', false)).toBe('dark')
  })
})

describe('getV2ThemeSnapshot', () => {
  test('resolves stored dark before the first component effect', () => {
    const storage = {
      getItem: (key: string) => (key === V2_THEME_STORAGE_KEY ? 'dark' : null),
    } satisfies Pick<Storage, 'getItem'>

    expect(getV2ThemeSnapshot(storage, false)).toEqual({
      mode: 'dark',
      resolvedTheme: 'dark',
      systemPrefersDark: false,
    })
  })
})
