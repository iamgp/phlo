import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import type { ObservatorySettings } from '@/lib/observatorySettings'
import {
  getFallbackObservatorySettings,
  loadStoredObservatorySettings,
  parseObservatorySettings,
  storeObservatorySettings,
} from '@/lib/observatorySettings'
import {
  getObservatorySettings,
  putObservatorySettings,
} from '@/server/observatory-settings.server'
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
    let active = true
    Promise.all([getObservatorySettingsDefaults(), getObservatorySettings()])
      .then(([serverDefaults, serverSettings]) => {
        if (!active) return
        setDefaults(serverDefaults)

        if (serverSettings.settings) {
          const parsed = parseObservatorySettings(
            serverSettings.settings,
            serverDefaults,
          )
          storeObservatorySettings(parsed)
          setStored({ settings: parsed, source: 'localStorage' })
          return
        }

        setStored((current) => {
          if (current.source === 'localStorage') {
            void putObservatorySettings({ data: { settings: current.settings } })
            return current
          }
          const next = serverDefaults
          storeObservatorySettings(next)
          void putObservatorySettings({ data: { settings: next } })
          return { settings: next, source: 'localStorage' }
        })
      })
      .catch(() => {
        if (!active) return
        setDefaults(fallback)
      })
    return () => {
      active = false
    }
  }, [fallback])

  const value = useMemo<ObservatorySettingsContextValue>(
    () => ({
      settings,
      defaults,
      setSettings: (next) => {
        storeObservatorySettings(next)
        setStored({ settings: next, source: 'localStorage' })
        void putObservatorySettings({ data: { settings: next } })
      },
      resetToDefaults: () => {
        storeObservatorySettings(defaults)
        setStored({ settings: defaults, source: 'localStorage' })
        void putObservatorySettings({ data: { settings: defaults } })
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
