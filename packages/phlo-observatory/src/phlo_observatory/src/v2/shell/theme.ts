export type V2ThemeMode = 'system' | 'light' | 'dark'
export type V2ResolvedTheme = 'light' | 'dark'

export const V2_THEME_STORAGE_KEY = 'phlo-observatory-v2-theme'

export type V2ThemeSnapshot = {
  mode: V2ThemeMode
  resolvedTheme: V2ResolvedTheme
  systemPrefersDark: boolean
}

export function resolveV2Theme(
  mode: V2ThemeMode,
  systemPrefersDark: boolean,
): V2ResolvedTheme {
  if (mode === 'system') return systemPrefersDark ? 'dark' : 'light'
  return mode
}

export function readV2ThemeMode(
  storage: Pick<Storage, 'getItem'>,
): V2ThemeMode {
  const stored = storage.getItem(V2_THEME_STORAGE_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored
  }
  return 'system'
}

export function getV2ThemeSnapshot(
  storage: Pick<Storage, 'getItem'>,
  systemPrefersDark: boolean,
): V2ThemeSnapshot {
  const mode = readV2ThemeMode(storage)
  return {
    mode,
    resolvedTheme: resolveV2Theme(mode, systemPrefersDark),
    systemPrefersDark,
  }
}
