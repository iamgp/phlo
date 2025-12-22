import { z } from 'zod'

export const OBSERVATORY_SETTINGS_STORAGE_KEY = 'phlo-observatory-settings-v1'

const densitySchema = z.enum(['comfortable', 'compact'])
const dateFormatSchema = z.enum(['iso', 'local'])

export const observatorySettingsSchema = z.object({
  version: z.literal(1),
  connections: z.object({
    dagsterGraphqlUrl: z.string().min(1),
    trinoUrl: z.string().min(1),
    nessieUrl: z.string().min(1),
  }),
  defaults: z.object({
    branch: z.string().min(1),
    catalog: z.string().min(1),
    schema: z.string().min(1),
  }),
  query: z.object({
    readOnlyMode: z.boolean(),
    defaultLimit: z.number().int().min(1).max(100_000),
    maxLimit: z.number().int().min(1).max(100_000),
    timeoutMs: z.number().int().min(1_000).max(300_000),
  }),
  ui: z.object({
    density: densitySchema,
    dateFormat: dateFormatSchema,
  }),
  // Auth settings (phlo-h2c)
  auth: z
    .object({
      token: z.string().optional(),
    })
    .optional(),
  // Real-time polling settings (phlo-cil)
  realtime: z
    .object({
      enabled: z.boolean(),
      intervalMs: z.number().int().min(1000).max(60000),
    })
    .optional(),
})

export type ObservatorySettings = z.infer<typeof observatorySettingsSchema>
export type ObservatorySettingsInput = z.input<typeof observatorySettingsSchema>

export function getFallbackObservatorySettings(): ObservatorySettings {
  return {
    version: 1,
    connections: {
      dagsterGraphqlUrl: 'http://localhost:3000/graphql',
      trinoUrl: 'http://localhost:8080',
      nessieUrl: 'http://localhost:19120/api/v2',
    },
    defaults: {
      branch: 'main',
      catalog: 'iceberg',
      schema: 'gold',
    },
    query: {
      readOnlyMode: true,
      defaultLimit: 100,
      maxLimit: 5000,
      timeoutMs: 30_000,
    },
    ui: {
      density: 'comfortable',
      dateFormat: 'iso',
    },
    auth: {
      token: undefined,
    },
    realtime: {
      enabled: true,
      intervalMs: 5000,
    },
  }
}

export function parseObservatorySettings(
  input: unknown,
  fallback: ObservatorySettings = getFallbackObservatorySettings(),
): ObservatorySettings {
  const parsed = observatorySettingsSchema.safeParse(input)
  if (!parsed.success) return fallback
  return parsed.data
}

export function loadStoredObservatorySettings():
  | { settings: ObservatorySettings; source: 'localStorage' }
  | { settings: ObservatorySettings; source: 'fallback' } {
  if (typeof window === 'undefined') {
    return { settings: getFallbackObservatorySettings(), source: 'fallback' }
  }

  const raw = window.localStorage.getItem(OBSERVATORY_SETTINGS_STORAGE_KEY)
  if (!raw) {
    return { settings: getFallbackObservatorySettings(), source: 'fallback' }
  }

  try {
    const parsed = parseObservatorySettings(JSON.parse(raw))
    return { settings: parsed, source: 'localStorage' }
  } catch {
    return { settings: getFallbackObservatorySettings(), source: 'fallback' }
  }
}

export function storeObservatorySettings(settings: ObservatorySettings): void {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(
    OBSERVATORY_SETTINGS_STORAGE_KEY,
    JSON.stringify(settings),
  )
}
