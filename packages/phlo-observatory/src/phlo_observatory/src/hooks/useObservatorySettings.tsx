import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import type { ObservatorySettings } from '@/lib/observatorySettings'
import {
  getFallbackObservatorySettings,
  loadStoredObservatorySettings,
  storeObservatorySettings,
} from '@/lib/observatorySettings'
import { getObservatorySettingsDefaults } from '@/server/settings.server'

type ObservatorySettingsContextValue = {
  settings: ObservatorySettings
  defaults: ObservatorySettings
  setSettings: (next: ObservatorySettings) => void
  resetToDefaults: () => void
}

const ObservatorySettingsContext =
  createContext<ObservatorySettingsContextValue | null>(null)

export function ObservatorySettingsProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const fallback = useMemo(() => getFallbackObservatorySettings(), [])
  const [{ settings }, setStored] = useState(() =>
    loadStoredObservatorySettings(),
  )
  const [defaults, setDefaults] = useState<ObservatorySettings>(fallback)

  useEffect(() => {
    getObservatorySettingsDefaults().then((serverDefaults) => {
      setDefaults(serverDefaults)
      setStored((current) => {
        if (current.source === 'localStorage') return current
        const next = serverDefaults
        storeObservatorySettings(next)
        return { settings: next, source: 'localStorage' }
      })
    })
  }, [fallback])

  const value = useMemo<ObservatorySettingsContextValue>(
    () => ({
      settings,
      defaults,
      setSettings: (next) => {
        storeObservatorySettings(next)
        setStored({ settings: next, source: 'localStorage' })
      },
      resetToDefaults: () => {
        storeObservatorySettings(defaults)
        setStored({ settings: defaults, source: 'localStorage' })
      },
    }),
    [defaults, settings],
  )

  return (
    <ObservatorySettingsContext.Provider value={value}>
      {children}
    </ObservatorySettingsContext.Provider>
  )
}

export function useObservatorySettings(): ObservatorySettingsContextValue {
  const value = useContext(ObservatorySettingsContext)
  if (!value) {
    throw new Error(
      'useObservatorySettings must be used within ObservatorySettingsProvider',
    )
  }
  return value
}
