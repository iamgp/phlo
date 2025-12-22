import type { ObservatorySettings } from '@/lib/observatorySettings'
import { loadStoredObservatorySettings } from '@/lib/observatorySettings'
import { getObservatorySettingsDefaults } from '@/server/settings.server'

export async function getEffectiveObservatorySettings(): Promise<ObservatorySettings> {
  const stored = loadStoredObservatorySettings()
  if (stored.source === 'localStorage') return stored.settings
  return await getObservatorySettingsDefaults()
}
